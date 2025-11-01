# Customer Management Portal
Customer Management Portal (CMP) is a web application for managing customer data for CoPPS. \
This is a Software Engineering and DevOps (SED) application, part of the DTS programme.

![Flask badge](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)

The application is available at the [CMP website](https://maklcs.eu.pythonanywhere.com/).

## How to create a virtual environment and install dependencies

Go to the application's root directory, create a virtual environment and activate it:
```shell
python -m venv venv
source venv/bin/activate
```
Install Flask and other dependencies in the virtual environment:
```shell
pip install -r requirements/prod.txt
```

## How to run the application

Go to the application's root directory and execute the following two commands in the terminal:
```shell
source .env
flask run
```

The application is then available at
`http://127.0.0.1:5000/`

Sourcing the .env file sets two required environmental variables, FLASK_APP and FLASK_ENV 
(these instructions are provided for and tested on a Mac - modify it accordingly if using a different operating system).

## How to run the tests

You will need `pytest` installed in the `venv` virtual environment:
```shell
pip install pytest
```
unless you have installed the `dev` alongside `prod` dependencies like this:
```shell
pip install -r requirements/dev.txt
```
in which case you already have it.

Go to the application's root directory and run:
```shell
pytest .
```

## Licence

[![License](https://img.shields.io/github/license/Ileriayo/markdown-badges?style=for-the-badge)](LICENSE)

Unless stated otherwise, the codebase is released under the
[MIT License](LICENSE). This covers both the codebase and any sample code in the documentation.

The documentation is
[© Crown copyright](http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/)
and available under the terms of the
[Open Government 3.0](http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
licence.
