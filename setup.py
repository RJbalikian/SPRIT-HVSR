from setuptools import setup, find_packages
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="sprit",
    author= "Riley Balikian",
    author_email = "balikian@illinois.edu",
    version="3.0.1",
    package_data={'sprit': ['resources/*', 'resources/icon/*', 'resources/themes/*', 'resources/themes/forest-dark/*', 
                            'resources/themes/forest-light/*', 'resources/sample_data/*','resources/settings/*']},
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    python_requires='>=3.9',
    entry_points={
        'console_scripts': [
            'sprit = sprit.sprit_cli:main',
        ]        
        }
    )