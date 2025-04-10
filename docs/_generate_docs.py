"""Generate automatic documentation"""

import os
import pathlib
import re
import shutil
import subprocess
import sys

import markdown

RELEASE_VERSION = "2.3.7"

VERBOSE = True

# Whether to CONVERT_MD using markdown (True), or github (False)
RTD_DOCS = True
GITHUB_PAGES = True  # Don't think I  need this anymore, and it still works

CONVERT_MD = True
RTD_THEME = False  # Not currently working, for github pages

RUN_TESTS = False
LINT_IT = False

if VERBOSE:
    print('Specifying filepaths')

# Setup relevant paths
currentDir = pathlib.Path((__file__)).parent
docsDir = currentDir
repoDir = docsDir.parent
spritDir = repoDir.joinpath('sprit')
spritGUIPath = spritDir.joinpath('sprit_gui.py')
spritUtilsPath = spritDir.joinpath('sprit_utils.py')
spritCLIPath = spritDir.joinpath('sprit_cli.py')
spritHVSRPath = spritDir.joinpath('sprit_hvsr.py')
resourcesDir = spritDir.joinpath('resources')
pyinstallerGUI = currentDir.joinpath('sprit_gui_COPY.py')

# Update setup file(s) with release version number
setupFPath = repoDir.joinpath('setup.py')
pyprojectFPath = repoDir.joinpath('pyproject.toml')
confFPath = docsDir.joinpath('conf.py')
condaFPath = repoDir.joinpath('conda/meta.yaml')
initFPath = spritDir.joinpath('__init__.py')
requirePath = docsDir.joinpath('requirements.txt')

# Set the package name, SUB_DIRectory, and output directory
venvPath = pathlib.Path(sys.executable).parent.parent

os.environ['PYTHONPATH'] = '..' + os.pathsep + os.environ.get('PYTHONPATH', '')

if VERBOSE:
    print('Updating version/release numbers')
confFilePaths = [setupFPath, pyprojectFPath, condaFPath,
                 confFPath, initFPath, requirePath]

for cFile in confFilePaths:
    if cFile.exists():
        with open(cFile.as_posix(), mode='r', encoding='utf-8') as f:
            cFileText = f.read()

        # Update which file is being analyzed for version number
        # Intended for setup.py
        VERTEXT = r'version=".*?"'
        NEWVERTEXT = r'version="'+RELEASE_VERSION+'"'
        cFileText = re.sub(VERTEXT, NEWVERTEXT, cFileText, flags=re.DOTALL)

        # intended for pyproject.toml
        VERTEXT = r'version:\s+\d+\.\d+\.\d+[^\n]*'
        NEWVERTEXT = r'version: '+RELEASE_VERSION
        cFileText = re.sub(VERTEXT, NEWVERTEXT, cFileText, flags=re.DOTALL)

        # intended for conda/meta.yaml, if used
        VERTEXT = r'git_tag:\s+v+\d+\.\d+\.\d+[^\n]*'
        NEWVERTEXT = r'git_tag: v'+RELEASE_VERSION
        cFileText = re.sub(VERTEXT, NEWVERTEXT, cFileText, flags=re.DOTALL)

        # intended for conf.py
        VERTEXT = r"release = '.*?'"
        NEWVERTEXT = r"release = '"+RELEASE_VERSION+"'"
        cFileText = re.sub(VERTEXT, NEWVERTEXT, cFileText, flags=re.DOTALL)

        # intended for __init__.py
        VERTEXT = r'__version__ = ".*?"'
        NEWVERTEXT = r'__version__ = "'+RELEASE_VERSION+'"'
        cFileText = re.sub(VERTEXT, NEWVERTEXT, cFileText, flags=re.DOTALL)

        # intended for requirements.txt
        VERTEXT = r"sprit==.*?[^\n]*"
        if 'dev' in RELEASE_VERSION:
            REL_VER = RELEASE_VERSION.replace('-', '.')+'0'
        else:
            REL_VER = RELEASE_VERSION
        NEWVERTEXT = r'sprit==' + REL_VER
        cFileText = re.sub(VERTEXT, NEWVERTEXT, cFileText, flags=re.DOTALL)

        cFileText = re.sub(VERTEXT, NEWVERTEXT, cFileText, flags=re.DOTALL)


        with open(cFile.as_posix(), mode='w', encoding='utf-8') as f:
            f.write(cFileText)

