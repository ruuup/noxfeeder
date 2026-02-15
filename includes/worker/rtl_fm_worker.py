import subprocess
from typing import List, Optional
import logging


class RtlFmWorker:
    """Worker for starting rtl_fm."""

    def __init__(
        self,
        command: str = "rtl_fm",
        args: Optional[List[str]] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.command = command
        self.args = args or []
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> subprocess.Popen:
        if self.logger:
            self.logger.info(
                "Starting rtl_fm: %s %s", self.command, " ".join(self.args)
            )

        self.process = subprocess.Popen(
            [self.command, *self.args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return self.process

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            if self.logger:
                self.logger.info("Stopping rtl_fm")
            self.process.terminate()
