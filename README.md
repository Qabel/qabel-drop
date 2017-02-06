<img align="left" width="0" height="150px" hspace="20"/>
<a href="https://qabel.de" align="left">
	<img src="https://files.qabel.de/img/qabel_logo_orange_preview.png" height="150px" align="left"/>
</a>
<img align="left" width="0" height="150px" hspace="25"/>
> The Qabel Drop Server

This project provides the drop server for <a href="https://qabel.de"><img alt="Qabel" src="https://files.qabel.de/img/qabel-kl.png" height="18px"/></a> that manages message exchange according to the [Qabel Drop Protocol](http://qabel.github.io/docs/Qabel-Protocol-Drop/).

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

* Python 3.5 (+virtualenv)
* PostgreSQL server 9.5
* libpq-dev (Ubuntu)
* Redis, if you want WebSockets

# Installation

1. Bootstrap the project

	    $ ./bootstrap.sh
	    Run '. ./activate.sh' to activate this environment.
	    $ . ./activate.sh
	    See 'inv --list' for available tasks.

2. Create a configuration file (see below), e.g. `qabel.yaml`

3. Set settings (see below for details), but most importantly:

	- Change SECRET_KEY and keep it save
	- Change database settings accordingly to your needs

4. Initial deployment

	    inv deploy

5. Point your uWSGI master/emperor at `deployed/current/uwsgi.ini`

   For example:

        uwsgi --master --http-socket=:9090 /path/to/drop/deployed/current/uwsgi.ini

   Or, assuming you have other Qabel servers in `/path/to/apps/`:

        uwsgi --emperor /path/to/apps/*/deployed/current/uwsgi.ini

    Usually you'd have this as a system-level service though.

## <a name="production_setup"></a>Production setup

* We recommend [uWSGI Emperor](http://uwsgi-docs.readthedocs.io/en/latest/Emperor.html)
* Add `deployed/current/uwsgi.ini` as a uWSGI Vassal (this file is created by `inv deploy` described below).
* But you can of course also just run it in the normal uWSGI master mode as in

        uwsgi --master /somewhere/qabel-drop/deployed/current/uwsgi.ini

* (Optional) use a webserver of your choice as a proxy (we recommend nginx) if you use a uwsgi UNIX socket.

Django uses Python modules for configuration which is often cumbersome when deploying applications. Therefore we use
some scripts based on invoke to handle this automatically. When using these scripts the configuration happens in
dedicated YAML configuration files instead.

The search path is:

* /etc/invoke.yaml, /etc/qabel.yaml
* ~/.invoke.yaml, ~/.qabel.yaml
* ./invoke.yaml, ./qabel.yaml

A sample production configuration could look like this (note that due to the flexibility of YAML an existing Django
settings.py file can be almost always copied over; you'll just need to exchange top-level `=` with `:`, e.g.
`DATABASES = {…` → `DATABASES: {…`).

```
qabel:
    drop:
        DEBUG: false
        SECRET_KEY: totally_random_numbers_999_999
        CSRF_COOKIE_SECURE: true
        CSRF_COOKIE_HTTPONLY: true
        X_FRAME_OPTIONS: DENY

        # Push notifications:

        PUSH_NOTIFICATORS:
          - drop_service.notify.FCM
            # Any errors will be logged to the drop_service.notify.fcm logger

        # Note: valid FCM_API_KEY required for drop_service.notify.FCM
        # If there is none, disable it.
        FCM_API_KEY: '<put your API key into site-local configuration>'

        # To proxy the FCM API requests through a HTTP proxy set this to a python-requests-compatible value.
        # See http://docs.python-requests.org/en/master/api/#requests.Session.proxies
        FCM_PROXY: ~

        ALLOWED_HOSTS:
          - qabel-drop.example.net

        DATABASES:
            default:
                ENGINE: django.db.backends.postgresql
                NAME: qabel-drop
                USER: qabel-drop
        uwsgi:
            processes: 2
            http-socket: :9697
```

See the [django documentation](https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/) for a checklist of
settings you need to revisit for deployment.

Also see the full list of [django core options](https://docs.djangoproject.com/en/1.9/ref/settings/), especially about
[databases](https://docs.djangoproject.com/en/1.9/ref/settings/#databases).

The server exports [prometheus](https://www.prometheus.io) metrics at /metrics. If those should not be public, you should
block this location in the webserver.

If you have problems with CORS (Cross-Origin Resource Sharing), edit the 'CORS_ORIGIN_WHITELIST' in the
configuration. For more information see [CORS middleware configuration options](https://github
.com/zestedesavoir/django-cors-middleware#configuration).

`manage.py` commands in production are run with `inv manage` instead of `python manage.py`. Note that the former
requires quotes around the command line:

	inv manage 'check --deploy'

Also note that changes in configuration are (on purpose) not reflected in the `inv manage` environment until you ran
`inv deploy` to actually deploy them.

Finally, after writing a configuration file, it is time to deploy (note that this step requires the database settings
to be correct, and the database to be available, since `inv deploy` also runs any database up/downgrades that may be
necessary):

    inv deploy

Done. If a bad commit is deployed roll it back:

    inv deploy --commit <known good commit>

`deployed/deploy-history` keeps track of which commits where deployed when if you are in doubt.

There is also support for multiple concurrent deployments for e.g. blue/green deployments: `inv deploy --into green`
would deploy the application into `deployed/green/uwsgi.ini`.

## Push notifications

Support for push notifications is available for Firebase Cloud Messaging (FCM). New drop messages
are posted via topic data messages to `/topic/<drop-id>`. Topic subscription is handled solely by FCM.
The data messages have the following structure:

    {
        'drop-id': STR drop_id,
        'message': STR base64(message),
    }

Note that unlike drop IDs which are encoded in URL-friendly base64 (RFC 4648 section 5, see
[drop specification](http://qabel.github.io/docs/Qabel-Protocol-Drop/)) the message is encoded
in standard base64.

Naturally using FCM requires obtaining a proper API key from Google. Operation without push notifications,
or no notifications at all is possible and does not require an API key:

    qabel:
        drop:
            PUSH_NOTIFICATORS: []

# Running the tests

`$ py.test` (that's it)

# Run it using Docker!!1!

1. Clone this Repository
2. Change Docker/invoke.yml according to your needs
3. run Docker build
4. Run the Container
