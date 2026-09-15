from PyQt6.QtCore import QThread


class CancellableWorker(QThread):
    FORCE_TERMINATE_ON_STOP: bool = False

    def is_cancelled(self) -> bool:
        return self.isInterruptionRequested()

    def request_stop(self) -> None:
        self.requestInterruption()
        if self.FORCE_TERMINATE_ON_STOP and self.isRunning():
            self.terminate()

    def stop(self, timeout_ms: int | None = None) -> None:
        self.request_stop()
        if timeout_ms is None:
            self.wait()
        else:
            self.wait(timeout_ms)

    def run(self) -> None:
        try:
            self.do_work()
        finally:
            self.cleanup()

    def do_work(self) -> None:
        raise NotImplementedError

    def cleanup(self) -> None:
        pass