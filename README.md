# Qabel drop documentation
* [Drop protocol](https://qabel.github.io/docs/Qabel-Protocol-Drop/)
* [Drop documentation](https://qabel.github.io/docs/Components-Drop/)

# qabel-drop

[![Build Status](https://travis-ci.org/Qabel/qabel-drop.svg)](https://travis-ci.org/Qabel/qabel-drop)

Qabel drop server
# Requirements
* Python 3.4
* pip
* PostgreSQL server 9.4
* libpq-dev

# Installation
* `pip install -r requirements.txt`
* `cp config.py.example config.py`
* Create the database and a user inside PostgreSQL
  * `CREATE DATABASE 'qabel_drop'`
  * `CREATE USER qabel WITH PASSWORD 'qabel_test'`
  * `GRANT ALL PRIVILEGES ON DATABASE qabel_drop TO qabel`
* You **should** change the database name, the username and the password for production, do **not** forget to change the `config.py` accordingly
