#!/usr/bin/env python

from distutils.core import setup

setup(name='obs4MIPS',
      version='1.0',
      description='Convert observation data to CMIP5s',
      author='Denis Nadeau',
      author_email='denis.nadeau@nasa.gov',
      url='http://nccs.nasa.gov',
      py_modules=['obs4MIPs_process'],
      packages=['','factory', 'Toolbox'],
      package_data={'': ['Tables/*']},
      install_requires=[
      "cmor >= 2.8",
      "cdms >= 1.0",
      "cdtime >= 3.2"
      "numpy >= 1.5.1",
      ],
     )
