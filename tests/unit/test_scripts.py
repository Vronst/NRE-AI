import pytest
from unittest.mock import patch
from subprocess import CalledProcessError
import scripts.release_version as rv


class TestReleaseScriptPositive:

    def test_current_version(self, toml_path):
        version = rv.get_current_version()
        assert version == "1.2.3"

    def test_latest_tag_found(self):
        with patch("subprocess.check_output", return_value=b"v1.2.3\n"):
            tag = rv.get_latest_tag()
            assert tag == "1.2.3"

    def test_get_latest_tag_not_found(self):
        with patch("subprocess.check_output", side_effect=CalledProcessError(1, ['git'])):
            tag = rv.get_latest_tag()
            assert tag is None

    def test_main_version_match(self, monkeypatch):
        monkeypatch.setattr(rv, "get_current_version", lambda: "1.0.0")
        monkeypatch.setattr(rv, "get_latest_tag", lambda: "1.0.0")
        with pytest.raises(SystemExit) as e:
            rv.main()
        assert e.type == SystemExit
        assert e.value.code == 1 

    def test_main_version_mismatch(self, monkeypatch):
        monkeypatch.setattr(rv, "get_current_version", lambda: "1.0.1")
        monkeypatch.setattr(rv, "get_latest_tag", lambda: "1.0.0")
        with pytest.raises(SystemExit) as e:
            rv.main()
        assert e.type == SystemExit
        assert e.value.code == 0
