"""Test that requirements.txt is consistent with main branch."""
import subprocess
import os


def test_ha_version_pin_not_downgraded():
    """Requirements.txt should not pin homeassistant to an older version than main."""
    repo_root = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    result = subprocess.run(
        ["git", "show", "main:requirements.txt"],
        capture_output=True, text=True,
        cwd=repo_root,
    )
    main_version = None
    for line in result.stdout.splitlines():
        if line.startswith("homeassistant=="):
            main_version = line.split("==")[1]
            break

    result2 = subprocess.run(
        ["git", "show", "HEAD:requirements.txt"],
        capture_output=True, text=True,
        cwd=repo_root,
    )
    branch_version = None
    for line in result2.stdout.splitlines():
        if line.startswith("homeassistant=="):
            branch_version = line.split("==")[1]
            break

    # If neither pins, that's fine
    if main_version is None and branch_version is None:
        return

    # If main pins, branch must pin >= main or not pin at all
    if main_version is not None and branch_version is not None:
        assert branch_version >= main_version, (
            f"HA version downgraded: main={main_version}, branch={branch_version}"
        )
    # If main is unpinned and branch pins, that's also acceptable
