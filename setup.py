from setuptools import setup

setup(name='github_enterprise',
      version='0.2.0',
      packages=['github_enterprise'],
      url='https://github.com/peak6/github_enterprise',
      description='Python API for Github Enterprise site admin',
      author='Cody A. Ray',
      author_email='cray@peak6.com',
      install_requires=[
          'selenium>=3.0',
          'pyvirtualdisplay>=0.2'
      ])
