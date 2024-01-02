from unittest.mock import patch

import main


def test_main():
    with patch("logging.basicConfig") as _, patch("src.utils.main") as _:
        assert main.main() is None
