# -*- coding: utf-8 -*-
#
# (c) 2016 Nuneo, http://www.nuneo.top
#
# This file is part of Ema.
#
# Ema is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Ema is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ema.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import print_function


import os
import sys
import hashlib
import urllib2
import collections

def make_files_md5(version="0.1"):
    files = []
    for (dirpath, dirnames, filenames) in os.walk("."):
        dirpath = os.path.normpath(dirpath).replace("\\", "/")
        check_it=True
        spath = dirpath.split("/")
        for sdir in spath:
            if sdir and sdir != "." and sdir[0] == ".":
                check_it=False
        if check_it:
            for filename in filenames:
                if filename.split(".")[-1] == "pyc" or filename == "files.md5" or filename == "version.py" or spath[0] == "save":
                    continue
                if dirpath != ".":
                    files.append(dirpath+"/"+filename)
                else:
                    files.append(filename)
    out = version+"\n"
    for f in files:
        out += hashlib.md5(open(f, "rb").read()).hexdigest()+" "+str(os.path.getsize(f))+" "+f+"\n"
    open("data/files.md5", "w").write(out)
    return out

def apply_patch():
    local_list = {}
    EMA_VERSION = open("version.py", "r").read().split("\"")[1]
    md5s = make_files_md5(EMA_VERSION).split("\n")

    EMA_VERSION = md5s[0]
    for line in md5s[1:]:
        if line:
            sline = line.split(" ")
            local_list[sline[2]] = (sline[0], sline[1])
            
    try:
        response = urllib2.urlopen('https://bobignyportugaise.org/share/Ema/data/files.md5', timeout=3).read(10000).split("\n")
    except urllib2.URLError as err:
        print("Error downloading files list:", err)
        return False

    dist_list = {}
    DIST_VERSION = response[0]
    out = ""
    for line in response[1:]:
        if line:
            sline = line.split(" ")
            dist_list[sline[2]] = (sline[0], sline[1])

    print("dist: ", DIST_VERSION, "vs local:", EMA_VERSION)
    if DIST_VERSION != EMA_VERSION: # PATCH !!
        print("Patching...")
        have_error = False
        od = collections.OrderedDict(sorted(dist_list.items()))
        for name, (md5, size) in od.items():
            if not name in local_list or md5 != local_list[name][0]:
                print("Processing...", name, "", end='')
                if not name in local_list:
                    print("NOT FOUND", end="")
                else:
                    print("OLD VERSION", end="")
                print(" -> Downloading")
                try:
                    update = urllib2.urlopen('https://bobignyportugaise.org/share/Ema/'+name, timeout=1).read(int(size))
                except urllib2.URLError as err:
                    print(" !!! Error downloading file", err)
                    have_error = True
                    continue
                
                print("     Checking download...", end="")
                new_md5 = hashlib.md5(update).hexdigest()
                if new_md5 == md5:
                    if name in local_list:
                        del(local_list[name])
                    if os.path.dirname(name) and not os.path.isdir(os.path.dirname(name)):
                        os.makedirs(os.path.dirname(name))
                    open(name, "wb").write(update)
                    #out += md5+" "+name+"\n"
                    print("     File patched!")
                else:
                    have_error = True
                    print("     Bad md5 !!!")
            else:
                out += md5+" "+name+"\n"

        if have_error:
            version = EMA_VERSION
        else:
            version = DIST_VERSION
        out = version+"\n"+out
        open("files.md5", "w").write(out)
        open("version.py", "w").write("EMA_VERSION=\""+version+"\"")


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        if sys.argv[1] == "apply":
            apply_patch()
        elif sys.argv[1] == "create":
            if len(sys.argv) > 2:
                EMA_VERSION = sys.argv[2]
            else:
                EMA_VERSION = open("version.py", "r").read().split("\"")[1].split(".")
                EMA_VERSION = EMA_VERSION[0]+"."+EMA_VERSION[1]+(".%03d" % (int(EMA_VERSION[2])+1))
            print("Creating patch "+EMA_VERSION)
            make_files_md5(EMA_VERSION)
            open("version.py", "w").write("EMA_VERSION=\""+EMA_VERSION+"\"")
    else:
        print("Synxtax error: "+sys.argv[0]+" (apply|create [version])")
