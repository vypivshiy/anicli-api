from setuptools import setup, find_packages
from anicli_api.__version__ import __version__

with open("README.MD", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='anicli-api',
    version=__version__,
    packages=find_packages(),
    url='https://github.com/vypivshiy/anicli_api',
    license='GPL-3',
    author='Georgiy aka Vypivshiy',
    author_email='',
    python_requires='>=3.8',
    description='anime parser API implementation',
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=['httpx', 'bs4'],
)
