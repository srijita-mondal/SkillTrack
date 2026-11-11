"""Thread-safe, stoppable verification jobs used by the Streamlit interface."""
from __future__ import annotations

import threading
from typing import Callable, Iterable

import config
from scraper import ProfileScraper


class VerificationJob:
    """Run a sequential profile-verification queue outside the Streamlit script thread.

    The UI polls :meth:`snapshot` and can request a stop between profiles. An in-flight
    HTTP request is allowed to finish (bounded by the configured request timeout); this
    avoids corrupting scraper state or leaving a half-written result.
    """

    def __init__(
        self,
        urls: Iterable[str],
        scraper_options: dict | None = None,
        scraper_factory: Callable = ProfileScraper,
    ):
        self.urls = list(dict.fromkeys(urls))
        self.scraper_options = dict(scraper_options or {})
        self.scraper_factory = scraper_factory
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.results: dict[str, dict] = {}
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.running = False
        self.stopped = False
        self.error: str | None = None
        self.technical_error: str | None = None

    @property
    def total(self) -> int:
        return len(self.urls)

    def start(self) -> None:
        """Start the job in a daemon thread. A job instance can only be started once."""
        with self._lock:
            if self._thread is not None:
                raise RuntimeError("This verification job has already been started.")
            self.running = True
            self._thread = threading.Thread(target=self._run, name="skilltrack-verifier", daemon=True)
            self._thread.start()

    def request_stop(self) -> None:
        """Stop after the current profile request completes."""
        self._stop_event.set()

    def wait(self, timeout: float | None = None) -> None:
        """Wait for completion; mainly useful in tests and controlled shutdowns."""
        thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def snapshot(self) -> dict:
        """Return a consistent copy of the current job state for rendering."""
        with self._lock:
            return {
                "total": self.total,
                "processed": self.processed,
                "successful": self.successful,
                "failed": self.failed,
                "running": self.running,
                "stopped": self.stopped,
                "error": self.error,
                "technical_error": self.technical_error,
                "results": dict(self.results),
            }

    def _run(self) -> None:
        try:
            scraper = self.scraper_factory(**self.scraper_options)
            for url in self.urls:
                if self._stop_event.is_set():
                    break
                try:
                    result = scraper.verify(url)
                except Exception as exc:  # one unexpected profile failure must not abort the queue
                    result = {
                        "url": url,
                        "status": config.SCRAPING_ERROR,
                        "error": (
                            "An unexpected problem occurred while checking this profile. "
                            "Retry it later; if the problem continues, contact the application administrator."
                        ),
                        "technical_error": f"{type(exc).__name__}: {exc}",
                        "http_status": None,
                        "profile_name": None,
                        "badge_count": None,
                        "badges": [],
                        "checked_at": "",
                    }
                with self._lock:
                    self.results[url] = result
                    self.processed += 1
                    if result.get("status") == config.SUCCESS:
                        self.successful += 1
                    else:
                        self.failed += 1
        except Exception as exc:
            with self._lock:
                self.error = "The verification process could not start or continue. Check the settings and try again."
                self.technical_error = f"{type(exc).__name__}: {exc}"
        finally:
            with self._lock:
                self.running = False
                self.stopped = self._stop_event.is_set() and self.processed < self.total
