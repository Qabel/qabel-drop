#!/bin/sh
inv deploy
uwsgi deployed/current/uwsgi.ini
