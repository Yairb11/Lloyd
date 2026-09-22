from PyQt6.QtCore import QThread


class CancellableWorker(QThread):
    def is_cancelled(self) -> bool:
        return self.isInterruptionRequested()

    def request_stop(self) -> None:
        self.requestInterruption()

    def run(self) -> None:
        try:
            self.do_work()
        finally:
            self.cleanup()

    def do_work(self) -> None:
        raise NotImplementedError

    def cleanup(self) -> None:
        pass
