from pathlib import Path


def test_deploy_config():
    backend_dir = Path(__file__).resolve().parent.parent
    dockerfile_path = backend_dir / "Dockerfile"
    pyproject_path = backend_dir / "pyproject.toml"

    assert dockerfile_path.exists(), f"Missing Dockerfile at {dockerfile_path}"
    dockerfile_text = dockerfile_path.read_text(encoding="utf-8")

    # 1. "EXPOSE 7860" and "--port 7860" are present.
    assert "EXPOSE 7860" in dockerfile_text, "Missing 'EXPOSE 7860' in Dockerfile"
    assert "--port 7860" in dockerfile_text, "Missing '--port 7860' in Dockerfile"

    # 2. "playwright" and "browser" are absent (case-insensitive).
    assert "playwright" not in dockerfile_text.lower(), "Found 'playwright' in Dockerfile"
    assert "browser" not in dockerfile_text.lower(), "Found 'browser' in Dockerfile"

    # 3. "COPY .env" is absent.
    assert "COPY .env" not in dockerfile_text, "Found 'COPY .env' in Dockerfile"

    # 4. A "USER " line exists and is not root.
    user_lines = [
        line.strip()
        for line in dockerfile_text.splitlines()
        if line.strip().startswith("USER ")
    ]
    assert len(user_lines) > 0, "No 'USER ' line found in Dockerfile"
    user_val = user_lines[0].split("USER ", 1)[1].strip()
    assert user_val.lower() != "root", f"USER line must not be root, got: {user_val}"

    # 5. pyproject.toml does not contain "browser-use" or "playwright".
    assert pyproject_path.exists(), f"Missing pyproject.toml at {pyproject_path}"
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    assert "browser-use" not in pyproject_text, "Found 'browser-use' in pyproject.toml"
    assert "playwright" not in pyproject_text, "Found 'playwright' in pyproject.toml"
