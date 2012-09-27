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
        
    # optionally add existing project settings
    
    from djeasytests.utils import settings_to_dict
    from project import settings
    default_settings.update(settings_to_dict(settings))
        
    default_settings.update(dict(
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
    ))
    
    testsetup = TestSetup(appname='project', default_settings=default_settings)
    
    if __name__ == '__main__':
        testsetup.run('shell') # Can be 'tests', 'shell', 'testserver' or 'manage'
        
Example usage in runmanage.py:

::

    #!/usr/bin/env python
    
    from runshell import testsetup
    
    if __name__ == '__main__':
        testsetup.run('manage') # Can be 'tests', 'shell', 'testserver' or 'manage'
        

        
        