[![Tests](https://github.com/captainhammy/install-rez-packages-action/actions/workflows/tests.yml/badge.svg)](https://github.com/captainhammy/install-rez-packages-action/actions/workflows/tests.yml)
# Install Rez Packages

This GitHub Action will install PyPi packages into [rez](https://github.com/AcademySoftwareFoundation/rez) via the `rez pip` command.

## Usage

```yaml
  - name: Install Rez Packages
    uses: captainhammy/install-rez-packages-action@v1
    with:
      packages: "pytest,pytest-cov" 
      files: requirements.txt
```

### Inputs

The optional `packages` and `files` inputs can accept single values, or a comma separated list as demonstrated above.

For the `files` input, the expectation is that each file will resemble a `requirements.txt` file with one package name
(and optional version constraints) per line.

## Dependencies

While this package has no direct dependencies, it must be run in an environment where the `rez` command is available. 
