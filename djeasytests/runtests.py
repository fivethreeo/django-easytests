#!/usr/bin/env python
from __future__ import with_statement
from djeasytests.tmpdir import temp_dir
import argparse
import sys

def runtests(configure=None, test_runner=None, junit_output_dir='.',
         time_tests=False, verbosity=1, failfast=False,
         test_labels=None, default_test_labels=None, tmp_dir_prefix=None, **kwargs):
    if not test_labels:
        test_labels = default_test_labels
    with temp_dir(prefix=tmp_dir_prefix) as STATIC_ROOT:
        with temp_dir(prefix=tmp_dir_prefix) as MEDIA_ROOT:
            configure(TEST_RUNNER=test_runner, JUNIT_OUTPUT_DIR=junit_output_dir,
                TIME_TESTS=time_tests, STATIC_ROOT=STATIC_ROOT, MEDIA_ROOT=MEDIA_ROOT, **kwargs)
            from django.conf import settings
            from django.test.utils import get_runner
            TestRunner = get_runner(settings)
        
            test_runner = TestRunner(verbosity=verbosity, interactive=False, failfast=failfast)
            failures = test_runner.run_tests(test_labels)
    sys.exit(failures)
    
def runtests_parse(test_labels_prefix='djeasytests', default_test_labels=['djeasytests'], tmp_dir_prefix='djeasytests', **kwargs):
    parser = argparse.ArgumentParser()
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
    args = parser.parse_args()
    if getattr(args, 'jenkins', False):
        test_runner = 'djeasytests.runners.JenkinsTestRunner'
    else:
        test_runner = 'djeasytests.runners.NormalTestRunner'
    junit_output_dir = getattr(args, 'jenkins_data_dir', '.')
    time_tests = getattr(args, 'time_tests', False)
    test_labels = ['%s.%s' % (test_labels_prefix, label) for label in args.test_labels]
    runtests(test_runner=test_runner, junit_output_dir=junit_output_dir, time_tests=time_tests,
         verbosity=args.verbosity, failfast=args.failfast,
         test_labels=test_labels, default_test_labels=default_test_labels, tmp_dir_prefix=tmp_dir_prefix, **kwargs)