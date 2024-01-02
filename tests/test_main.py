from unittest.mock import MagicMock, patch

import pytest

import main


def test_main():
    with patch("logging.basicConfig") as mocked, patch(
        "src.utils.main"
    ) as mocked_main:
        mocked_main = lambda x: res.append(0)
        assert main.main() is None
