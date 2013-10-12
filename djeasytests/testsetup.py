from __future__ import print_function
import multiprocessing
import pkgutil
import pyclbr
import subprocess
import os
import sys
import warnings

from docopt import docopt
from django import VERSION
from django.utils import autoreload

from djeasytests.tmpdir import temp_dir
from django.conf import global_settings
from django.conf import settings

class GlobalSettingsWrapper:
    
    def __init__(self, settings, default_settings):
        self.settings = settings
        self.default_settings = default_settings
        
    def __getattr__(self, setting):
        try:
            return getattr(self.settings, setting)
        except AttributeError:
            return getattr(self.default_settings, setting)
        
def _split(itr, num):
    split = []
    size = int(len(itr) / num)
    for index in range(num):
        split.append(itr[size * index:size * (index + 1)])
    return split

def _get_test_labels(test_modules):
    test_labels = []
    for test_module in test_modules:
        for module in [name for _, name, _ in pkgutil.iter_modules([os.path.join(test_module,"tests")])]:
            clsmembers = pyclbr.readmodule("%s.tests.%s" % (test_module, module))
            for clsname, cls in clsmembers.items():
                for method, _ in cls.methods.items():
                    if method.startswith('test_'):
                        test_labels.append('%s.%s.%s' % (test_module, clsname, method))
    return test_labels

def _test_run_worker(test_labels, settings=None, failfast=False, test_runner='django.test.simple.DjangoTestSuiteRunner'):
    warnings.filterwarnings(
        'error', r"DateTimeField received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')
    settings.TEST_RUNNER = test_runner
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)

    test_runner = TestRunner(verbosity=1, interactive=False, failfast=failfast)
    failures = test_runner.run_tests(test_labels)
    return failures

def _test_in_subprocess(test_labels, script, db=None):
    db = db and ['--db', db] or []
    return subprocess.call(['python', script, 'test'] + db + test_labels)
            
