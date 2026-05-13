# Central Training Portal

![Django badge](https://img.shields.io/badge/django-092E20?logo=django&logoColor=white)
[![Continuous Integration](https://github.com/makl8/dts-sed-app/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/makl8/dts-sed-app/actions/workflows/ci.yaml)

## Description
Version: 0.1.0  <!-- x-release-please-version -->

The Central Training Portal (CTP) is a Django application for recording and maintaining staff training records.

It allows authenticated users to add, review, extend and remove completed training against a central course catalogue. The application also tracks renewal periods and expiry dates so mandatory and recurring training can be monitored in one place.

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

### GitHub Actions workflows

The repository currently includes these main workflows:

<!-- markdown-table-prettify-ignore-start -->
| Workflow         | Purpose                                               |
|------------------|-------------------------------------------------------|
| `ci.yaml`        | Run tests, linting and validation checks              |
| `pip-audit.yaml` | Run a manual dependency vulnerability audit           |
| `release.yaml`   | Create and update Release Please release PRs and tags |
<!-- markdown-table-prettify-ignore-end -->

## Releases

Releases are managed by Release Please from commits merged into `main`. Use Conventional Commits where `fix:` creates a patch release, `feat:` creates a minor release and `feat!:` or any commit with a `BREAKING CHANGE:` creates a major release.

When qualifying commits are merged, Release Please opens or updates a release pull request. Merging that release pull request creates the GitHub release, updates the tracked version files and publishes a SemVer tag in the format `v0.0.1`.

The release workflow is defined in `.github/workflows/release.yaml`, while the release rules are configured in `release-please-config.json` and `.release-please-manifest.json`.

## How to run the application locally

Local development uses `learning.settings` by default. \
Create a `.env` file in the repository root with at least the Django secret key value:

```env
SECRET_KEY=<secret_key_value>
```
You can also set:

```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
DEBUG=true
DJANGO_LOG_LEVEL=DEBUG
```

Static files are served through WhiteNoise. For local development with `DEBUG=true`, Django can serve static assets during `runserver`. If you are testing production-style settings with `DEBUG=false`, collect the static files first:

```shell
python manage.py collectstatic
```

Go to the application's root directory, apply migrations and start the development server:

```bash
python manage.py migrate
python manage.py runserver
```

Application is then available at
`http://127.0.0.1:8000/`

The default local database is SQLite at `trainingdb.sqlite3` in the application root.

## License

[![License](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](LICENSE)

Unless stated otherwise, the codebase is released under the
[MIT License](LICENSE). This covers both the codebase and any sample code in the documentation.
