"""This script is used to install pip packages into rez."""

# Standard Library
import argparse
import pathlib
import subprocess


def build_parser() -> argparse.ArgumentParser:
    """Build an argument parser to get the command line data.

    Returns:
        An argument parser to get the required input information.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--packages", default="")
    parser.add_argument("--files", default="")

    return parser


def flatten_files(files: list[str], packages: list[str]) -> None:
    """Flatten the contents of the requirements files into the packages list.

    Args:
        files: The list of requirements files.
        packages: The list of packages to install.
    """
    for file_path in files:
        f = pathlib.Path(file_path).resolve()

        with f.open() as handle:
            packages.extend(handle.read().split())


def install_packages(packages: list[str]) -> None:
    """Install packages from pip into rez.

    Args:
        packages: The list of packages to install.
    """
    for package in packages:
        cmd = [
            "rez",
            "pip",
            "--install",
            package,
        ]
        subprocess.call(cmd)


def get_input_list(value: str) -> list[str]:
    """Convert the input string into a list of strings.

    Args:
        value: A comma separated list of names or paths.

    Returns:
        The converted list of strings.
    """
    if not value:
        return []

    return value.split(",")


def main() -> None:
    """The main execution function."""
    # Parse the args from the action execution.
    parser = build_parser()
    parsed_args = parser.parse_args()

    packages = get_input_list(parsed_args.packages)
    files = get_input_list(parsed_args.files)

    flatten_files(files, packages)

    install_packages(packages)


if __name__ == "__main__":
    main()
