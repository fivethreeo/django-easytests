from __future__ import with_statement
import os
import sys
import argparse
from djeasytests.tmpdir import temp_dir

gettext = lambda s: s

default_settings = dict(
    CACHE_BACKEND = 'locmem:///',
    DEBUG = True,
    TEMPLATE_DEBUG = True,
    DATABASE_SUPPORTS_TRANSACTIONS = True,
    SITE_ID = 1,
    USE_I18N = True,
    MEDIA_URL = '/media/',
    STATIC_URL = '/static/',
    ADMIN_MEDIA_PREFIX = '/static/admin/',
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend',
    SECRET_KEY = 'key',
    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
        'django.template.loaders.eggs.Loader',
    ),
   TEMPLATE_CONTEXT_PROCESSORS = [
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.i18n",
        "django.core.context_processors.debug",
        "django.core.context_processors.request",
        "django.core.context_processors.media",
        'django.core.context_processors.csrf',
        "django.core.context_processors.static"
    ],
    MIDDLEWARE_CLASSES = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.doc.XViewMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware'
    ],
    INSTALLED_APPS = [
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'django.contrib.sites',
        'django.contrib.staticfiles'
    ],
    LANGUAGE_CODE = "en",
    LANGUAGES = (
        ('en', gettext('English')),
        ('fr', gettext('French')),
        ('de', gettext('German')),
        ('pt-BR', gettext("Brazil")),
        ('nl', gettext("Dutch")),
    ),
    SOUTH_TESTS_MIGRATE = False
)
    
class TestSetup(object):
    
    def __init__(self, appname='djeasytests', default_settings={}):
        self.default_settings = default_settings
        self.appname = appname
        
    def get_argparser(self):
        return argparse.ArgumentParser()
        
    def argparser_tests(self):
        parser = self.get_argparser()
        parser.add_argument('--jenkins', action='store_true', default=False,
                dest='jenkins')
        parser.add_argument('--jenkins-data-dir', default='.', dest='jenkins_data_dir')
        parser.add_argument('--coverage', action='store_true', default=False,
                dest='coverage')
        parser.add_argument('--failfast', action='store_true', default=False,
                dest='failfast')
        parser.add_argument('--verbosity', default=1)
        parser.add_argument('--time-tests', action='store_true', default=False,
                dest='time_tests')
        parser.add_argument('test_labels', nargs='*')
        return parser
        
    def argparser_testserver(self):
        parser = self.get_argparser()
        parser.add_argument('-p', '--port', default='8000')
        parser.add_argument('-b', '--bind', default='127.0.0.1')
        return parser
                
    def argparser_shell(self):
        return self.get_argparser()
        
    def argparser_manage(self):
        parser = self.get_argparser()
        return parser
    
    def run(self, what):
        if what in ('tests', 'shell', 'testserver', 'manage'):
            tmp_dir_prefix = '%s-test-tmpdir' % self.appname
            with temp_dir(prefix=tmp_dir_prefix) as STATIC_ROOT:
                with temp_dir(prefix=tmp_dir_prefix) as MEDIA_ROOT:
                    getattr(self, 'run%s' % what)(STATIC_ROOT=STATIC_ROOT, MEDIA_ROOT=MEDIA_ROOT)
        
    def runtests(self, **kwargs):
        parser = self.argparser_tests()
        args = parser.parse_args()
        
        if getattr(args, 'jenkins', False):
            test_runner = 'djeasytests.runners.JenkinsTestRunner'
        else:
            test_runner = 'djeasytests.runners.NormalTestRunner'
        junit_output_dir = getattr(args, 'jenkins_data_dir', '.')
        time_tests = getattr(args, 'time_tests', False)
        
        test_labels = ['%s.%s' % (self.appname, label) for label in args.test_labels]
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
                  
    def runtestserver(self, **kwargs):
        parser = self.argparser_testserver()
        args = parser.parse_args()
        settings = self.configure(args=args, **kwargs)
        self.setup_database(settings)
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
        rs.addr = args.bind
        rs.port = args.port
        rs.inner_run(addrport='%s:%s' % (args.bind, args.port),
           insecure_serving=True)
    
    def runshell(self, **kwargs):
        parser = self.argparser_shell()
        args = parser.parse_args()
        settings = self.configure(args=args, **kwargs)
        self.setup_database(settings)
        from django.core.management import call_command
        call_command('shell')
        
    def runmanage(self, **kwargs):
        parser = self.argparser_manage()
        args, rest = parser.parse_known_args()
        settings = self.configure(args=args, **kwargs)
        self.setup_database(settings)
        from django.core.management import execute_from_command_line
        execute_from_command_line([sys.argv[0]] + rest)
                
    def handle_args(self, args):
        return {}
                
    def configure(self, args=None, **kwargs):
        from django.conf import settings
        defaults = self.default_settings
        
        if 'MEDIA_ROOT' in defaults and 'MEDIA_ROOT' in kwargs:
            del kwargs['MEDIA_ROOT']
        if 'STATIC_ROOT' in defaults and 'STATIC_ROOT' in kwargs:
            del kwargs['STATIC_ROOT']
         
        defaults.update(kwargs)
        defaults.update(self.handle_args(args))
        settings.configure(**defaults)
        return settings
                
    def setup_database(self, settings):
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