venvPath = pathlib.Path(sys.executable).parent.parent
os.environ['PYTHONPATH'] = '..' + os.pathsep + os.environ.get('PYTHONPATH', '')

if RTD_DOCS:
    if VERBOSE:
        print('Creating Read the Docs files')
    keepList = ['_generate_docs', 'conf', 'requirements', 'wiki']

    if VERBOSE:
        print('Saving conf.py and index.rst so they do not get overwritten')
    # It seems apidoc rewrites conf.py and index.rst file (don't want that),
    # so save it first and rewrite after
    confFilePath = docsDir.joinpath('conf.py')
    indFilePath = docsDir.joinpath('index.rst')

    with open(confFilePath.as_posix(), mode='r', encoding='utf-8') as f:
        confFileText = f.read()
    with open(indFilePath.as_posix(), mode='r', encoding='utf-8') as f:
        indFileText = f.read()

    if VERBOSE:
        print('Running sphinx-apidoc')
    # Run apidoc to update api documentation from docstrings
    subprocess.run(['sphinx-apidoc', '-F', '-M', '-e', '-f', 
                    '-o',docsDir.as_posix(), spritDir.as_posix(),
                    '-H', 'SpRIT HVSR'],
                   check=False)

    if VERBOSE:
        print('sphinx-apidoc complete')
        print('Putting original conf.py and index.rst files back')
    with open(confFilePath.as_posix(), mode='w', encoding='utf-8') as f:
        f.write(confFileText)
    with open(indFilePath.as_posix(), mode='w', encoding='utf-8') as f:
        f.write(indFileText)

    if VERBOSE:
        print('Cleaning make file and sources')
    subprocess.run([docsDir.joinpath('make.bat').as_posix(), 'clean'],
                   check=False)
    if VERBOSE:
        print('Creating make file (for html)')
    subprocess.run([docsDir.joinpath('make.bat').as_posix(), 'html'],
                   check=False)

    if VERBOSE:
        print('Organizing documentation files')
    buildDir = docsDir.joinpath('_build')
    htmlDir = buildDir.joinpath('html')

    copyList = ['documentation_options', 'doctools',
                'sphinx_highlight', 'theme', 'pygments']

    if not htmlDir.exists():
        os.mkdir(htmlDir)
    
    for f in htmlDir.iterdir():
        if f.name[0] != '_':
            shutil.copy(f, docsDir.joinpath(f.name))
        else:
            if f.name == '_static':
                for f2 in f.iterdir():
                    if f2.stem in copyList:
                        shutil.copy(f2, docsDir.joinpath(f.name))
                    elif f2.stem == 'js':
                        shutil.copy(f2.joinpath('theme.js'),
                                    docsDir.joinpath('theme.js'))
                    elif f2.stem == 'css':
                        shutil.copy(f2.joinpath('theme.css'),
                                    docsDir.joinpath('theme.css'))

    for file in docsDir.iterdir():
        if file.suffix == '.html':
            with open(file.as_posix(), mode='r', encoding='utf-8') as f:
                htmlFileText = f.read()
            htmlFileText = htmlFileText.replace('src="_static/', 'src="')
            htmlFileText = htmlFileText.replace('src="js/', 'src="')

            htmlFileText = htmlFileText.replace('href="_static/', 'href="')
            htmlFileText = htmlFileText.replace('href="css/', 'href="')
            with open(file.as_posix(), mode='w', encoding='utf-8') as f:
                f.write(htmlFileText)

