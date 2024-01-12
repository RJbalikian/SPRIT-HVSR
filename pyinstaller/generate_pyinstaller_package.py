import os
import pathlib
import shutil
import sys
import re

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, exec_statement, copy_metadata,\
    collect_submodules, get_package_paths, collect_all, collect_entry_point
import os.path

do_package=True
package_type='spec'
onefile=False
pythonfpath = ''

currentDir = pathlib.Path((__file__)).parent
docsDir = currentDir.parent.joinpath('docs/')
repoDir = docsDir.parent

spritDir = repoDir.joinpath('sprit')
spritGUIPath = spritDir.joinpath('sprit_gui.py')
spritPath = spritDir.joinpath('sprit_hvsr.py')
resourcesDir = spritDir.joinpath('resources')
pyinstallerGUI = currentDir.joinpath('sprit_gui_COPY.py')
shutil.copy(spritGUIPath, pyinstallerGUI)
pyinstallerGUI_new = pyinstallerGUI.with_name('sprit_gui_pyinstaller.py')

sys.path.append(str(spritDir))
#import sprit

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

#Update .spec file
specPath = currentDir.joinpath('sprit_gui_pyinstaller.spec')
with open(specPath.as_posix(), 'r',  encoding='utf-8') as f:
    specText = f.read()

#Update which file is being analyzed for creating exe
analysisArgText = r'Analysis\(\[.*?\]'
newAnalysisArgText = r"Analysis(['"+pyinstallerGUI_new.name+"']"
specText = re.sub(analysisArgText, newAnalysisArgText, specText, flags=re.DOTALL)

(_, obspy_root) = get_package_paths('obspy')

reqdatas, reqbinaries, reqhiddenimports = collect_all('requests')
decdatas, decbinaries, dechiddenimports = collect_all('decorator')
sqldatas, sqlbinaries, sqlhiddenimports = collect_all('sqlalchemy')
lxmldatas, lxmlbinaries, lxmlhiddenimports = collect_all('lxml')
mpldatas, mplbinaries, mplhiddenimports = collect_all('matplotlib')
scipydatas, scipybinaries, scipyhiddenimports = collect_all('scipy')
npdatas, npbinaries, nphiddenimports = collect_all('numpy')
cfpdatas, cfbinaries, cfhiddenimports = collect_all('certifi')
urldatas, urlbinaries, urlhiddenimports = collect_all('urllib3')
idnadatas, idnabinaries, idnahiddenimports = collect_all('idna')
cndatas, cnbinaries, cnhiddenimports = collect_all('chardet')
gldatas, glbinaries, glhiddenimports = collect_all('greenlet')
tedatas, tebinaries, tehiddenimports = collect_all('typing-extensions')

spritdatas, sprithiddenimports = collect_entry_point("sprit")
obspydatas, obspyhiddenimports = collect_entry_point("obspy")
tedatas1, tehiddenimports1 = collect_entry_point("typing-extensions")

updateddatas = [reqdatas, decdatas, sqldatas, lxmldatas,mpldatas,scipydatas,
                npdatas,cfpdatas,urldatas,idnadatas,cndatas, gldatas, tedatas,tedatas1,
                spritdatas, obspydatas]
updatebinaries = [reqbinaries, decbinaries, sqlbinaries, lxmlbinaries, mplbinaries,
                scipybinaries, npbinaries,cfbinaries,urlbinaries,idnabinaries,cnbinaries,
                glbinaries, tebinaries]
updatehidimps = [reqhiddenimports,dechiddenimports,sqlhiddenimports,lxmlhiddenimports,
               mplhiddenimports,scipyhiddenimports,nphiddenimports,cfhiddenimports,
               urlhiddenimports,idnabinaries,cnhiddenimports,glhiddenimports,
               tehiddenimports,['typing_extensions', 'typing-extensions'],tehiddenimports1,
               sprithiddenimports, obspyhiddenimports]

binaries = collect_dynamic_libs('obspy')

for d in updatebinaries:
    binaries.extend(d)

#Update which files are being included as binaries
binText = r'binaries=\[.*?\]'
newbinText = r"binaries={}".format(binaries)
specText = re.sub(binText, newbinText, specText, flags=re.DOTALL)

