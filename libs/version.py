import os
import re
import sys
import win32api
from new_function.default_path import *

def getFileVersion(file_name):
    info = win32api.GetFileVersionInfo(file_name,os.sep)
    ms = info['FileVersionMS']
    ls = info['FileVersionLS']
    version = '%d.%d.%d.%d'%(win32api.HIWORD(ms),win32api.LOWORD(ms),win32api.HIWORD(ls),win32api.LOWORD(ls))
    return version


# 是否需要更新
def compareVersion(cur_version,rem_version):
    cur_temp=re.split('\.',cur_version)
    rem_temp=re.split('\.',rem_version)

    cur_temp=[int(cur_temp[i]) for i in range(len(cur_temp))]
    rem_temp=[int(rem_temp[i]) for i in range(len(rem_temp))]

    return cur_temp<rem_temp

print(sys.executable)
__appname__ = DefaultPath.software_name
__version__ = getFileVersion(sys.executable)    # 软件版本号
