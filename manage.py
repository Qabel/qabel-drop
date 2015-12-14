from flask import url_for

from database import init_db
from flask_script import Manager

from views import app

manager = Manager(app)

@manager.command
def create_db():
    print('Create tables')
    init_db()
    print('Created tables')

@manager.command
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        print(rule)

        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)

        methods = ','.join(rule.methods)
        url = url_for(rule.endpoint, **options)
        line = urllib.parse.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
        output.append(line)

    for line in sorted(output):
        print(line)

if __name__ == "__main__":
    manager.run()
    init_db()