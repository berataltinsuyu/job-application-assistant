from services.job_sources.manual_mock import ManualMockJobSourceAdapter


def get_phase_2a_adapters() -> dict[str, ManualMockJobSourceAdapter]:
    return {
        ManualMockJobSourceAdapter.source_name: ManualMockJobSourceAdapter(),
    }
