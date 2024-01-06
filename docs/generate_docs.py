"""Generate automatic documentation"""

import os
import pathlib
import re
import shutil
import subprocess
import sys

import markdown

#Whether to CONVERT_MD using markdown library (True), or let github do it (False)
CONVERT_MD=True
RTD_THEME=False #Not currently working
RELEASE_VERSION= '0.1.59'
RUN_TESTS=False
LINT_IT=False

#Setup relevant paths
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

# Set the package name, SUB_DIRectory, and output directory
SUB_DIR = './sprit'
output_dir = docsDir

venvPath = pathlib.Path(sys.executable).parent.parent

os.environ['PYTHONPATH'] = '..' + os.pathsep + os.environ.get('PYTHONPATH', '')

# Run the pdoc command
if RTD_THEME:
    THEME_PATH = venvPath.as_posix()+'/lib/site-packages/sphinx_RTD_THEME/'
    subprocess.run(['pdoc', '--html', '-o', str(docsDir), '--force', '--template-dir', THEME_PATH, str(spritDir)], check=False)
else:
    subprocess.run(['pdoc', '--html', '-o', str(docsDir), '--force', str(spritDir)],check=False)
    
#Set up a working directory for the files generated from pdoc
workDir = pathlib.Path(os.getcwd())
print('workdir:',workDir)
if workDir.stem == 'docs':
    pass
elif 'docs' in str(workDir):
    pass
else:
    for p in pathlib.Path('.').rglob('*'): 
        if 'docs\\' in str(p):
            docsPath = pathlib.Path(str(p)[:str(p).find('docs')+ 4])
            os.chdir(docsPath)
            break

src_path = spritDir # pathlib.Path(SUB_DIR)
trg_path = docsDir # src_path.parent.joinpath(output_dir) # this is main repo folder, usually

print('Reading .py files from', src_path.absolute())
print('Placing html files in', trg_path.absolute())

# Move items back into the main docs folder
keepList = ['generate_docs.py', 'conf.py', 'requirements.txt', 'wiki', 'pyinstaller']
for t in trg_path.iterdir():
    #print('main folder', t)
    if t.name in keepList:
        # Don't do anything to requirements.txt or wiki folder
        pass
    elif t.is_dir():
        for file in t.iterdir():
            if file.is_dir():
                if file.name == 'resources':
                    for f in file.iterdir():
                        # We don't want the resources folder in docs folder, remove all items
                        os.remove(f)
                elif file.name == 'wiki':
                    # Keep wiki folder
                    pass
                else:
                    for f in file.iterdir():
                        destFilePath = trg_path.joinpath(f.name)
                        if destFilePath.exists():
                            os.remove(destFilePath)
                        f = f.rename(destFilePath)
                        keepList.append(destFilePath.name) #Already deleted and replaced, want to keep it now
                if file.name not in keepList and file.parent.name != 'wiki':
                    os.rmdir(file)
            else:
                destFilePath = trg_path.joinpath(file.name)
                if destFilePath.is_file() and file.name not in keepList and file.parent.name != 'wiki':
                    os.remove(destFilePath)
                file = file.rename(destFilePath)
                keepList.append(destFilePath.name)
                if file.name=='index.html':
                    mainhtmlFPath = file.parent.joinpath('main.html')
                    if mainhtmlFPath.is_file():
                        os.remove(mainhtmlFPath)
                    file.rename(mainhtmlFPath)      
        if t.name not in keepList:
            os.rmdir(t)
    else:
        if t.name not in keepList:
            os.remove(t)

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
    html = html.replace('|','</tr>', 1)
    html = html.replace('|------------|----------------------------|-------------------------------------------------------------------------------------------------|','', 1)

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
    #Copy main readme file into docs so github pages will read it
    shutil.copy(src=str(readmePath.as_posix()), dst='.')

#Update setup file(s) with release version number
setupFPath = repoDir.joinpath('setup.py')
pyprojectFPath = repoDir.joinpath('pyproject.toml')
condaFPath = repoDir.joinpath('conda/meta.yaml')

confFilePaths = [setupFPath, pyprojectFPath, condaFPath]
for cFile in confFilePaths:
    with open(cFile.as_posix(), mode='r', encoding='utf-8') as f:
        cFileText = f.read()


    #Update which file is being analyzed for creating exe
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
        print(f'\nLINTING {fileP.as_posix()}')
        ignoreList = ['E501']
        strIgnoreList =  "--ignore="+str(str(ignoreList)[1:-1].replace(' ', '').replace("'",""))
        result = subprocess.run(['flake8', strIgnoreList, fileP.as_posix(),], 
                                stdout=subprocess.PIPE, check=False)
        print(result.stdout.decode('utf-8'))

if RUN_TESTS:
    print('Testing sprit.run()')
    SHELL_TYPE=True
    if sys.platform == 'linux':
        SHELL_TYPE = False
    try:
        subprocess.run(["python", "-m", "pytest", repoDir.as_posix()], shell=SHELL_TYPE, check=False)
    except Exception:
        subprocess.run(["pytest", repoDir.as_posix()], shell=SHELL_TYPE, check=False)