if GITHUB_PAGES:
    # Run the pdoc command
    if RTD_THEME:
        THEME_PATH = venvPath.as_posix()+'/lib/site-packages/sphinx_RTD_THEME/'
        subprocess.run(['pdoc', '--html', '-o', str(docsDir),
                        '--force', '--template-dir', THEME_PATH, str(spritDir)], check=False)
    else:
        subprocess.run(['pdoc', '--html', '-o', str(docsDir),
                        '--force', str(spritDir)], check=False)

    # Set up a working directory for the files generated from pdoc
    workDir = pathlib.Path(os.getcwd())
    print('workdir:', workDir)
    if workDir.stem == 'docs':
        pass
    elif 'docs' in str(workDir):
        pass
    else:
        for p in pathlib.Path('.').rglob('*'):
            if 'docs\\' in str(p):
                docsPath = pathlib.Path(str(p)[:str(p).find('docs') + 4])
                os.chdir(docsPath)
                break

    src_path = spritDir  # pathlib.Path(SUB_DIR)
    trg_path = docsDir   # 

    print('Reading .py files from', src_path.absolute())
    print('Placing html files in', trg_path.absolute())

    # Move items back into the main docs folder
    keepList = ['_generate_docs.py', 'conf.py', 'requirements.txt',
                'wiki', 'pyinstaller', '.readthedocs.yaml', 'index.rst']
    
    for t in trg_path.iterdir():

        if t.name in keepList:
            # Don't do anything to requirements.txt or wiki folder
            pass
        elif t.is_dir():
            for file in t.iterdir():
                if file.is_dir():
                    if file.name == 'resources':
                        for f in file.iterdir():
                            # Don't want resources dir in docs dir, remove
                            os.remove(f)
                    elif file.name == 'wiki':
                        # Keep wiki folder
                        pass
                    else:
                        for f in file.iterdir():
                            destFilePath = trg_path.joinpath(f.name)
                            if destFilePath.exists() and destFilePath.is_file():
                                os.remove(destFilePath)
                            try:
                                f = f.rename(destFilePath)
                            except:
                                pass
                            keepList.append(destFilePath.name)  # Already deleted and replaced, want to keep it now
                    if file.name not in keepList and file.parent.name != 'wiki':
                        if file.is_dir() and file.exists():
                            try:
                                os.rmdir(file)
                            except:
                                pass

                else:
                    destFilePath = trg_path.joinpath(file.name)
                    if destFilePath.is_file() and file.name not in keepList and file.parent.name != 'wiki':
                        os.remove(destFilePath)
                    file = file.rename(destFilePath)
                    keepList.append(destFilePath.name)
                    if file.name == 'index.html':
                        mainhtmlFPath = file.parent.joinpath('main.html')
                        if mainhtmlFPath.is_file():
                            os.remove(mainhtmlFPath)
                        file.rename(mainhtmlFPath)
            if t.name not in keepList:
                try:
                    os.rmdir(t)
                except:
                    pass
        else:
            if t.name not in keepList:
                try:
                    os.remove(t)
                except:
                    pass

    # Update html files
    readmePath = repoDir.joinpath('README.md')
    print("Using Readme for landing page")
    if CONVERT_MD:

        with open(readmePath.as_posix(), mode='r', encoding='utf-8') as f:
            markdown_text = f.read()

        html = markdown.markdown(markdown_text)

        html = html.replace('| Dependency', '<table>\n\t<tr>\n\t<th>Dependency</th>\n', 1)
        html = html.replace('| Link', '\t\t<th>Link</th>\n', 1)
        html = html.replace('| Description', '\t\t<th>Description</th>\n', 1)
        html = html.replace('|', '</tr>', 1)
        html = html.replace('|------------|----------------------------|-------------------------------------------------------------------------------------------------|', '', 1)

        html = html.replace('|', '\t<tr>\n\t\t<td>', 1)
        html = html.replace('|', '\t</td>\n\t\t<td>', 2)
        html = html.replace('|', '\t</td>\n\t</tr>', 1)

        html = html.replace('|', '\t<tr>\n\t\t<td>', 1)
        html = html.replace('|', '\t</td>\n\t\t<td>', 2)
        html = html.replace('|', '\t</td>\n\t</tr>', 1)

        html = html.replace('|', '\t<tr>\n\t\t<td>', 1)
        html = html.replace('|', '\t</td>\n\t\t<td>', 2)
        html = html.replace('|', '\t</td>\n\t</tr>', 1)

        html = html.replace('|', '\t<tr>\n\t\t<td>', 1)
        html = html.replace('|', '\t</td>\n\t\t<td>', 2)
        html = html.replace('|', '\t</td>\n\t</tr>', 1)

        html = html.replace('|', '\t<tr>\n\t\t<td>', 1)
        html = html.replace('|', '\t</td>\n\t\t<td>', 2)
        html = html.replace('|', '\t</td>\n\t</tr>\n</table>', 1)
        html = html.replace('</table></p>', '</table>', 1)

        dst = docsDir.joinpath('index.html')
        with open(dst, mode='w', encoding='utf-8') as f:
            f.write(html)
        print('hmtl landing page:', dst)
    else:
        # Copy main readme file into docs so github pages will read it
        shutil.copy(src=str(readmePath.as_posix()), dst='.')

    # Update setup file(s) with release version number
    setupFPath = repoDir.joinpath('setup.py')
    pyprojectFPath = repoDir.joinpath('pyproject.toml')
    condaFPath = repoDir.joinpath('conda/meta.yaml')

    confFilePaths = [setupFPath, pyprojectFPath, condaFPath]
    for cFile in confFilePaths:
        with open(cFile.as_posix(), mode='r', encoding='utf-8') as f:
            cFileText = f.read()

        # Update which file is being analyzed for creating exe
        VER_TEXT = r'version=".*?"'
        NEW_VER_TEXT = r'version="'+RELEASE_VERSION+'"'
        cFileText = re.sub(VER_TEXT, NEW_VER_TEXT, cFileText, flags=re.DOTALL)

        VER_TEXT = r'version:\s+\d+\.\d+\.\d+[^\n]*'
        NEW_VER_TEXT = r'version: '+RELEASE_VERSION
        cFileText = re.sub(VER_TEXT, NEW_VER_TEXT, cFileText, flags=re.DOTALL)

        VER_TEXT = r'git_tag:\s+v+\d+\.\d+\.\d+[^\n]*'
        NEW_VER_TEXT = r'git_tag: v'+RELEASE_VERSION
        cFileText = re.sub(VER_TEXT, NEW_VER_TEXT, cFileText, flags=re.DOTALL)

        with open(cFile.as_posix(), mode='w', encoding='utf-8') as f:
            f.write(cFileText)

if LINT_IT:
    print('Running linting')
    fileList = [spritGUIPath, spritCLIPath, spritUtilsPath, spritHVSRPath]
    for fileP in fileList:
        print(fileP)
        print(f'\nLINTING {fileP.as_posix()}')
        ignoreList = ['E501']
        STR_IGNORE_LIST = "--ignore=" + str(str(ignoreList)[1:-1].replace(' ', '').replace("'", ""))
        result = subprocess.run(['flake8', STR_IGNORE_LIST, fileP.as_posix(),],
                                stdout=subprocess.PIPE, check=False)
        print(result.stdout.decode('utf-8'))

if RUN_TESTS:
    print('Testing sprit.run()')
    SHELL_TYPE = True
    if sys.platform == 'linux':
        SHELL_TYPE = False
    try:
        subprocess.run(["python", "-m", "pytest", repoDir.as_posix()], shell=SHELL_TYPE, check=False)
    except Exception:
        subprocess.run(["pytest", repoDir.as_posix()], shell=SHELL_TYPE, check=False)
