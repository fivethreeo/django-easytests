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

    pip install -e git+git://github.com/fivethreeo/django-easytests.git#egg=django-easytests

Example usage in runshell.py:
-----------------------------

::
    
    #!/usr/bin/env python
    
    import sys
    import os
    
    from djeasytests.testsetup import TestSetup
    
    # optionally add apps to path

    local_apps = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'local_apps')
    if not local_apps in sys.path:
        sys.path.append(local_apps)    

    settings = dict(
        ROOT_URLCONF='project.urls',
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'app.sqlite'
        },
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.admin',
            'django.contrib.sites',
            'django.contrib.staticfiles'
        ]
    )
    
    testsetup = TestSetup(appname='app', settings=settings)
    
    if __name__ == '__main__':
        testsetup.run('shell') # Can be 'tests', 'shell', 'testserver' or 'manage'

Using existing settings:
-----------------------

app/base_settings.py
====================

::
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'base.sqlite'
        }
    }

app/settings.py
===============

::
    
    from app.base_settings import *
    from local_settings import *
    
app/local_settings.py
======================

::
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'local.sqlite'
        }
    }


runshell.py
===========

::    

    settings = dict(
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'app.sqlite'
            }
        }
    )
    
    from app import base_settings
    testsetup = TestSetup(appname='app', settings=settings, fallback_settings=base_settings)
    
    if __name__ == '__main__':
        testsetup.run('shell') # Can be 'tests', 'shell', 'testserver' or 'manage'

default_settings
================

By default fallback_settings gets merged with default_settings ( by default django.conf.global_settings) like in djangos settings.configure.

This can be changed by passing default_settings with a module/object other than global_settings to TestSetup.

::

    from app import other_global_settings
    testsetup = TestSetup(appname='app', settings=settings, fallback_settings=base_settings, default_settings=other_global_settings)    

Example usage in runmanage.py:
==============================

::

    #!/usr/bin/env python
    
    from runshell import testsetup
    
    if __name__ == '__main__':
        testsetup.run('manage') # Can be 'tests', 'shell', 'testserver' or 'manage'
        

        
        
