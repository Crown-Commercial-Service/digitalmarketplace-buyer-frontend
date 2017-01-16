"""
Common utils for Digital Marketplace apps.
"""

from setuptools import setup, find_packages

setup(
    name='dto-digitalmarketplace-buyer-frontend',
    version='528',
    url='https://github.com/ausdto/dto-digitalmarketplace-buyer-frontend',
    license='MIT',
    author='GDS Developers',
    description='Buyer frontend',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
        'Flask-Login',
        'inflection',
        'newrelic',
        'cffi',
        'Flask-WeasyPrint',
        'pendulum',
        'csvx',
        'xlsxwriter',
        'blinker',
        'rollbar',
        'dto-digitalmarketplace-utils',
        'dto-digitalmarketplace-content-loader',
        'dto-digitalmarketplace-apiclient'
    ]
)
