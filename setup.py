from setuptools import setup, find_packages


setup(
    name="sprit",
    author= "Riley Balikian",
    author_email = "balikian@illinois.edu",
    version="0.1.32",
    package_data={'sprit': ['resources/*', 'resources/themes/*', 'resources/themes/forest-dark/*', 'resources/themes/forest-light/*']},
    long_description_content_type="text/html",
    long_description=open("docs/index.html", "r").read(),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'sprit = sprit.sprit_cli:main',
        ]
    }
    )