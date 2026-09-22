import itertools

from app.config import LOG_PREFIX_ERROR, PHONE_SCAN_POLL_INTERVAL_S
from app.core.qthread_support import track
from app.network.phone_upload import PhoneUploadServer
from app.threads.cancellable_worker import CancellableWorker

_phone_server_sequence = itertools.count(1)

class PhoneServerWorker(CancellableWorker):
    def __init__(self, httpd: PhoneUploadServer, parent=None) -> None:
        super().__init__(parent)
        track(self, f"PhoneServerWorker-{next(_phone_server_sequence)}")
        self.httpd = httpd

    def do_work(self) -> None:
        self.httpd.serve_forever(poll_interval=PHONE_SCAN_POLL_INTERVAL_S)

    def request_stop(self) -> None:
        super().request_stop()
        try:
            self.httpd.shutdown()
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: error shutting down phone scan server: {exc}")

    def cleanup(self) -> None:
        try:
            self.httpd.server_close()
        except Exception as exc:
            print(f"{LOG_PREFIX_ERROR}: error closing phone scan server socket: {exc}")
