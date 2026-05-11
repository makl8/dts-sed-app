# Central Training Portal

![Django badge](https://img.shields.io/badge/django-092E20?logo=django&logoColor=white)
[![Continuous Integration](https://github.com/makl8/dts-sed-app/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/makl8/dts-sed-app/actions/workflows/ci.yaml)

## Description
Version: 0.0.0  <!-- x-release-please-version -->

The Central Training Portal (CTP) is a Django application for managing and recording training information. \

## How to create a virtual environment and install dependencies

Go to the application's root directory, create a virtual environment and activate it:
```shell
python -m venv .venv
source .venv/bin/activate
```
Install Django and other dependencies in the virtual environment:
```shell
pip install --upgrade pip
pip install -r requirements/prod.txt
```

## Testing and Quality

The repository currently uses GitHub Actions and Python tooling for linting and quality checks.

Key tools include:

- MegaLinter (including ruff, black and yamllint)
- pytest
- pytest-cov
- pytest-django

### How to run the tests

You need `pytest` installed in the `.venv` virtual environment:
```shell
pip install pytest pytest-cov pytest-django
```
unless you have installed the `dev` alongside `prod` dependencies like this:
```shell
pip install -r requirements/dev.txt
```
in which case you already have it.

Go to the application's root directory and run:
```shell
pytest tests --cov
```

### GitHub Actions workflows

The repository currently includes these main workflows:

| Workflow      | Purpose                                  |
|---------------|------------------------------------------|
| `ci.yaml`     | Run tests, linting and validation checks |

[//]: # (| `deploy.yaml` | Run deployment                           |)

## How to run the application locally

Local development uses `learning.settings` by default. \
Create a `.env` file in the repository root with at least the Django secret key value:

```env
SECRET_KEY=<secret_key_value>
DEBUG=true
```
You can also set:

```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
DJANGO_LOG_LEVEL=DEBUG
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
