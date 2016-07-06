
import datetime

from pathlib import Path

from invoke import task
from invoke.config import Config

from tasks_base import trees, virtualenvs, deployed
from tasks_base import ref_to_sha1, create_virtualenv, load_project, BaseUwsgiConfiguration

project = load_project(Path(__file__).parent)


@task(help={
    'commit': 'git commit, e.g. sha1, branch, HEAD, HEAD~1. Default: HEAD'
})
def checkout(ctx, commit='HEAD'):
    """Checkout <commit> into trees/<id>/ and create an environment to run the app."""
    trees.mkdir(exist_ok=True)
    # Note that this never collides unless the full sha1 collides, since git detects short-sha1 collisions and makes
    # it's output longer to compensate.
    sha1 = ref_to_sha1(commit)
    print('Resolved \'{commit}\' to {sha1}'.format(commit=commit, sha1=sha1))
    tree = trees / sha1
    if tree.is_dir():
        # Idempotency
        return tree
    ctx.run('git archive --prefix {tree}/ {sha1} | tar x'.format(tree=tree, sha1=sha1))
    create_virtualenv(tree, virtualenvs)
    return tree


@task(help={
    'commit': 'commit identifier to deploy (e.g. sha1, HEAD[~n], branch name, ...). Default: HEAD',
    'into': 'name of deployment; existing file will be replaced. Default: current',
    'from': 'name previous deployment, used for finding database migrations. Default: current',
})
def deploy(ctx, commit='HEAD', into='current', _from='current'):
    """
    Deploy <commit> to deployed/<into>.ini (uWSGI configuration). Migrate database to <commit>.

    Creates trees/<commit>/ and populates it, if necessary. See 'inv --help checkout'.

    A configuration file is generated from defaults and local configuration. It is placed at deployed/<into>.ini and
    contains all merged configuration.
    """
    from_config = deployed / _from / 'uwsgi.ini'
    if from_config.exists():
        from_commit = BaseUwsgiConfiguration.get_commit_from_config(from_config)
        from_tree = trees / from_commit
    else:
        from_tree = None
    tree = checkout(ctx, commit)
    configuration_path = deployed / into / 'uwsgi.ini'

    config = project.uwsgi_configuration(ctx, tree, configuration_path)
    config.emplace()
    project.migrate_db(ctx, config, from_tree, tree)
    with (deployed / 'deploy-history').open('a') as history:
        print(datetime.datetime.now(), tree, file=history)


def try_load(path, configurable):
    """Try to load configuration file at *path* and merge it into *configurable*."""
    if not path.exists():
        return False
    loader = getattr(Config, '_load_' + path.suffix.lstrip('.'))
    configurable.configure(loader(None, str(path)) or {})
    return True


def load_local_configuration(configurable):
    """.configure() *configurable* with local configuration."""
    # This is a bit ugly and should be something upstream invoke should be able to do by itself.
    for path in ['/etc/qabel', '~/.qabel', Path(__file__).with_name('qabel')]:
        path = Path(path).expanduser()
        for suffix in ['.yaml', '.py', '.json']:
            path_with_suffix = path.with_suffix(suffix)
            if try_load(path_with_suffix, configurable):
                print('Picked up extra configuration from', path)

namespace = project.make_namespace()
namespace.add_task(checkout)
namespace.add_task(deploy)
assert try_load(Path(__file__).with_name('defaults.yaml'), namespace)
load_local_configuration(namespace)
