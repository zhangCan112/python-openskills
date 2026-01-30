"""
Setup configuration for OpenSkills Python package
"""

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='openskills',
    version='1.0.0',
    author='OpenSkills Contributors',
    author_email='',
    description='Universal skills loader for AI coding agents - Python implementation',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/numman-ali/openskills',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    python_requires='>=3.8',
    install_requires=[
        'click>=8.1.0',
        'questionary>=2.0.0',
    ],
    entry_points={
        'console_scripts': [
            'openskills=openskills.cli:cli',
        ],
    },
)