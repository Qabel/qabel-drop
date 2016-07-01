# The following is specially crafted for Django projects

import sys

import pprintpp

from invoke import Collection, run, task
from invoke.util import cd

from tasks_base import trees, deployed
from tasks_base import Project, BaseUwsgiConfiguration, get_tree_commit, commit_is_ancestor


def manage_command(tree, config, args, hide='out'):
    environment = {
        'DJANGO_SETTINGS_MODULE': config.settings_module(),
        'PYTHONPATH': str(config.settings_pythonpath()),
    }
    return run('{python} -Wi {manage} '.format(python=tree / '_venv/bin/python', manage=tree / 'manage.py') + args, env=environment, hide=hide)


class UwsgiConfiguration(BaseUwsgiConfiguration):
    def __init__(self, project, ctx, config, tree, path):
        super().__init__(config, tree, path)
        self.project = project
        self.ctx = ctx

        self.basename = self.path.with_suffix('').name
        self.settings_path = self.tmp_path / 'settings.py'

        # By default automagic, but allow override
        if 'STATIC_ROOT' not in self.config:
            self.config.config['STATIC_ROOT'] = str((self.path.parent / 'static').absolute())

        # generated stuff first, so we can override it later manually, if ever necessary
        self.sections.append(self.automagic())
        self.sections.append(self.uwsgi_config())

        self.make_settings()

    def emplace(self):
        super().emplace()
        manage_command(self.tree, self, 'collectstatic --noinput')

    def settings_module(self):
        return self.settings_path.with_suffix('').name

    def settings_pythonpath(self):
        return self.path.parent.absolute()

    def automagic(self):
        """Return automatically inferred|inferrable configuration."""
        config = {
            'plugin': 'python3',
            'module': self.project.project_config['wsgi_app'],

            # Path to the settings module generated (e.g. deployed/current.py)
            'python-path': self.settings_pythonpath(),
            'env': 'DJANGO_SETTINGS_MODULE=' + self.settings_module(),

            # Where the app packages (e.g. qabel_provider, qabel_id) live
            'pythonpath': '{tree}',

            'chdir': '{basedir}',

            'virtualenv': '{virtualenv}',
            'touch-chain-reload': '{uwsgi_ini}',
            'lazy-apps': True,
        }
        if 'STATIC_ROOT' in self.config:
            # Serve static files by default via uWSGI, but it could also be done by the reverse proxy
            # (or rsync the directory to your favourite CDN)
            config['static-map'] = '/static=' + self.config.STATIC_ROOT
        return 'automatically inferred configuration', config

    def make_settings(self):
        with self.settings_path.open('w') as settings:
            self.write_info(settings)
            print(file=settings)
            print(self.project.project_config['settings_prelude'], file=settings)
            print(file=settings)
            for key, value in self.config.items():
                if key == 'uwsgi':
                    continue
                if key.islower():
                    print('Invalid Django setting "{key}".'.format(key=key))
                    sys.exit(1)
                print(key, '=', end=' ', file=settings)
                pprintpp.pprint(value, indent=4, stream=settings)


class Django(Project):
    def __init__(self, project_config):
        self.project_config = project_config

    def make_namespace(self):
        return Collection(*self._tasks())

    def migrate_db(self, ctx, config, from_tree, to_tree):
        def manage_py(against, args, hide='out'):
            return manage_command(against, config, args, hide=hide)

        def get_migrations(tree):
            # showmigrations output looks like this:
            # <app label>
            #  [X] <migration name>  <-- applied migration
            #  [ ] <migration>       <-- not applied
            line_prefix_length = len(' [X] ')
            all_migrations = manage_py(tree, 'showmigrations').stdout.splitlines()
            app_migrations = {}
            while all_migrations:
                current_app = all_migrations.pop(0)
                migrations = []
                while all_migrations and all_migrations[0].startswith(' ['):
                    migrations.append(all_migrations.pop(0))
                # migrations is now a list of " [x] nnnn_...", find last applied and the last overall migration
                last_migration = migrations[-1][line_prefix_length:]
                applied_migrations = filter(lambda m: m.startswith(' [X] '), migrations)
                last_applied_migration = None
                for last_applied_migration in applied_migrations:
                    pass
                if last_applied_migration:
                    last_applied_migration = last_applied_migration[line_prefix_length:]

                app_migrations[current_app] = last_applied_migration, last_migration
            return app_migrations

        if from_tree:
            current_commit = get_tree_commit(from_tree)
            to_commit = get_tree_commit(to_tree)

            # We are upgrading if the current current commit is an ancestor (precedes) the commit we are deploying.
            # Otherwise it's an downgrade. This is important because we need to use the tree which has the most currently
            # applied migration when downgrading, since the downgraded-to-tree cannot undo migrations it doesn't know.
            upgrading = commit_is_ancestor(current_commit, to_commit)
        else:
            # If we have no old tree it's always a straight upgrade of everything
            upgrading = True

        print('Database is being', 'upgraded' if upgrading else 'downgraded')

        if upgrading:
            manage_py(to_tree, 'migrate')
        else:
            if from_tree:
                from_migrations = get_migrations(from_tree)
            else:
                from_migrations = {}
            to_migrations = get_migrations(to_tree)

            not_migrated = []
            for application, (_, target_migration) in to_migrations.items():
                try:
                    applied_migration, _ = from_migrations[application]
                except KeyError:
                    applied_migration = '<None/Unknown>'
                if applied_migration == target_migration:
                    not_migrated.append(application)
                    continue
                print('Migrating \'{app}\': {applied} -> {target}'.format(app=application, applied=applied_migration,
                                                                          target=target_migration))
                if upgrading:
                    against = to_tree
                else:
                    against = from_tree
                manage_py(against, 'migrate {app} {target}'.format(app=application, target=target_migration))
            print('No migrations needed for:', ', '.join(not_migrated))

    def get_context_config(self, ctx):
        return ctx.qabel[self.project_config['name']]

    def uwsgi_configuration(self, ctx, tree, path):
        return UwsgiConfiguration(self, ctx, self.get_context_config(ctx), tree, path)

    def _tasks(self):
        @task(
            help={
                'which': 'which ini to use (deployed/<which>.ini). Default: current',
                'command': 'command to run (don\'t forget quotes around it)',
            },
            positional=('command')
        )
        def manage(ctx, command, which='current'):
            """
            Run manage.py command in a deployed environemnt.
            """
            configuration_path = deployed / which / 'uwsgi.ini'
            tree = trees / UwsgiConfiguration.get_commit_from_config(configuration_path)
            config = self.uwsgi_configuration(ctx, tree, configuration_path)
            manage_command(tree, config, command, hide=None)

        return (manage,)
