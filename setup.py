import os
import sys
from setuptools import setup

def read(fname):
	sys.path.insert(0, os.path.dirname(__file__))
	return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(

      name = "vkparser",
      version = "0.1",

      description = """Library for various VK API requests""",
      long_description = read('README.md'),

      author = "Max Kharchenko",
      author_email = "ma.kharchenko@gmail.com",
      install_requires = [
           "pymongo",
           "requests",
      ],

)