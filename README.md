<img align="left" width="0" height="150px" hspace="20"/>
<a href="https://qabel.de" align="left">
	<img src="https://files.qabel.de/img/qabel_logo_orange_preview.png" height="150px" align="left"/>
</a>
<img align="left" width="0" height="150px" hspace="25"/>
> The Qabel Drop Server

This project provides the drop server for <a href="https://qabel.de"><img alt="Qabel" src="https://files.qabel.de/img/qabel-kl.png" height="18px"/></a> that manages Qabel-Accounts that authorize Qabel Box usage according to the [Qabel Box Protocol](http://qabel.github.io/docs/Qabel-Protocol-Box/).

<br style="clear: both"/>
<br style="clear: both"/>
<p align="center">
	<a href="#introduction">Introduction</a> |
	<a href="#requirements">Requirements</a> |
	<a href="#installation">Installation</a>
</p>

# Introduction
For a comprehensive documentation of the whole Qabel Platform use https://qabel.de as the main source of information. http://qabel.github.io/docs/ may provide additional technical information.

Qabel consists of multiple Projects:
 * [Qabel Android Client](https://github.com/Qabel/qabel-android)
 * [Qabel Desktop Client](https://github.com/Qabel/qabel-desktop)
 * [Qabel Core](https://github.com/Qabel/qabel-core) is a library that includes the common code between both clients to keep them consistent
 * [Qabel Drop Server](https://github.com/Qabel/qabel-drop) is the target server for drop messages according to the [Qabel Drop Protocol](http://qabel.github.io/docs/Qabel-Protocol-Drop/)
 * [Qabel Accounting Server](https://github.com/Qabel/qabel-accounting) manages Qabel-Accounts that authorize Qabel Box usage according to the [Qabel Box Protocol](http://qabel.github.io/docs/Qabel-Protocol-Box/)
 * [Qabel Block Server](https://github.com/Qabel/qabel-block) serves as the storage backend according to the [Qabel Box Protocol](http://qabel.github.io/docs/Qabel-Protocol-Box/)

# Requirements
* Python 3.4
* pip
* PostgreSQL server 9.4
* libpq-dev

# Installation
* `virtualenv --python=python3.4 ../venv`
* `source ../venv/bin/activate`
* `pip install -r requirements.txt`
* `cp config.py.example config.py`
* Create the database and a user inside PostgreSQL
    * `CREATE DATABASE 'qabel_drop'`
    * `CREATE USER qabel WITH PASSWORD 'qabel_test'`
    * `GRANT ALL PRIVILEGES ON DATABASE qabel_drop TO qabel`
* You **should** change the database name, the username and the password for production, do **not** forget to change the `config.py` accordingly
* Configure prometheus monitoring
	* Maybe disable the prometheus metric export by setting PROMETHEUS_ENABLE = False
	* Or configure the port range for the metrics export

# Build
after setting up and activating the virtualenv, go to tests and run py.test
```BASH
cd tests
py.test
```
