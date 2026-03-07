#!/usr/bin/env python3
import sys
import time
import argparse
import setproctitle
from includes.api.laravel_api_client import LaravelAPIClient
from includes.config import Config
from includes.logger import (
    configure_loggers_with_targets,
    console_logger,
    api_logger,
    file_logger,
)
from includes.realtime import LaravelWebSocketListener
from includes.worker import RtlFmWorker, MultimonWorker
from includes.handlers import MessageHandler, CommandHandler


# Main program
if __name__ == "__main__":
    try:
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="NoxFeed - RTL-SDR data processor")
        parser.add_argument(
            "-l",
            "--log",
            nargs="+",
            choices=["file", "api", "console"],
            default=["file", "api"],
            help="Logging targets (default: file api)",
        )
        args = parser.parse_args()

        # Load configuration
        config = Config()

        # Set process name so it shows as "noxfeed" in ps -A
        setproctitle.setproctitle(config.process_name)

        # Configure loggers with specified targets
        configure_loggers_with_targets(
            log_file=config.logging_file,
            level=config.logging_level,
            targets=args.log,
        )

        api_logger.info("NoxFeed starting...")

        # API client
        api_user = config.get("api.user")
        api_password = config.get("api.password")
        api_token = config.get("api.token")

        api_client = LaravelAPIClient(
            base_url=config.api_base_url,
            api_token=api_token if api_token else None,
            user=api_user if api_user else None,
            password=api_password if api_password else None,
            logger=api_logger,
        )

        # Authenticate if user/password configured
        if api_user and api_password:
            try:
                api_logger.info("Authenticating with API...")
                api_client.login()
                api_logger.info("Authentication successful")
            except Exception as e:
                api_logger.error("Failed to authenticate with API: %s", e)
                console_logger.error(
                    "Authentication failed. Please check your credentials in config.json"
                )
                sys.exit(1)

        # Use API token for WebSocket authentication if available
        # This allows private channels to work with the same authentication
        websocket_auth_token = (
            api_client.token if api_client.token else config.get("websocket.token", "")
        )

        # Message handler
        message_handler = MessageHandler(
            storage_dir=config.get("messages.storage_dir", "messages"),
            api_client=api_client if config.get("messages.send_to_api", True) else None,
            api_endpoint=config.get("api.messages_endpoint", "/messages"),
            logger=file_logger,
        )

        # Command handler
        command_handler = CommandHandler(
            install_dir="/home/nox/noxfeed",
            logger=api_logger,
        )

        # Config update handler
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

        # Command handler for WebSocket
        def handle_command(payload):
            api_logger.info("Command event received: %s", payload)
            try:
                data = payload.get("data", {})
                command = data.get("command")
                params = data.get("params", {})

                if command:
                    success = command_handler.handle_command(command, params)
                    if success:
                        api_logger.info("Command executed successfully: %s", command)
                    else:
                        api_logger.error("Command execution failed: %s", command)
            except Exception as exc:
                api_logger.error("Failed to handle command: %s", exc)

        # WebSocket configuration
        ws_host = config.get("websocket.host", "")
        ws_port = config.get("websocket.port", 443)
        ws_secure = config.get("websocket.secure", True)
        ws_app_key = config.get("websocket.app_key", "")
        ws_reconnect_delay = config.get("websocket.reconnect_delay", 5)

        # WebSocket listeners
        ws_listeners = []

        if ws_host and ws_app_key:
            # Log WebSocket authentication status
            if websocket_auth_token:
                api_logger.info("WebSocket will use API authentication token")
            else:
                api_logger.info(
                    "WebSocket will connect without authentication (public channels only)"
                )

            # Config updates listener
            config_channel = config.get("websocket.channels.config", "config-updates")
            config_event = config.get(
                "websocket.events.config_updated", "config.updated"
            )

            ws_config_listener = LaravelWebSocketListener(
                app_key=ws_app_key,
                channel=config_channel,
                event_name=config_event,
                on_event=handle_config_update,
                host=ws_host,
                port=ws_port,
                secure=ws_secure,
                token=websocket_auth_token if websocket_auth_token else None,
                reconnect_delay=ws_reconnect_delay,
                logger=api_logger,
            )
            ws_config_listener.start()
            ws_listeners.append(ws_config_listener)
            api_logger.info("WebSocket config listener started")

            # Commands listener
            commands_channel = config.get("websocket.channels.commands", "commands")
            commands_event = config.get(
                "websocket.events.command_received", "command.execute"
            )

            ws_commands_listener = LaravelWebSocketListener(
                app_key=ws_app_key,
                channel=commands_channel,
                event_name=commands_event,
                on_event=handle_command,
                host=ws_host,
                port=ws_port,
                secure=ws_secure,
                token=websocket_auth_token if websocket_auth_token else None,
                reconnect_delay=ws_reconnect_delay,
                logger=api_logger,
            )
            ws_commands_listener.start()
            ws_listeners.append(ws_commands_listener)
            api_logger.info("WebSocket commands listener started")

            api_logger.info("WebSocket commands listener started")

        # RTL-FM and Multimon-NG workers
        rtl_command = config.get("rtl_fm.command", "rtl_fm")
        rtl_args = config.get("rtl_fm.args", [])

        multimon_command = config.get("multimon.command", "multimon-ng")
        multimon_args = config.get("multimon.args", [])

        api_logger.info("Starting RTL-FM worker...")
        rtl_worker = RtlFmWorker(rtl_command, rtl_args, logger=api_logger)
        rtl_process = rtl_worker.start()

        # Check if rtl_fm started successfully
        time.sleep(0.5)  # Give process a moment to start
        if rtl_process.poll() is not None:
            # Process already exited
            console_logger.error("RTL-FM failed to start!")
            if rtl_process.stderr:
                error_output = rtl_process.stderr.read()
                if isinstance(error_output, bytes):
                    error_output = error_output.decode("utf-8", errors="replace")
                console_logger.error("RTL-FM error: %s", error_output)
            console_logger.error("Make sure an RTL-SDR device is connected")
            console_logger.error("Test with: rtl_test")
            sys.exit(1)

        api_logger.info("Starting Multimon-NG worker...")
        multimon_worker = MultimonWorker(
            multimon_command,
            multimon_args,
            input_stream=rtl_process.stdout,
            logger=api_logger,
        )
        multimon_process = multimon_worker.start()

        # Check if multimon-ng started successfully
        time.sleep(0.5)
        if multimon_process.poll() is not None:
            console_logger.error("Multimon-NG failed to start!")
            if multimon_process.stderr:
                error_output = multimon_process.stderr.read()
                if isinstance(error_output, bytes):
                    error_output = error_output.decode("utf-8", errors="replace")
                console_logger.error("Multimon-NG error: %s", error_output)
            rtl_process.terminate()
            sys.exit(1)

        if rtl_process.stdout:
            rtl_process.stdout.close()

        console_logger.info("Workers started. Listening for POCSAG messages...")

        # Process multimon-ng output
        for line in multimon_worker.iter_lines():
            # Log raw output if console logging is enabled
            if "console" in args.log:
                print(line)

            # Process POCSAG messages
            message_data = message_handler.process_line(line)

            # You can add additional processing here if needed
            # For example, filtering, alerting, etc.

        multimon_process.wait()

    except FileNotFoundError as e:
        console_logger.error("Error: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        console_logger.info("Stopped by user")

        # Cleanup
        if "ws_listeners" in locals():
            for listener in ws_listeners:
                listener.stop()

        sys.exit(0)
    except Exception as e:
        console_logger.error("Error: %s", e, exc_info=True)
        sys.exit(1)
