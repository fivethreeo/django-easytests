from __future__ import print_function
import multiprocessing
import pkgutil
import pyclbr
import subprocess
import os
import sys
import warnings

from docopt import docopt
import dj_database_url

from django import VERSION
from django.utils import autoreload
from django.conf import global_settings
from django.conf import settings

from djeasytests.tmpdir import temp_dir

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

def _test_run_worker(test_labels, test_settings, failfast=False, test_runner='django.test.simple.DjangoTestSuiteRunner'):
    warnings.filterwarnings(
        'error', r"DateTimeField received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')
    test_settings.TEST_RUNNER = test_runner
    from django.test.utils import get_runner
    TestRunner = get_runner(test_settings)

    test_runner = TestRunner(verbosity=1, interactive=False, failfast=failfast)
    failures = test_runner.run_tests(test_labels)
    return failures

def _test_in_subprocess(args):
    test_label, script, migrate = args
    return subprocess.call(['python', script] + (migrate and ['--migrate'] or []) + ['test', test_label])

def _test_run_worker_settings(tests):
    test_labels, test_settings = tests
    return _test_run_worker(test_labels, test_settings)
                            
class TestSetup(object):
    
    __doc__ = '''django development helper script.
Usage:
    %(filename)s [--migrate] [--parallel | --failfast] test [<test-label>...]
    %(filename)s [--migrate] timed test [<test-label>...]
    %(filename)s [--migrate] [--parallel] isolated test [<test-label>...]
    %(filename)s [--port=<port>] [--bind=<bind>] server
    %(filename)s shell
    %(filename)s manage [<args>...]
    %(filename)s compilemessages
    %(filename)s makemessages

Options:
    -h --help                   Show this screen.
    --version                   Show version.
    --parallel                  Run tests in parallel.
    --migrate                   Use south migrations in test command.
    --failfast                  Stop tests on first failure (only if not --parallel).
    --port=<port>               Port to listen on [default: 8000].
    --bind=<bind>               Interface to bind to [default: 127.0.0.1].
'''
    
    default_settings = None
    
    def __init__(self, appname='djeasytests', test_settings={}, test_modules=None, fallback_settings=None, default_settings=global_settings, version=None):
        
        self.version = version
        self.test_modules = test_modules or [appname]
         
        if fallback_settings:
            if default_settings:
                self.default_settings = GlobalSettingsWrapper(fallback_settings, default_settings)
            else:
                self.default_settings = fallback_settings
        else:
            self.default_settings = default_settings
            
        self.new_settings = test_settings
        self.appname = appname

    def get_doc(self):
        return self.__doc__ % {'filename': self.filename}
        
    def get_args(self):
        return docopt(self.get_doc(), version=self.version, options_first=True)
    
    def run(self, thefile):
        self.path = os.path.abspath(thefile)
        self.dirname = os.path.dirname(self.path)
        self.filename = os.path.basename(self.path)
        testing = os.path.join(self.dirname, 'testing')
        
        if not testing in sys.path:
            sys.path.append(testing)
        
        self.args = self.get_args()
        if self.args.get('test', False):
            if self.args.get('isolated', False):
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
            elif self.args.get('timed', False):
                num_failures = self.timed()
            else:
                num_failures = self.test()
            sys.exit(num_failures)
        elif self.args.get('server', False):
            self.server()
        elif self.args.get('shell', False):
            self.shell()
        elif self.args.get('compilemessages', False):
            self.compilemessages()
        elif self.args.get('makemessages', False):
            self.makemessages()
        elif self.args.get('manage', False):
            self.manage()
            
    def server(self, bind='127.0.0.1', port=8000):
        self.configure()
        if os.environ.get("RUN_MAIN") != "true":
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
                        
    def isolated(self):
        parallel= self.args.get('--parallel', False)
        test_labels =  self.args.get('<test-label>', '') or _get_test_labels(self.test_modules)
        if parallel:
            pool = multiprocessing.Pool()
            mapper = pool.map
        else:
            mapper = map
        migrate = self.args.get('--migrate', False)    
        results = mapper(_test_in_subprocess, ((test_label, self.path, migrate) for test_label in test_labels))
        failures = [test_label for test_label, return_code in zip(test_labels, results) if return_code != 0]
        return failures
    
    def timed(self):
        test_labels =  self.args.get('<test-label>', '') or _get_test_labels(self.test_modules)
        test_settings = self.configure()
        return _test_run_worker(test_labels, test_settings, test_runner='djeasytests.runners.TimedTestRunner')
    
    def test(self):
        parallel= self.args.get('--parallel', False)
        failfast= self.args.get('--failfast', False)
        test_labels =  self.args.get('<test-label>', '') or _get_test_labels(self.test_modules)
        test_settings = self.configure()
        if parallel:
            worker_tests = _split(test_labels, multiprocessing.cpu_count())

            pool = multiprocessing.Pool()
            # fixme
            failures = sum(pool.map(_test_run_worker_settings, ([test, test_settings] for test in worker_tests)))
            return failures
        else:
            return _test_run_worker(test_labels, test_settings, failfast=failfast)
    
    def compilemessages(self):
        self.configure()
        from django.core.management import call_command
        os.chdir(self.appname)
        call_command('compilemessages', all=True)
    
    def makemessages(self):
        self.configure()
        from django.core.management import call_command
        os.chdir(self.appname)
        call_command('makemessages', all=True)
    
    def shell(self):
        self.configure()
        from django.core.management import call_command
        call_command('shell')
            
    def manage(self):
        self.configure()
        from django.core.management import execute_from_command_line
        execute_from_command_line([self.filename] + self.args.get('<args>', []))
                
    def configure(self, **kwargs):
        migrate = self.args.get('--migrate', False)
        kwargs['SOUTH_TESTS_MIGRATE'] = migrate
        
        if not 'DATABASES' in self.new_settings:
            default_name = ':memory:' if self.args.get('test', False) else 'local.sqlite'
            db_url = os.environ.get("DATABASE_URL", "sqlite://localhost/%s" % default_name)
            kwargs['DATABASES'] = {'default': dj_database_url.parse(db_url)}
            
        tmp_dir_prefix = '%s-test-tmpdir' % self.appname
        with temp_dir(prefix=tmp_dir_prefix) as STATIC_ROOT:
            with temp_dir(prefix=tmp_dir_prefix) as MEDIA_ROOT:
                if not 'MEDIA_ROOT' in self.new_settings:
                    kwargs['MEDIA_ROOT'] = MEDIA_ROOT
                if not 'STATIC_ROOT' in self.new_settings:
                     kwargs['STATIC_ROOT'] = STATIC_ROOT
                kwargs.update(self.new_settings)
                settings.configure(default_settings=self.default_settings, **kwargs)
                return settings

