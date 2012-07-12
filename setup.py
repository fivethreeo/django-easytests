from setuptools import setup, find_packages
import os

import djeasytests

CLASSIFIERS = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
]

setup(
    name='django-easytests',
    version=djeasytests.get_version(),
    description='Slightly modified test utils from django-cms as a own module',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Oyvind Saltvik',
    author_email='oyvind.saltvik@gmail.com',
    url='http://github.com/fivethreeo/django-easytests/',
    packages=find_packages(),
    classifiers=CLASSIFIERS,
    include_package_data=True,
    zip_safe=False,
    install_requires=['Django>=1.3', 'argparse', 'unittest-xml-reporting']
)
