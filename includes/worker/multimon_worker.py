import subprocess
from typing import List, Optional, Iterable
import logging


class MultimonWorker:
    """Worker for starting multimon-ng."""

    def __init__(
        self,
        command: str = "multimon-ng",
        args: Optional[List[str]] = None,
        input_stream=None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.command = command
        self.args = args or []
        self.input_stream = input_stream
        self.logger = logger
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> subprocess.Popen:
        if self.logger:
            self.logger.info(
                "Starting multimon-ng: %s %s", self.command, " ".join(self.args)
            )

        self.process = subprocess.Popen(
            [self.command, *self.args],
            stdin=self.input_stream,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        return self.process

    def iter_lines(self) -> Iterable[str]:
        if not self.process or not self.process.stdout:
            return []
        for line in self.process.stdout:
            yield line.rstrip("\n")

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            if self.logger:
                self.logger.info("Stopping multimon-ng")
            self.process.terminate()
