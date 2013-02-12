from distutils.core import setup

setup(
    name='TrelloCardUpdate',
    version='0.0.0',
    author='Thomas Ballinger',
    author_email='tom@hackerschool.com',
    packages=['trellocardupdate', 'trellocardupdate.test'],
    scripts=['bin/tu.py', 'bin/tu'],
    license='LICENSE.txt',
    description='basic command line trello client',
    long_description=open('README.txt').read(),
)


