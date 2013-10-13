================
django-easytests
================

Utils for test setup based on test utils from django-cms

Installation
------------

For the current stable version:

::

    pip install django-easytests

For the development version:

::

    pip install -e git+git://github.com/fivethreeo/django-easytests.git@develop#egg=django-easytests

Example usage in develop.py:
-----------------------------

::
    
    #!/usr/bin/env python
    
    from djeasytests.testsetup import TestSetup

    settings = dict(
        ROOT_URLCONF='appname_test_project.urls',
        INSTALLED_APPS = [
            'appname_test_project',
            'appname',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.admin',
            'django.contrib.sites',
            'django.contrib.staticfiles'
        ]
    )
    
    testsetup = TestSetup(
        appname='appname',
        test_settings=settings
    )
    
    if __name__ == '__main__':
        testsetup.run(__file__)
    
Project structure
-----------------

    How to lay out files for using django-easytests::
    
        django-appname
          ...
          appname/
            __init__.py
            views.py
            urls.py
            models.py
            tests.py
          testing/
            appname_test_project/
                __init__.py
                templates/appname/
          README.rst
          MANIFEST.in
          LICENSE
          .travis.yml
          develop.py
          ...

Running tests and commands
--------------------------

::

    develop.py test
    develop.py --failfast test
    develop.py --parallel test
    develop.py --migrate test
    develop.py test test_labels here
    develop.py timed test
    develop.py isolated test
    develop.py manage help
    develop.py manage syncdb
    develop.py server

Using a custom database
-----------------------

Simply set a environment varable::

    export DATABASE_URL="postgres://myuser:mypass@localhost/mydb"
    
Then test, server and manage will use this database.

Using existing settings:
-----------------------

Useful for testing projects

appname/base_settings.py
========================

::
    
    ROOT_URLCONF = 'appname.urls',
    INSTALLED_APPS = [
        'appname'.
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.admin',
        'django.contrib.sites',
        'django.contrib.staticfiles'
    ]
    
    
appname/settings.py
===================

::
    
    from appname.base_settings import *
    from local_settings import *
    
appname/local_settings.py
=========================

::
    
    SOME_LOCAL_SETTING = False


develop.py
==========

::
    
    settings = dict(
        DEBUG = True
    )
    
    from appname import base_settings
    testsetup = TestSetup(
       appname='appname',
       test_settings=settings,
       fallback_settings=base_settings
    )
    
    if __name__ == '__main__':
        testsetup.run(__file__)

default_settings
================

By default fallback_settings gets merged with default_settings ( by default django.conf.global_settings) like in djangos settings.configure.

This can be changed by passing default_settings with a module/object other than global_settings to TestSetup.

::

    from appname import other_global_settings
    testsetup = TestSetup(
        appname='appname',
        test_settings=settings,
        fallback_settings=base_settings,
        default_settings=other_global_settings
    )

Additional apps (test_modules) for testing
==========================================

    Say you want this filestructure when the amount of test increase exponentially::

        django-appname
          ...
          appname/
            __init__.py
            views.py
            urls.py
            models.py
          testing/
            appname_test_project/
                __init__.py
                templates/appname/
            appname_modeltests/
                __init__.py
                tests.py
                models.py
            appname_admintests/
                __init__.py
                tests.py
                models.py
            appname_somothertests/
                __init__.py
                tests.py
                models.py
          README.rst
          MANIFEST.in
          LICENSE
          .travis.yml
          develop.py
          ...

    In develop.py::
        
        from djeasytests.testsetup import TestSetup
    
        settings = dict(
            ROOT_URLCONF='appname_test_project.urls',
            INSTALLED_APPS = [
                'appname_modeltests',
                'appname_admintests',
                'appname_somothertests',
                'appname_test_project',
                'appname',
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.admin',
                'django.contrib.sites',
                'django.contrib.staticfiles'
            ]
        )
    
        testsetup = TestSetup(
            appname='appname',
            test_settings=settings,
            test_modules=['appname_modeltests','appname_admintests','appname_somothertests']
        )
        
            
        if __name__ == '__main__':
            testsetup.run(__file__)