from services.job_sources.manual_mock import ManualMockJobSourceAdapter
from services.job_sources.registry import (
    can_run_source,
    get_available_sources,
    get_enabled_runnable_sources,
    get_source_adapter,
    get_source_setting,
    record_source_run,
    seed_default_source_settings,
    update_source_setting,
    validate_source_can_run,
)


def get_phase_2a_adapters() -> dict[str, ManualMockJobSourceAdapter]:
    return {
        ManualMockJobSourceAdapter.source_name: ManualMockJobSourceAdapter(),
    }
