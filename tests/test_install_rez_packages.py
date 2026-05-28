"""Test the install_rez_packages script."""

# Standard Library
import contextlib
import pathlib
import urllib.error
from argparse import Namespace

# Third Party
import pytest
import tomlkit

# install-rez-packages-action
import install_rez_packages

# Tests


@pytest.mark.parametrize("variant", (None, "2"))
def test__build_package(mocker, fp, variant):
    """Test install_rez_packages._build_package()."""
    mock_target = mocker.MagicMock(spec=pathlib.Path)

    args = ["rez", "build", "--install"]
    if variant is not None:
        args.extend(["--variant", variant])

    recorder = fp.register(args)

    install_rez_packages._build_package(mock_target, variant=variant)

    assert recorder.calls[0].args == args
    assert recorder.calls[0].kwargs == {"cwd": mock_target}


@pytest.mark.parametrize("branch", (None, "foo"))
def test__clone_repo(mocker, branch):
    """Test install_rez_packages._clone_repo()."""
    mock_clone = mocker.patch("install_rez_packages.Repo.clone_from")

    mock_target = mocker.MagicMock(spec=pathlib.Path)
    mock_url = mocker.MagicMock(spec=str)

    expected_kwargs = {}

    if branch is not None:
        expected_kwargs = {
            "branch": branch,
            "single_branch": True,
            "depth": 1,
        }

    install_rez_packages._clone_repo(mock_target, mock_url, branch=branch)

    mock_clone.assert_called_with(mock_url, mock_target, **expected_kwargs)


@pytest.mark.parametrize(
    "url,expected",
    (
        (
            "https://github.com/captainhammy/install-rez-packages-action.git",
            ("https://github.com/captainhammy/install-rez-packages-action.git", None, None),
        ),
        (
            "https://github.com/captainhammy/install-rez-packages-action.git?variant=2",
            ("https://github.com/captainhammy/install-rez-packages-action.git", None, "2"),
        ),
        (
            "https://github.com/captainhammy/install-rez-packages-action.git?branch=foo",
            ("https://github.com/captainhammy/install-rez-packages-action.git", "foo", None),
        ),
        (
            "https://github.com/captainhammy/install-rez-packages-action.git?variant=1&branch=bar",
            ("https://github.com/captainhammy/install-rez-packages-action.git", "bar", "1"),
        ),
        (
            "https://github.com/captainhammy/install-rez-packages-action.git?branch=foo&variant=0",
            ("https://github.com/captainhammy/install-rez-packages-action.git", "foo", "0"),
        ),
    ),
)
def test__get_components_from_url(url, expected):
    """Test install_rez_packages._get_components_from_url()."""
    result = install_rez_packages._get_components_from_url(url)

    assert result == expected


@pytest.mark.parametrize(
    "file_exists,context",
    (
        (False, pytest.raises(FileNotFoundError)),
        (True, contextlib.nullcontext()),
    ),
)
def test__get_dependency_groups(mocker, shared_datadir, file_exists, context):
    """Test install_rez_packages._get_dependency_groups()."""
    project_file = shared_datadir / "test_pyproject.toml"
    with project_file.open("rb") as handle:
        data = handle.read()
        handle.seek(0)
        expected_data = tomlkit.load(handle)

    mock_open = mocker.mock_open(read_data=data)

    mocker.patch.object(pathlib.Path, "open", mock_open)
    mocker.patch.object(pathlib.Path, "exists", return_value=file_exists)

    with context:
        results = install_rez_packages._get_dependency_groups()
        assert results == expected_data["dependency-groups"]


@pytest.mark.parametrize(
    "url,expected,context",
    (
        (
            "https://github.com/captainhammy/install-rez-packages-action.git",
            "install-rez-packages-action",
            contextlib.nullcontext(),
        ),
        (
            "git@github.com:captainhammy/install-rez-packages-action.git",
            "install-rez-packages-action",
            contextlib.nullcontext(),
        ),
        (
            "https://github.com/captainhammy/install-rez-packages-action",
            "install-rez-packages-action",
            contextlib.nullcontext(),
        ),
        (
            "https://github.com/captainhammy/install-rez-packages-action.git/asd",
            None,
            pytest.raises(urllib.error.URLError),
        ),
    ),
)
def test__get_repo_name_from_url(url, expected, context):
    """Test install_rez_packages._get_repo_name_from_url()."""
    with context:
        result = install_rez_packages._get_repo_name_from_url(url)

        assert result == expected


