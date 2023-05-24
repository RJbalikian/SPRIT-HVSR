import os
import pathlib
import shutil
import subprocess
import sys

#Whether to convert_md using markdown library (True), or let github do it (False)
convert_md=True
rtd_theme=False #Not currently working

# Set the package name, subdirectory, and output directory
subdir = '.\sprit'
output_dir = 'docs'

venvPath = pathlib.Path(sys.executable).parent.parent

os.environ['PYTHONPATH'] = '..' + os.pathsep + os.environ.get('PYTHONPATH', '')

# Run the pdoc command
if rtd_theme:
    themePath = venvPath.as_posix()+'/lib/site-packages/sphinx_rtd_theme/'
    subprocess.run(['pdoc', '--html', '-o', output_dir, '--force', '--template-dir', themePath, subdir])
else:
    subprocess.run(['pdoc', '--html', '-o', output_dir, '--force', subdir ])

workDir = pathlib.Path(os.getcwd())
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

src_path = pathlib.Path(subdir)
trg_path = src_path.parent # this ends up being current folder, usually

keepList = ['generate_docs.py', 'conf.py', 'requirements.txt', 'wiki']
for t in trg_path.iterdir():
    #print('main folder', t)
    if t.name in keepList:
        pass
    elif t.is_dir():
        for file in t.iterdir():
            #print('second layer', file)
            if file.is_dir():
                if file.name == 'resources':
                    for f in file.iterdir():
                        os.remove(f)
                elif file.name == 'wiki':
                    pass
                else:
                    #print('file', file.name)
                    for f in file.iterdir():
                        destFilePath = trg_path.joinpath(f.name)
                        print(destFilePath)
                        if destFilePath.exists():
                            os.remove(destFilePath)
                        f = f.rename(destFilePath)
                if file.name not in keepList and file.parent.name != 'wiki':
                    os.rmdir(file)
            else:
                destFilePath = trg_path.joinpath(file.name)
                if destFilePath.is_file() and file.name not in keepList and file.parent.name != 'wiki':
                    os.remove(destFilePath)
                file = file.rename(destFilePath)
                if file.name=='index.html':
                    mainhtmlFPath = file.parent.parent.joinpath('main.html')
                    if mainhtmlFPath.is_file():
                        os.remove(mainhtmlFPath)
                    file.rename(mainhtmlFPath)      
        if file.name not in keepList:
            os.rmdir(t)
    else:
        if t.name not in keepList:
            os.remove(t)

#os.rmdir(subdir)

repo_path = pathlib.Path('..')
for each_file in repo_path.iterdir():
    if each_file.name == 'README.md':
        if convert_md:
            import markdown

            with open(each_file, 'r') as f:
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


            dst = pathlib.Path('index.html')
            with open(dst, 'w') as f:
                f.write(html)
            print(dst)
            break
        else:
            #Copy main readme file into docs so github pages will read it
            shutil.copy(src=str(each_file), dst='.')
            break