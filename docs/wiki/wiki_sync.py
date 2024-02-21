import subprocess

upload_wiki=False
download_wiki=False

download_cmd=r"git clone git@github.com:RJbalikian/SPRIT-HVSR.wiki.git"

SHELL_TYPE=True
subprocess.run(download_cmd, shell=SHELL_TYPE, check=False)
