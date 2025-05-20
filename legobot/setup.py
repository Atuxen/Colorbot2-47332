from setuptools import setup, find_packages


setup(
    name='legobot',
    author='DTU Energy',
    version='1.0',
    description='an awesome module for 47332 course',
    license='MPL-2.0',
    packages=find_packages(),
    python_requires='>=3.9',
    install_requires=[
        'numpy',
        'jupyter',
        'sklearn',
        'pandas',
        'seaborn',
        'scipy',
        'matplotlib',
        'dragonfly-opt',
        'ase',
        'nglview',
        'paramiko',
        'python-ev3dev2',
    ],
    # For including things from the MANIFEST.in
    include_package_data=True,
)
