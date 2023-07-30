import os
import pathlib
import shutil
import sys
import re

do_package=False
package_type='file'

currentDir = pathlib.Path((__file__)).parent
docsDir = currentDir.parent
repoDir = docsDir.parent
spritDir = repoDir.joinpath('sprit')
spritGUIPath = spritDir.joinpath('sprit_gui.py')
spritPath = spritDir.joinpath('sprit.py')
pyinstallerGUI = currentDir.joinpath('sprit_gui_COPY.py')
shutil.copy(spritGUIPath, pyinstallerGUI)
pyinstallerGUI_new = pyinstallerGUI.with_name('sprit_gui_pyinstaller.py')

sys.path.append(str(spritDir))
import sprit
print(sprit.check_mark())

with open(str(pyinstallerGUI), 'r') as f:
    pyinstallerGUI_text = f.read()

#UPDATE TEXT
#Update gui .py file
#Change intro text
introText = "graphical user interface"
newIntroText = "pyinstaller app"
pyinstallerGUI_text = pyinstallerGUI_text.replace(introText, newIntroText)

#Now, the real changes needed for pyinstaller to work


#Update .spec file
specPath = currentDir.joinpath('sprit_gui_pyinstaller.spec')
with open(str(specPath), 'r',  encoding='utf-8') as f:
    specText = f.read()

#THIS NEEDS TO BE FIXED!!
analysisText = r'Analysis\(\[.*?\]'
newAnalysisText = r"Analysis(['"+specPath.as_posix()+"']"
specText = re.sub(analysisText, newAnalysisText, specText, flags=re.DOTALL)

#WRITE FILES
#Write spec file
with open(str(specPath)) as f:
    f.write(specText)

#Write py file
with open(str(pyinstallerGUI_new), 'w') as f:
    f.write(pyinstallerGUI_text)

if do_package:
    if package_type=='spec':
        pass
    elif package_type=='file':
        import PyInstaller.__main__
        PyInstaller.__main__.run([
            str(pyinstallerGUI_new),
            '--onefile',
            '--windowed',
            '--distpath',
            str(currentDir),
            '--workpath',
            str(currentDir),
            '-y',
            '--clean',
            '--specpath',
            str(currentDir),
            ])
    else:
        print('What is your package_type?')
