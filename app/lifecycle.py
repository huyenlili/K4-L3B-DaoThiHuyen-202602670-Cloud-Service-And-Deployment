"""CP4 — Graceful shutdown.

Khi bạn deploy phiên bản mới, orchestrator (Docker, Railway, Cloud Run, K8s)
gửi SIGTERM rồi đợi vài chục giây trước khi SIGKILL. Nếu app bỏ qua tín
hiệu đó, mọi request đang xử lý dở bị cắt giữa chừng.

Ứng xử đúng:
nhận SIGTERM → báo "tôi sắp tắt" qua health check
→ load balancer ngừng đẩy traffic mới
→ xử lý nốt request đang chạy
→ thoát.
"""

from __future__ import annotations

import signal


class Lifecycle:
    """Giữ trạng thái vòng đời của process."""

    def __init__(self) -> None:
        self.shutting_down = False

        # Lưu lại handler cũ của từng signal.
        # Uvicorn có thể đã đăng ký handler trước đó.
        self._previous: dict = {}

    def request_shutdown(self, signum=None, frame=None) -> None:
        """Signal handler: đánh dấu process đang tắt dần."""

        # 1. Báo cho application biết process đang shutdown.
        self.shutting_down = True

        # 2. Gọi lại handler cũ nếu có.
        #
        # Quan trọng: handler của uvicorn có thể đã được đăng ký
        # trước khi Lifecycle.install() ghi đè nó.
        previous = self._previous.get(signum)

        if callable(previous):
            previous(signum, frame)

    def install(self) -> None:
        """Đăng ký handler cho SIGTERM và SIGINT."""

        # Đăng ký cả SIGTERM và SIGINT.
        for sig in (signal.SIGTERM, signal.SIGINT):
            # Nhớ handler hiện tại trước khi ghi đè.
            self._previous[sig] = signal.getsignal(sig)

            # Đăng ký handler của Lifecycle.
            signal.signal(sig, self.request_shutdown)


# Một instance dùng chung cho cả app.
lifecycle = Lifecycle()