class JobSourceAdapter:
    source_name: str = ""

    def search_jobs(self, alert_profile: dict) -> list[dict]:
        raise NotImplementedError
