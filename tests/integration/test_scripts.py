import pytest
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import patch
import scripts.release_version as rv


class TestReleaseVersionPositive:

    def test_main_found_version_match(self, toml_path):
        with pytest.raises(SystemExit) as e:
            with patch('subprocess.check_output', return_value=b'v1.2.3\n'):
                rv.main()
        assert e.type == SystemExit
        assert e.value.code == 1

    def test_main_found_version_not_match(self, toml_path):
        with pytest.raises(SystemExit) as e:
            with patch('subprocess.check_output', return_value=b'v2.2.3\n'):
                rv.main()
        assert e.type == SystemExit
        assert e.value.code == 0


class TestReleaseVersionNegative:
    
    def test_main_no_toml(self, no_toml):
        with pytest.raises(FileNotFoundError):
            rv.main()
