# Central Training Portal

![Django badge](https://img.shields.io/badge/django-092E20?logo=django&logoColor=white)
[![Continuous Integration](https://github.com/makl8/dts-sed-app/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/makl8/dts-sed-app/actions/workflows/ci.yaml)

## Description
Version: 0.1.2  <!-- x-release-please-version -->

The Central Training Portal (CTP) is a Django application for recording and maintaining staff training records.

It allows authenticated users to add, review, renew and remove completed training against a central course catalogue. The application tracks renewal periods and expiry dates so mandatory, recurring and one-off training can be monitored in one place.

## Authentication and security model

- Authentication is handled by `django-allauth`
- Login is configured to use email addresses only
- The test suite includes OWASP-focused tests for A1 Injection, A2 Broken Authentication and A5 Broken Access Control

## How to create a virtual environment and install dependencies

Go to the application's root directory, create a virtual environment and activate it:
```shell
python -m venv .venv
```

On PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

On bash:
```shell
source .venv/bin/activate
```

Install the application dependencies from `pyproject.toml`:
```shell
pip install --upgrade pip
pip install .
```

If you are contributing to the project, install the development and test extras as well:
```shell
pip install -e ".[dev,test]"
```

## How to run the application locally

Local development uses `learning.settings` by default.

Create a `.env` file in the repository root with at least a Django secret key:

```env
SECRET_KEY=<secret_key_value>
```

Common optional settings are:

```env
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
DJANGO_LOG_LEVEL=DEBUG
DJANGO_LOG_FILE=general.log
DB_NAME=trainingdb.sqlite3
```

Notes:

- `DEBUG=True` is suitable for local development only
- `DB_NAME` changes the SQLite file name under the repository root
- When `DEBUG=false`, secure-cookie and HTTPS settings are enabled

Apply migrations and start the development server:

```bash
python manage.py migrate
python manage.py runserver
```

The application is then available at `http://127.0.0.1:8000/`.

The default local database is SQLite and uses `trainingdb.sqlite3` unless `DB_NAME` is set in `.env`.

Static files are served through WhiteNoise. If you want to emulate production-style static file handling with `DEBUG=false`, collect static files first:

```shell
python manage.py collectstatic
```

## Testing and Quality

The repository currently uses GitHub Actions and Python tooling for linting and quality checks.

Key tools include:

- MegaLinter (including ruff, black and yamllint)
- pytest
- pytest-cov
- pytest-django

### How to run the tests

You need the test dependencies installed in the `.venv` virtual environment:
```shell
pip install -e ".[test]"
```

Go to the application's root directory and run:
```shell
pytest tests
```

To include coverage in the terminal output:

```shell
pytest tests --cov=learning --cov-report=term-missing
```

### GitHub Actions workflows

The repository currently includes these main workflows:

<!-- markdown-table-prettify-ignore-start -->
| Workflow         | Purpose                                               |
|------------------|-------------------------------------------------------|
| `ci.yaml`        | Run tests, linting and validation checks              |
| `release.yaml`   | Create and update Release Please release PRs and tags |
<!-- markdown-table-prettify-ignore-end -->

## Releases

Releases are managed by Release Please from commits merged into `main`. Use Conventional Commits where `fix:` creates a patch release, `feat:` creates a minor release and `feat!:` or any commit with a `BREAKING CHANGE:` creates a major release.

When qualifying commits are merged, Release Please opens or updates a release pull request. Merging that release pull request creates the GitHub release, updates the tracked version files and publishes a SemVer tag in the format `v0.0.1`.

The release workflow is defined in `.github/workflows/release.yaml`, while the release rules are configured in `release-please-config.json` and `.release-please-manifest.json`.

## License

[![License](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](LICENSE)

Unless stated otherwise, the codebase is released under the
[MIT License](LICENSE). This covers both the codebase and any sample code in the documentation.
