"""
Setup configuration for OpenSkills Python package
"""

from setuptools import setup, find_packages

setup(
    name='openskills',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'click>=8.1.0',
        'questionary>=2.0.0',
        'PyYAML>=6.0',
    ],
    entry_points={
        'console_scripts': [
            'openskills=openskills.cli:cli',
        ],
    },
)
