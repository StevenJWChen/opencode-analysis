"""Pytest configuration and fixtures for PyCode tests"""

import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    tmpdir = Path(tempfile.mkdtemp())
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def temp_file(temp_dir):
    """Create a temporary file for tests"""
    def _create_temp_file(name: str, content: str = ""):
        file_path = temp_dir / name
        file_path.write_text(content)
        return file_path
    return _create_temp_file
