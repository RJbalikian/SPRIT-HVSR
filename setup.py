from setuptools import setup, find_packages


setup(
    name="sprit",
    author= "Riley Balikian",
    author_email = "balikian@illinois.edu",
    version="0.1.31",
    install_requires=["obspy", "scipy", "matplotlib", "pandas", "numpy", "pyqt5", "pyproj"],
    description="A package for processing and analyzing HVSR (Horizontal to Vertical Spectral Ratio) data",
    package_data={'sprit': ['resources/*', 'resources/themes/*', 'resources/themes/forest-dark/*', 'resources/themes/forest-light/*']},
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sprit = sprit.sprit_cli:main',
        ]
    }
    )