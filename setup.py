from setuptools import setup

setup(
    name="SPRĪT HVSR",
    version="0.0.2",
    install_requires=["obspy", "scipy", "matplotlib", "pandas", "numpy"],
    extras_require={'optional':["ipykernel", "pyqt5", "tkcalendar"]},
    description="A package for processing and analyzing HVSR (Horizontal to Vertical Spectral Ratio) data",
    author="Riley Balikian",
    author_email="balikian@illinois.edu",
    url=["https://github.com/RJbalikian/SPRIT", "https://rjbalikian.github.io/SPRIT/main.html"],
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Geophysics",
        ]
    )
