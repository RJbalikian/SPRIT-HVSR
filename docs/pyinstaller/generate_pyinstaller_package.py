import os
import pathlib
import shutil
import sys
import re

do_package=True
package_type='spec'

currentDir = pathlib.Path((__file__)).parent
docsDir = currentDir.parent
repoDir = docsDir.parent
spritDir = repoDir.joinpath('sprit')
spritGUIPath = spritDir.joinpath('sprit_gui.py')
spritPath = spritDir.joinpath('sprit.py')
resourcesDir = spritDir.joinpath('resources')
pyinstallerGUI = currentDir.joinpath('sprit_gui_COPY.py')
shutil.copy(spritGUIPath, pyinstallerGUI)
pyinstallerGUI_new = pyinstallerGUI.with_name('sprit_gui_pyinstaller.py')

sys.path.append(str(spritDir))
import sprit

with open(str(pyinstallerGUI), 'r') as f:
    pyinstallerGUI_text = f.read()

#UPDATE TEXT
#Update gui .py file
#Change intro text
introText = "graphical user interface"
newIntroText = "pyinstaller app"
pyinstallerGUI_text = pyinstallerGUI_text.replace(introText, newIntroText)

#resourcePathText = r'pkg_resources.resource_filename\(\[.*?\]'
#newresourcePathText = r"Analysis(['"+pyinstallerGUI_new.name+"']"
#pyinstallerGUI_text = re.sub(resourcePathText, resourcePathText, pyinstallerGUI_text, flags=re.DOTALL)

def replace_resources_with_data(text):
    pattern = r'(pkg_resources\.resource_filename\(__name__,\s*)(.*)(\))'
    return re.sub(pattern, lambda match: match.group(1) + match.group(2).replace('resources', 'data') + match.group(3), text)

pyinstallerGUI_text = replace_resources_with_data(pyinstallerGUI_text)

#Update .spec file
specPath = currentDir.joinpath('sprit_gui_pyinstaller.spec')
with open(specPath.as_posix(), 'r',  encoding='utf-8') as f:
    specText = f.read()

#Update which file is being analyzed for creating exe
analysisArgText = r'Analysis\(\[.*?\]'
newAnalysisArgText = r"Analysis(['"+pyinstallerGUI_new.name+"']"
specText = re.sub(analysisArgText, newAnalysisArgText, specText, flags=re.DOTALL)

#Update which files are being included as data
datasText = r'datas=\[.*?\]'
newDatasText = r"datas=[('{}', '{}')]".format(resourcesDir.as_posix(), 'data')
specText = re.sub(datasText, newDatasText, specText, flags=re.DOTALL)

print(specText)
#WRITE FILES
#Write spec file
with open(specPath.as_posix(), 'w') as fout:
    fout.write(specText)

#Write py file
with open(pyinstallerGUI_new.as_posix(), 'w') as f:
    f.write(pyinstallerGUI_text)

if do_package:

    if package_type=='file':
        scriptPath = pyinstallerGUI_new.as_posix()
        addl_cmds = ['--onefile', '--windowed', '--specpath',currentDir.as_posix()]
    else:
        scriptPath = specPath.as_posix()
        addl_cmds = []
        scriptPath = specPath.as_posix()
    
    base_command = [scriptPath,
        '--distpath',
        currentDir.as_posix(),
        '--workpath',
        currentDir.as_posix(),
        '-y',
        '--clean']
    
    cmd = base_command + addl_cmds

    import PyInstaller.__main__
    PyInstaller.__main__.run(cmd)

