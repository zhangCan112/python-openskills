from setuptools import setup, find_packages

setup(
    name='openskills',
    version='2.0.0',
    python_requires='>=3.11',
    packages=find_packages(),
    package_data={
        'openskills': ['data/marketskills/market_index.json'],
    },
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
