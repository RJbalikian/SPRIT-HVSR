import os
import pathlib
import shutil
import stat
import subprocess

currentDir = pathlib.Path((__file__)).parent
download_wiki=True

def onerror(func, path, exc_info):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)  # Make the file writable
        func(path)
    else:
        assert False

if download_wiki:
    dir_path = currentDir.joinpath('SPRIT-HVSR_Wiki')

    if dir_path.exists():
        try:
            shutil.rmtree(dir_path.as_posix(), onerror=onerror)
            print(f"Directory '{dir_path}' and its contents have been removed.")
        except OSError as e:
            print(f"Error: {e.strerror}")    
    download_path = currentDir.as_posix()
    download_cmd=f"git -C {download_path} clone git@github.com:RJbalikian/SPRIT-HVSR.wiki.git"
    SHELL_TYPE=True
    subprocess.run(download_cmd, shell=SHELL_TYPE, check=False)
