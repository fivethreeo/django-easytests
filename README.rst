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

Example usage in runtests.py:

::
    
    #!/usr/bin/env python
    from djeasytests.testsetup import TestSetup, default_settings
    
    default_settings.update(dict(
        ROOT_URLCONF='shop_categories.test_utils.project.urls',
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'shopexampledb.sqlite',
            }
        },
        INSTALLED_APPS = [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.admin',
            'django.contrib.sites',
            'django.contrib.staticfiles',
            'treeadmin',
            'shop_categories',
            'shop_categories.test_utils.project'
        ],
        SHOP_PRODUCT_MODEL = 'shop_categories.test_utils.project.models.product.Product',
        SHOP_CATEGORIES_CATEGORY_MODEL = 'shop_categories.test_utils.project.models.category.Category'
    ))
    
    testsetup = TestSetup(appname='shop_categories', default_settings=default_settings)
    
    if __name__ == '__main__':
        testsetup.run('tests') # Can be 'tests', 'shell' or 'testserver'