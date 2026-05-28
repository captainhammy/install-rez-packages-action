"""This script is used to install pip packages into rez."""

# Future
from __future__ import annotations

# Standard Library
import argparse
import pathlib
import subprocess
import tempfile
import urllib.error
import urllib.parse
from typing import Any

# Third Party
import tomlkit
from git import Repo


def _build_package(package_directory: pathlib.Path, *, variant: str | None) -> None:
    """Build and install the package.

    Args:
        package_directory: The directory of the package to build.
        variant: Optional specific variant to build.
    """
    cmd = [
        "rez",
        "build",
        "--install",
    ]

    if variant is not None:
        cmd.extend(["--variant", variant])

    subprocess.call(cmd, cwd=package_directory)


def _clone_repo(target_dir: pathlib.Path, url: str, *, branch: str | None) -> None:
    """Clone the git repository to the target directory.

    Args:
        target_dir: The directory to clone the repository under.
        url: The git repository url.
        branch: Optional branch/tag to check out.
    """
    kwargs: dict[str, Any] = {}

    if branch is not None:
        kwargs["branch"] = branch
        kwargs["single_branch"] = True
        kwargs["depth"] = 1

    Repo.clone_from(url, target_dir, **kwargs)


def _get_components_from_url(url: str) -> tuple[str, str | None, str | None]:
    """Get relevant components from a url.

    Args:
        url: The url to get the components from.

    Returns:
        A tuple containing the url, optional branch name, and optional variant.
    """
    result = urllib.parse.urlparse(url)
    query = dict(urllib.parse.parse_qsl(result.query))

    branch = query.get("branch")
    variant = query.get("variant")

    if query:
        url = urllib.parse.urlunparse((result.scheme, result.netloc, result.path, result.params, "", result.fragment))

    return url, branch, variant


def _get_dependency_groups() -> dict:
    """Get the dependency group dictionary from pyproject.toml.

    Returns:
        The 'dependency-groups' dictionary.

    Raises:
        OSError: If the pyproject.toml does not exist.
    """
    project_file = pathlib.Path("pyproject.toml")

    if not project_file.exists():
        raise FileNotFoundError(f"{project_file.resolve()} does not exist")

    with project_file.open("rb") as handle:
        data = tomlkit.load(handle)

    return data["dependency-groups"]


def _get_repo_name_from_url(url: str) -> str:
    """Get git repository name from a clone url.

    Args:
        url: The url to get the git repository from.

    Returns:
        The git repository name.

    Raises:
        urllib.error.URLError: If the url is badly formed.
    """
    last_slash_index = url.rfind("/")
    last_suffix_index = url.rfind(".git")

    if last_suffix_index < 0:
        last_suffix_index = len(url)

    if last_slash_index < 0 or last_suffix_index <= last_slash_index:
        raise urllib.error.URLError(f"Badly formatted url {url}")

    return url[last_slash_index + 1 : last_suffix_index]


def build_parser() -> argparse.ArgumentParser:
    """Build an argument parser to get the command line data.

    Returns:
        An argument parser to get the required input information.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--packages", default="")
    parser.add_argument("--files", default="")
    parser.add_argument("--groups", default="")
    parser.add_argument("--projects", default="")

    return parser


def flatten_files(files: list[str], packages: list[str]) -> None:
    """Flatten the contents of the requirements files into the packages list.

    We must do this as rez-pip cannot install packages from files.

    Args:
        files: The list of requirements files.
        packages: The list of packages to install.
    """
    for file_path in files:
        f = pathlib.Path(file_path).resolve()

        with f.open() as handle:
            packages.extend(handle.read().split())


def install_groups(groups: list[str]) -> None:
    """Install dependency groups from pyproject.toml into rez.

    Args:
        groups: The list of packages to install.
    """
    if not groups:
        return

    dependency_groups = _get_dependency_groups()

    packages_to_install = []

    for group in groups:
        group_packages = dependency_groups.get(group)

        if group_packages is None:
            print(f"Could not find dependency group '{group}' in pyproject.toml")
            continue

        packages_to_install.extend(group_packages)

    install_packages(packages_to_install)


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


def install_projects(projects: list[str]) -> None:
    """Checkout, build and install projects from git.

    Args:
        projects: A list of projects to build and install.
    """
    for project in projects:
        target_dir = pathlib.Path(tempfile.mkdtemp(prefix="rez-install-packages-"))

        url, branch, variant = _get_components_from_url(project)

        repo_name = _get_repo_name_from_url(url)
        repo_dir = target_dir / repo_name

        _clone_repo(repo_dir, url, branch=branch)

        _build_package(repo_dir, variant=variant)


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
    groups = get_input_list(parsed_args.groups)
    projects = get_input_list(parsed_args.projects)

    flatten_files(files, packages)

    install_packages(packages)

    install_groups(groups)

    install_projects(projects)


if __name__ == "__main__":
    main()
