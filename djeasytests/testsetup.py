from __future__ import with_statement
import os
import sys
import argparse
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
        
        
class TestSetup(object):
    
    __doc__ = '''django development helper script.
Usage:
    %(filename)s [--parallel | --failfast] [--migrate] test [<test-label>...]
    %(filename)s timed test [test-label...]
    %(filename)s [--parallel] [--migrate] isolated test [<test-label>...]
    %(filename)s [--port=<port>] [--bind=<bind>] [--migrate] server
    %(filename)s [--migrate] shell
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
'''
    
    default_settings = None
    
    def __init__(self, appname='djeasytests', settings={}, fallback_settings=None, default_settings=global_settings, version=None):
        
        self.version = version
        
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
                    
    def test(self, **kwargs):

        time_tests = getattr(args, 'time_tests', False)
        
        test_labels = ['%s.%s' % (self.appname, label) for label in self.args.test_labels]
        if not test_labels:
            test_labels = [self.appname]
            
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
        
        self.configure(args=args, TEST_RUNNER=test_runner, JUNIT_OUTPUT_DIR=junit_output_dir,
            TIME_TESTS=time_tests, DATABASES=DATABASES, **kwargs)
            
        from django.conf import settings
        from django.test.utils import get_runner
        TestRunner = get_runner(settings)
    
        test_runner = TestRunner(verbosity=args.verbosity, interactive=False, failfast=args.failfast)
        failures = test_runner.run_tests(test_labels)
        sys.exit(failures)
                  
    def server(self, **kwargs):
        parser = self.argparser_testserver()
        self.args = parser.parse_args()
        new_settings = self.configure(args=args, **kwargs)
        self.setup_database(new_settings, no_sync=args.no_sync)
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
            print
            print "A admin user (username: admin, password: admin) has been created."
            print
        from django.contrib.staticfiles.management.commands import runserver
        rs = runserver.Command()
        rs.stdout = sys.stdout
        rs.stderr = sys.stderr
        rs.use_ipv6 = False
        rs._raw_ipv6 = False
        rs.addr = self.args.bind
        rs.port = self.args.port
        rs.inner_run(addrport='%s:%s' % (args.bind, self.args.port),
           insecure_serving=True)
    
    def shell(self, **kwargs):
        new_settings = self.configure(args=args, **kwargs)
        self.setup_database(new_settings, no_sync=args.no_sync)
        from django.core.management import call_command
        call_command('shell')
        
    def manage(self, **kwargs):
        new_settings = self.configure(args=args, **kwargs)
        self.setup_database(new_settings, no_sync=args.no_sync)
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
