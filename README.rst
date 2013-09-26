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

::
    
    #!/usr/bin/env python
    
    import sys
    import os
    
    from djeasytests.testsetup import TestSetup, default_settings
    
    # optionally add apps to path

    local_apps = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'local_apps')
    if not local_apps in sys.path:
        sys.path.append(local_apps)    

    new_settings = dict(
        ROOT_URLCONF='project.urls',
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'project.sqlite',
        },
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.admin',
            'django.contrib.sites',
            'django.contrib.staticfiles',
        ]
    )
    
    testsetup = TestSetup(appname='project', new_settings=new_settings)
    
    if __name__ == '__main__':
        testsetup.run('shell') # Can be 'tests', 'shell', 'testserver' or 'manage'

Using default settings:


app/base_settings.py

::
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'base.sqlite',
    }

app/settings.py

::
    
    from app.base_settings import *
    from local_settings import *
    
    app/local_settings.py
    
    ::
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'local.sqlite',
    }

app/dev_settings.py

::
    
    from django.conf import global_settings
    from app.base_settings import *
    
runshell.py

::    

    new_settings = dict(
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'project.sqlite',
            }
        }
    )
    
    from app import dev_settings
    testsetup = TestSetup(appname='project', default_settings=dev_settings, new_settings=new_settings)


Example usage in runmanage.py:

::

    #!/usr/bin/env python
    
    from runshell import testsetup
    
    if __name__ == '__main__':
        testsetup.run('manage') # Can be 'tests', 'shell', 'testserver' or 'manage'
        

        
        
