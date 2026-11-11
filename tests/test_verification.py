from verification import VerificationJob


class FakeScraper:
    def __init__(self, outcomes=None, **kwargs):
        self.outcomes = list(outcomes or [])
        self.calls = []

    def verify(self, url):
        self.calls.append(url)
        return self.outcomes.pop(0) if self.outcomes else {"status": "SUCCESS", "url": url}


def test_job_processes_queue_and_reports_counts():
    urls = ["u1", "u2", "u1"]
    job = VerificationJob(urls, scraper_factory=lambda **kw: FakeScraper([
        {"status": "SUCCESS"}, {"status": "RATE LIMITED"}
    ]))
    job.start()
    job.wait(2)
    state = job.snapshot()
    assert state["total"] == 2
    assert state["processed"] == 2
    assert state["successful"] == 1
    assert state["failed"] == 1
    assert not state["running"]
    assert set(state["results"]) == {"u1", "u2"}


def test_job_stops_between_profiles_and_keeps_partial_results():
    holder = {}

    class StopAfterFirst:
        def __init__(self, **kwargs):
            pass

        def verify(self, url):
            holder["job"].request_stop()
            return {"status": "SUCCESS", "url": url}

    job = VerificationJob(["u1", "u2", "u3"], scraper_factory=StopAfterFirst)
    holder["job"] = job
    job.start()
    job.wait(2)
    state = job.snapshot()
    assert state["processed"] == 1
    assert state["stopped"] is True
    assert set(state["results"]) == {"u1"}


def test_job_converts_unexpected_profile_exception_and_continues():
    class RaisesOnce:
        def __init__(self, **kwargs):
            self.calls = 0

        def verify(self, url):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("network wrapper failed")
            return {"status": "SUCCESS", "url": url}

    job = VerificationJob(["u1", "u2"], scraper_factory=RaisesOnce)
    job.start()
    job.wait(2)
    state = job.snapshot()
    assert state["processed"] == 2
    assert state["results"]["u1"]["status"] == "SCRAPING ERROR"
    assert state["results"]["u2"]["status"] == "SUCCESS"


def test_unexpected_worker_error_is_safe_and_keeps_technical_detail():
    class RaisesAlways:
        def __init__(self, **kwargs):
            pass

        def verify(self, url):
            raise RuntimeError("internal worker detail")

    job = VerificationJob(["u1"], scraper_factory=RaisesAlways)
    job.start()
    job.wait(2)
    result = job.snapshot()["results"]["u1"]
    assert result["status"] == "SCRAPING ERROR"
    assert "internal worker detail" not in result["error"]
    assert "internal worker detail" in result["technical_error"]