class TestSetup(object):
    
    __doc__ = '''django development helper script.
Usage:
    %(filename)s [--db] [--migrate] [--parallel | --failfast] test [<test-label>...]
    %(filename)s [--db] [--migrate] timed test [<test-label>...]
    %(filename)s [--db] [--migrate] [--parallel] isolated test [<test-label>...]
    %(filename)s [--db] [--migrate] [--port=<port>] [--bind=<bind>] server
    %(filename)s [--db] [--migrate] shell
    %(filename)s [--db] [--migrate] manage
    %(filename)s compilemessages
    %(filename)s makemessages

Options:
    -h --help                   Show this screen.
    --version                   Show version.
    --parallel                  Run tests in parallel.
    --migrate                   Use south migrations in test or server command.
    --failfast                  Stop tests on first failure (only if not --parallel).
    --port=<port>               Port to listen on [default: 8000].
    --bind=<bind>               Interface to bind to [default: 127.0.0.1].
    --db=<db>                   Db to use.
'''
    
    default_settings = None
    
    def __init__(self, appname='djeasytests', settings={}, test_modules=None, fallback_settings=None, default_settings=global_settings, version=None):
        
        self.version = version
        self.test_modules = test_modules or [appname]
         
        if fallback_settings:
            if default_settings:
                self.default_settings = GlobalSettingsWrapper(fallback_settings, default_settings)
            else:
                self.default_settings = fallback_settings
        else:
            self.default_settings = default_settings
            
        self.new_settings = settings
        self.appname = appname

    def get_doc(self):
        return self.__doc__ % {'filename': self.filename}
        
    def get_args(self):
        print(self.get_doc())
        return docopt(self.get_doc(), version=self.version, options_first=True)
    
    def run(self, thefile):
        self.path = os.path.abspath(thefile)
        self.dirname = os.path.dirname(self.path)
        self.filename = os.path.basename(self.path)
        self.args = self.get_args()
        if self.args['test']:
            if self.args['isolated']:
                failures = self.isolated()
                print()
                print("Failed tests")
                print("============")
                if failures:
                    for failure in failures:
                        print(" - %s" % failure)
                else:
                    print(" None")
                num_failures = len(failures)
            elif self.args['timed']:
                num_failures = self.timed()
            else:
                num_failures = self.test()
            sys.exit(num_failures)
        elif self.args['server']:
            self.server()
        elif self.args['shell']:
            self.shell()
        elif self.args['compilemessages']:
            self.compilemessages()
        elif self.args['makemessages']:
            self.makemessages()
            
    def server(self, bind='127.0.0.1', port=8000, migrate=False):
        if os.environ.get("RUN_MAIN") != "true":
            from south.management.commands import syncdb, migrate
            if migrate:
                syncdb.Command().handle_noargs(interactive=False, verbosity=1, database='default')
                migrate.Command().handle(interactive=False, verbosity=1)
            else:
                syncdb.Command().handle_noargs(interactive=False, verbosity=1, database='default', migrate=False, migrate_all=True)
                migrate.Command().handle(interactive=False, verbosity=1, fake=True)
            from django.contrib.auth.models import User
            if not User.objects.filter(is_superuser=True).exists():
                usr = User()
                usr.username = 'admin'
                usr.email = 'admin@admin.com'
                usr.set_password('admin')
                usr.is_superuser = True
                usr.is_staff = True
                usr.is_active = True
                usr.save()
                print('')
                print("A admin user (username: admin, password: admin) has been created.")
                print('')
        from django.contrib.staticfiles.management.commands import runserver
        rs = runserver.Command()
        rs.stdout = sys.stdout
        rs.stderr = sys.stderr
        rs.use_ipv6 = False
        rs._raw_ipv6 = False
        rs.addr = bind
        rs.port = port
        autoreload.main(rs.inner_run, (), {
            'addrport': '%s:%s' % (bind, port),
            'insecure_serving': True,
            'use_threading': True
        })
                        
    def isolated(self, test_labels, parallel=False):
        test_labels = test_labels or _get_test_labels()
        if parallel:
            pool = multiprocessing.Pool()
            mapper = pool.map
        else:
            mapper = map
        results = mapper(_test_in_subprocess, ([test_label] for test_label in test_labels))
        failures = [test_label for test_label, return_code in zip(test_labels, results) if return_code != 0]
        return failures
    
    def timed(self, test_labels):
        return _test_run_worker(test_labels, test_runner='djeasytests.runners.TimedTestRunner')
    
    def test(self, test_labels, parallel=False, failfast=False):
        test_labels = test_labels or _get_test_labels(self.test_modules)
        if parallel:
            worker_tests = _split(test_labels, multiprocessing.cpu_count())
    
            pool = multiprocessing.Pool()
            failures = sum(pool.map(_test_run_worker, worker_tests))
            return failures
        else:
            return _test_run_worker(test_labels, failfast)
    
    def compilemessages():
        from django.core.management import call_command
        os.chdir(self.appname)
        call_command('compilemessages', all=True)
    
    def makemessages():
        from django.core.management import call_command
        os.chdir(self.appname)
        call_command('makemessages', all=True)
    
    def shell():
        from django.core.management import call_command
        call_command('shell')
            
    def manage(self, **kwargs):
        new_settings = self.configure()
        self.setup_database(new_settings)
        from django.core.management import execute_from_command_line
        execute_from_command_line([sys.argv[0]] + rest)
                
    def configure(self, **kwargs):
        tmp_dir_prefix = '%s-test-tmpdir' % self.appname
        with temp_dir(prefix=tmp_dir_prefix) as STATIC_ROOT:
            with temp_dir(prefix=tmp_dir_prefix) as MEDIA_ROOT:
                if not 'MEDIA_ROOT' in self.new_settings:
                    kwargs['MEDIA_ROOT'] = MEDIA_ROOT
                if not 'STATIC_ROOT' in self.new_settings:
                     kwargs['STATIC_ROOT'] = STATIC_ROOT
                    
                kwargs = self.new_settings
                settings.configure(default_settings=self.default_settings, **kwargs)
                return settings
                
    def setup_database(self, settings, no_sync=False):
        if not no_sync:
            databases = getattr(settings, 'DATABASES', None)
            database_name = databases and databases['default']['NAME']
            database_engine = databases and databases['default']['ENGINE'] 
            if database_engine and database_name and database_engine == 'django.db.backends.sqlite3' and database_name != ':memory:':
                new_db = not os.path.exists(database_name)
                from django.core.management import call_command
                if 'south' in settings.INSTALLED_APPS:
                    call_command('syncdb', interactive=False, migrate_all=new_db)
                    call_command('migrate', interactive=False, fake=new_db)
                else:
                    call_command('syncdb', interactive=False)