(_, PIL_root) = get_package_paths('PIL')

datas = [
    # Dummy path, this needs to exist for obspy.core.util.libnames._load_cdll
    (os.path.join(PIL_root), os.path.join('PIL')),
    (os.path.join(obspy_root), os.path.join('obspy')),
    #(os.path.join(obspy_root, "core", "util"), os.path.join('obspy', 'core', 'util')),
    #(os.path.join(obspy_root, "lib"), os.path.join('obspy', 'lib')),
    # Data
    #(os.path.join(obspy_root, "imaging"), os.path.join('obspy', 'imaging')),
    #(os.path.join(obspy_root, "imaging", "data"), os.path.join('obspy', 'imaging', 'data')),
    #(os.path.join(obspy_root, "taup", "data"), os.path.join('obspy', 'taup', 'data')),
    #(os.path.join(obspy_root, "geodetics", "data"), os.path.join('obspy', 'geodetics', 'data')),
]

for d in updateddatas:
    datas.extend(d)

# Plugins are defined in the metadata (.egg-info) directory, but if we grab the whole thing it causes
# other errors, so include only entry_points.txt
metadata = copy_metadata('obspy')
#egg = metadata[0]
#if '.egg' not in egg[0]:
#    raise Exception("Unexpected metadata: %s" % (metadata,))
# Specify the source as just the entry points file
#metadata = [(os.path.join(egg[0], 'entry_points.txt'), egg[1])]
datas += metadata
datas += [(resourcesDir.as_posix(), 'resources')]

#def replace_resources_with_data(text):
#    pattern = r'(pkg_resources\.resource_filename\(__name__,\s*)(.*)(\))'
#    return re.sub(pattern, lambda match: match.group(1) + match.group(2).replace('resources', 'data') + match.group(3), text)
#pyinstallerGUI_text = replace_resources_with_data(pyinstallerGUI_text)

#Update which files are being included as data
datasText = r'datas=\[.*?\]'
newDatasText = r"datas={}".format(datas)
specText = re.sub(datasText, newDatasText, specText, flags=re.DOTALL)

# Thse are the actual plugin packages
#Update which files are being included as data
hiddenimports = collect_submodules('obspy.io')
hiddenimports.extend(['PIL.ImageTk', 'PIL.ImageTk._imagingtk'])

for d in updatehidimps:
    hiddenimports.extend(d)

hiddenimportsText = r'hiddenimports=\[.*?\]'
newhiddenimportsText = r"hiddenimports={}".format(hiddenimports)
specText = re.sub(hiddenimportsText, newhiddenimportsText, specText, flags=re.DOTALL)


rthooks = [os.path.join('rthook-obspy.py')]
runtimeHooksText = r'runtime_hooks=\[.*?\]'
newruntimeHooksText = r"runtime_hooks={}".format(rthooks)
specText = re.sub(runtimeHooksText, newruntimeHooksText, specText, flags=re.DOTALL)

nameText = r'name=\'.*?\''
newnameText = r"name='{}'".format('SpRIT')
specText = re.sub(nameText, newnameText, specText, flags=re.DOTALL)


#WRITE FILES
#Write spec file
print('Writing Spec file')
with open(specPath.as_posix(), 'w') as fout:
    fout.write(specText)

#Write py file
with open(pyinstallerGUI_new.as_posix(), 'w') as f:
    f.write(pyinstallerGUI_text)

if do_package:

    if package_type=='file':
        scriptPath = pyinstallerGUI_new.as_posix()
        if onefile:
            addl_cmds = ['--onefile']
        else:
            addl_cmds = []
        addl_cmds.extend(['--windowed', '--specpath', currentDir.as_posix(),'--name', 'SPRIT',])


    else:
        scriptPath = specPath.as_posix()
        addl_cmds = []

    addl_cmds.extend(['--distpath',currentDir.joinpath('dist').as_posix(),
                    '--workpath', currentDir.as_posix(),
                    '-y', '--clean'])

    base_command = [scriptPath]
    base_command.extend(addl_cmds)

    
    cmd = base_command + addl_cmds
    print(cmd)
    import PyInstaller.__main__
    PyInstaller.__main__.run(cmd)

