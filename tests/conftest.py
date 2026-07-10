import pytest

from schwerpunkt.config import Profile, RunMode, Settings
from schwerpunkt.runtime.session import reset_manager


@pytest.fixture
def stub_settings(tmp_path):
    fixtures = tmp_path / "fixtures"
    (fixtures / "scenarios").mkdir(parents=True)
    (fixtures / "cognition" / "default").mkdir(parents=True)
    import shutil
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "fixtures"
    shutil.copytree(root, fixtures, dirs_exist_ok=True)
    return Settings(
        mode=RunMode.STUB,
        profile=Profile.LOCAL,
        data_dir=str(tmp_path / "data"),
        fixtures_dir=str(fixtures),
        rules_path=str(fixtures / "igc_rules.json"),
    )


@pytest.fixture
def manual_settings(stub_settings, tmp_path, monkeypatch):
    monkeypatch.setenv("SCHWERKPUNKT_USE_SQLITE", "0")
    return stub_settings.model_copy(update={"mode": RunMode.MANUAL, "data_dir": str(tmp_path / "data")})


@pytest.fixture
def manager(stub_settings):
    return reset_manager(stub_settings)


@pytest.fixture
def manual_manager(manual_settings):
    return reset_manager(manual_settings)