def test_build_parser():
    """Test install_rez_packages.build_parser()."""
    parser = install_rez_packages.build_parser()

    expected = [option.lstrip("-") for action in parser._actions[-4:] for option in action.option_strings]

    assert expected == ["packages", "files", "groups", "projects"]


def test_flatten_files(shared_datadir):
    """Test install_rez_packages.flatten_files()."""
    expected = ["pytest-asyncio", "pytest-ruff", "pytest-home"]

    files = [shared_datadir / name for name in ["requirements.txt", "other.txt"]]

    packages = []

    install_rez_packages.flatten_files(files, packages)

    assert packages == expected


@pytest.mark.parametrize(
    "groups,expected",
    (
        ([], []),
        (["test"], ["pytest", "pytest_cov", "pytest_datadir", "pytest_houdini", "pytest_mock"]),
        (["deps", "github"], ["humanfriendly", "python-singleton", "coverage", "tox"]),
        (["bob"], []),
    ),
)
def test_install_groups(mocker, shared_datadir, groups, expected):
    """Test install_rez_packages.install_groups()."""
    project_file = shared_datadir / "test_pyproject.toml"
    with project_file.open("rb") as handle:
        data = tomlkit.load(handle)

    mocker.patch("install_rez_packages._get_dependency_groups", return_value=data["dependency-groups"])

    mock_install = mocker.patch("install_rez_packages.install_packages")

    install_rez_packages.install_groups(groups)

    if groups:
        mock_install.assert_called_with(expected)

    else:
        mock_install.assert_not_called()


def test_install_packages(fp):
    """Test install_rez_packages.install_packages()."""
    packages = ["foo", "bar"]

    fp.register(["rez", "pip", "--install", "foo"])
    fp.register(["rez", "pip", "--install", "bar"])

    install_rez_packages.install_packages(packages)

    assert len(fp.calls) == len(packages)


def test_install_projects(mocker):
    """Test install_rez_packages.install_projects()."""
    project_name = "project1"

    url = "a_url"
    branch = "main"
    variant = "variant2"
    repo_name = "test_repo"

    mock_target = pathlib.Path()

    mock_temp_dir = mocker.patch("install_rez_packages.tempfile.mkdtemp", return_value=mock_target)

    mock_get_components = mocker.patch(
        "install_rez_packages._get_components_from_url", return_value=(url, branch, variant)
    )

    mock_get_repo = mocker.patch("install_rez_packages._get_repo_name_from_url", return_value=repo_name)
    mock_clone_repo = mocker.patch("install_rez_packages._clone_repo")
    mock_build = mocker.patch("install_rez_packages._build_package")

    install_rez_packages.install_projects([project_name])

    mock_temp_dir.assert_called_with(prefix="rez-install-packages-")
    mock_get_components.assert_called_with(project_name)
    mock_get_repo.assert_called_with(url)
    mock_clone_repo.assert_called_with(mock_target / repo_name, url, branch=branch)

    mock_build.assert_called_with(mock_target / repo_name, variant=variant)


@pytest.mark.parametrize(
    "value,expected",
    [
        ("", []),
        ("foo", ["foo"]),
        ("foo,bar", ["foo", "bar"]),
        ("/path/to/foo.txt,bar.txt", ["/path/to/foo.txt", "bar.txt"]),
    ],
)
def test_get_input_list(value, expected):
    """Test install_rez_packages.get_input_list()."""
    result = install_rez_packages.get_input_list(value)
    assert result == expected


def test_main(mocker):
    """Test install_rez_packages.main()."""
    mock_namespace = mocker.MagicMock(spec=Namespace)
    mock_namespace.packages = "foo,bar"
    mock_namespace.files = ""
    mock_namespace.projects = ""
    mock_namespace.groups = ""

    mock_parser = mocker.patch("install_rez_packages.argparse.ArgumentParser")
    mock_parser.return_value.parse_args.return_value = mock_namespace

    mock_install = mocker.patch("install_rez_packages.install_packages")

    install_rez_packages.main()

    mock_install.assert_called_with(["foo", "bar"])
