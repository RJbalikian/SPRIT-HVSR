from setuptools import setup

setup(
    name="sprit",
    version="0.0.3",
    install_requires=["obspy", "scipy", "matplotlib", "pandas", "numpy","ipykernel", "pyqt5", "tkcalendar"],
    description="A package for processing and analyzing HVSR (Horizontal to Vertical Spectral Ratio) data",
    )
