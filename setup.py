#!/usr/bin/env python

from distutils.core import setup

setup(name='get_exp_group_id',
      version='1.0',
      description='Python tools for getting exposure group ids from star files',
      author='Dustin Morando with edits by Hamish Brown',
      author_email='hgbrown@unimelb.edu.au',
      url='https://github.com/HamishGBrown/EPU_group_AFIS',
      install_requires=['numpy',  'tqdm', 'scikit-learn', 'matplotlib'],
      scripts=['get_exp_id_from_star.py','EPU_Group_AFIS.py'])
