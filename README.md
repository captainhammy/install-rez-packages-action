[![Tests](https://github.com/captainhammy/install-rez-packages-action/actions/workflows/tests.yml/badge.svg)](https://github.com/captainhammy/install-rez-packages-action/actions/workflows/tests.yml)
# Install Rez Packages

This GitHub Action will install PyPi packages and Git projects into [rez](https://github.com/AcademySoftwareFoundation/rez).

PyPi packages are installed via the `rez pip` command.

Git projects are cloned and then built using `rez build --install`.

## Usage

```yaml
  - name: Install Rez Packages
    uses: captainhammy/install-rez-packages-action@v1
    with:
      packages: "pytest,pytest-cov" 
      files: requirements.txt
      groups: test
      projects: https://github.com/captainhammy/you-can-call-me-houdini.git
```

### Inputs

The optional `packages`, `files`, `groups`, and `projects` inputs can accept single values, or a comma separated list as
demonstrated above.

#### Packages
The `packages` value is one or more PyPi package names.

#### Files

For the `files` input, the expectation is that each file will resemble a `requirements.txt` file with one package name
(and optional version constraints) per line. The file names can be relative or absolute paths.

#### Groups
The `groups` value is one or more names of any `dependency-groups` in a pyproject.toml file.

#### Projects

For the `projects` input, the URLs should be `git clone`able projects. These URLs can contain extra info to use specific
branches/tags, or to build specific variants.

##### Branches

It is possible to use a specific branch/tag by passing it after an `@`:

```yaml
    ...
    with:
      projects: https://github.com/captainhammy/test-project@v2.3.1
```

##### Variants

If you need to build a specific variant from that package, it can be selected by pass it after a `#`:

```yaml
    ...
    with:
      projects: https://github.com/captainhammy/test-project#2
```

This is equivalent to running `rez build --install --variant 2`.


## Dependencies

This package must be run in an environment where the `rez` and `git` commands are available. 
