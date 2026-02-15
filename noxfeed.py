#!/usr/bin/env python3
import sys
import setproctitle
from includes.api.laravel_api_client import LaravelAPIClient
from includes.config import Config
from includes.logger import configure_loggers, console_logger, api_logger
from includes.realtime import LaravelWebSocketListener
from includes.worker import RtlFmWorker, MultimonWorker


# Main program
if __name__ == "__main__":
    try:
        # Load configuration
        config = Config()

        # Set process name so it shows as "noxfeed" in ps -A
        setproctitle.setproctitle(config.process_name)

        # Configure loggers
        configure_loggers(log_file=config.logging_file, level=config.logging_level)

        # API client for config refresh
        api_client = LaravelAPIClient(
            base_url=config.api_base_url,
            api_token=config.api_token if config.api_token else None,
        )

        config_endpoint = config.get("api.config_endpoint", "/config")

        def handle_config_update(payload):
            api_logger.info("Config update event received: %s", payload)
            try:
                new_config = api_client.get(config_endpoint)
                config.update_from_dict(new_config)
                if config.get("config.persist", False):
                    config.save()
                api_logger.info("Config reloaded from API")
            except Exception as exc:
                api_logger.error("Failed to reload config: %s", exc)

        ws_host = config.get("websocket.host", "")
        ws_port = config.get("websocket.port", 443)
        ws_secure = config.get("websocket.secure", True)
        ws_app_key = config.get("websocket.app_key", "")
        ws_channel = config.get("websocket.channel", "config-updates")
        ws_event = config.get("websocket.event", "config.updated")
        ws_token = config.get("websocket.token", "")
        ws_reconnect_delay = config.get("websocket.reconnect_delay", 5)

        if ws_host and ws_app_key:
            ws_listener = LaravelWebSocketListener(
                app_key=ws_app_key,
                channel=ws_channel,
                event_name=ws_event,
                on_event=handle_config_update,
                host=ws_host,
                port=ws_port,
                secure=ws_secure,
                token=ws_token if ws_token else None,
                reconnect_delay=ws_reconnect_delay,
                logger=api_logger,
            )
            ws_listener.start()

        rtl_command = config.get("rtl_fm.command", "rtl_fm")
        rtl_args = config.get("rtl_fm.args", [])

        multimon_command = config.get("multimon.command", "multimon-ng")
        multimon_args = config.get(
            "multimon.args", ["-a", "AFSK1200", "-f", "auto", "-"]
        )

        rtl_worker = RtlFmWorker(rtl_command, rtl_args, logger=console_logger)
        rtl_process = rtl_worker.start()

        multimon_worker = MultimonWorker(
            multimon_command,
            multimon_args,
            input_stream=rtl_process.stdout,
            logger=console_logger,
        )
        multimon_process = multimon_worker.start()

        if rtl_process.stdout:
            rtl_process.stdout.close()

        console_logger.info("Workers started. Waiting for multimon-ng output...")

        for line in multimon_worker.iter_lines():
            print(line)

        multimon_process.wait()

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
