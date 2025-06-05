"""
This script compares the version specified in pyproject.toml with the latest Git tag which will be echoed
into env for future use.
If the versions differ, it exits with code 0 to signal that a new release should be triggered.
If the versions are the same, it exits with code 1, indicating no release is necessary.
"""
import os
import toml
import subprocess
import sys

def get_current_version():
    """
    Scans pyproject.toml for project's version.

    Returns:
        str: version found in pyproject.toml
    """
    with open('pyproject.toml', 'r') as f:
        data = toml.load(f)
    return data['project']['version']

def get_latest_tag():
    """
    Checks latest Git tag and returns it.

    Returns:
        str or None: project version found in Git tags, or if not present, None.
    """
    try:
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).decode().strip()
        return tag.lstrip('v')
    except subprocess.CalledProcessError:
        return None

def main():
    """
    With help of get_current_version() and get_latest_tag(), prints versions diff and returns proper integer.
    Echoes version into env.

    Returns:
        int: 0 if chenges exists, 1 if version is not changed.
    """
    current_version = get_current_version()
    latest_tag = get_latest_tag()

    if latest_tag != current_version:
        print(f"Version changed: {latest_tag} -> {current_version}")
        if github_env := os.getenv('GITHUB_ENV'):
            with open(github_env, 'a') as env:
                env.write(f"RELEASE_VERSION={current_version}\n")
        else:
            print(f"Writing to env failed with {current_version=}")
        sys.exit(0)
    else:
        print("Version unchanged.")
        sys.exit(1)

if __name__ == "__main__":
    main()
