from setuptools import setup, find_packages

setup(
    name='watchcmd',
    version='1.0',
    packages=find_packages(),
    author='Mateusz Kadula',
    include_package_data=True,
    description='Command line application for managing watch accuracy measurements',
    entry_points={
        'console_scripts': [
            'watches=watch:commands.main',
        ],
    },
    install_requires=[
        'requests',
        'pydantic',
        'prompt_toolkit',
        'tabulate'
    ],
    dependency_links=[
        'file://../communication#egg=communication'
    ]
)
