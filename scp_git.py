#!python

# cat ~/.ssh/id_rsa.pub | ssh user@hostname 'cat >> .ssh/authorized_keys'

from os import system, path
import sys

desthost = sys.argv[1]
passwd = raw_input('Password: ')

gitfiles = []

dirmap = {'sourcedir1': '/dest/dir1', 'sourcedir2': '/dest/dir2'}

system('git status >/tmp/.git_status')

lines = open('/tmp/.git_status').readlines()

gitfiles = []

for line in lines:
    if 'new file:' in line or 'modified:' in line:
        gitfiles.append(line.strip().split(':')[1].strip())

for sourcefile in gitfiles:
    for source in dirmap.keys():
        if sourcefile.startswith(source):
            destf = sourcefile.replace(source, dirmap[source])
            sshstr = "scp " + sourcefile + " root@" + desthost + ":" + destgf
            print sshstr

