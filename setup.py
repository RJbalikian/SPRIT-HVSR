from setuptools import setup

setup(
    name="sprit",
    author= "Riley Balikian",
    author_email = "balikian@illinois.edu",
    version="0.1.1",
    install_requires=["obspy", "scipy", "matplotlib", "pandas", "numpy", "pyqt5", "tkcalendar"],
    description="A package for processing and analyzing HVSR (Horizontal to Vertical Spectral Ratio) data",
    package_data={'sprit': ['resources/*']}
    )
