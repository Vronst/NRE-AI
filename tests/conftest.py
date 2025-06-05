import pytest
import toml


@pytest.fixture(scope='function')
def toml_path(tmp_path, monkeypatch):
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_content = {
        "project": {
            "version": "1.2.3"
        }
    }
    pyproject_path.write_text(toml.dumps(pyproject_content))

    monkeypatch.chdir(tmp_path)
    return pyproject_path
        

@pytest.fixture(scope='function')
def no_toml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path
