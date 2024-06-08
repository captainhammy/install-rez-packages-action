"""Test the install_rez_packages script."""

# Standard Library
from argparse import Namespace

# Third Party
import pytest

# install-rez-packages-action
import install_rez_packages

# Tests


def test_build_parser():
    """Test install_rez_packages.build_parser()."""
    parser = install_rez_packages.build_parser()

    expected = [option.lstrip("-") for action in parser._actions[-2:] for option in action.option_strings]

    assert expected == ["packages", "files"]


def test_flatten_files(shared_datadir):
    """Test install_rez_packages.flatten_files()."""
    expected = ["pytest-asyncio", "pytest-ruff", "pytest-home"]

    files = [shared_datadir / name for name in ["requirements.txt", "other.txt"]]

    packages = []

    install_rez_packages.flatten_files(files, packages)

    assert packages == expected


def test_install_packages(fp):
    """Test install_rez_packages.install_packages()."""
    packages = ["foo", "bar"]

    fp.register(["rez", "pip", "--install", "foo"])
    fp.register(["rez", "pip", "--install", "bar"])

    install_rez_packages.install_packages(packages)

    assert len(fp.calls) == len(packages)


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

    mock_parser = mocker.patch("install_rez_packages.argparse.ArgumentParser")
    mock_parser.return_value.parse_args.return_value = mock_namespace

    mock_install = mocker.patch("install_rez_packages.install_packages")

    install_rez_packages.main()

    mock_install.assert_called_with(["foo", "bar"])
