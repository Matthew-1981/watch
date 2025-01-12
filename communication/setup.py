from setuptools import setup, find_packages

setup(
    name='communication',
    version='1.0.0',
    packages=find_packages(),
    install_requires=[
        'pydantic>=2.10.5',
    ],
    include_package_data=True,
    description='A set of Pydantic models for the purpose of communication between the watch backend and frontend',
    author='Mateusz Kadula',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.10',
)
