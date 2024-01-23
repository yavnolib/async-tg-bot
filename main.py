"""Main program file"""

import logging

import src.utils


def main() -> None:
    """Run logging and main from utils"""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        filename=f"logs/{src.utils.get_fname()}.log",
        filemode="w",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    src.utils.main()


if __name__ == "__main__":
    main()
