#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  Author: Jason Wang
import os,sys
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import hashlib
import os,sys
import time,logging
from conf import conf
def b2s(b_str,code ='utf-8'):
    return str(b_str,code)

def s2b(s_str,code ='utf-8'):
    return bytes(s_str,code)


def show_md5(filename):
    import os
    import hashlib
    if not os.path.isfile(filename):
        return None
    myhash = hashlib.md5()
    f = open(filename,'rb')
    while True:
        b = f.read(4096)
        if not b:
            break
        myhash.update(b)
    f.close()
    return myhash.hexdigest()

def get_file_size(file):
    import os
    file_size = 0
    if os.path.isfile(file):
        file_size = os.stat(file).st_size
    return file_size

def get_file_name(file):
    import os
    filename = file.split('/')[-1]
    # print('file:%s size:%s'%(filename,))
    return filename

def md5(arg):
    """
    md5加密
    :param arg:
    :return:
    """
    obj = hashlib.md5()
    obj.update(bytes(arg,encoding='utf-8'))
    return obj.hexdigest()

def get_dir_size_for_linux(filename):
    """
    获取目录大小方法
    :param filename:
    :return:
    """
    import os
    size=0
    for (root,dirs,files) in os.walk(filename):
        for name in files:
            try:
                size += os.path.getsize(os.path.join(root,name))
            except:
                continue
    return size


def view_bar(num, total):
    rate = float(num) / float(total)
    rate_num = int(rate * 100)
    # r = '\r%s%d%%' % ("=" *num,rate_num, )
    r = '\r%s%d%%' % ("=" * rate_num,rate_num, )
    sys.stdout.write(r)
    sys.stdout.flush()

def ftp_logger():
    file_name = time.strftime("%Y-%m-%d",time.gmtime())
    file_handler = logging.FileHandler(os.path.join(conf.LOG_DIR,file_name),encoding='utf-8')
    fmt = logging.Formatter(fmt="%(asctime)s: %(message)s")
    file_handler.setFormatter(fmt)
    logger1 = logging.Logger('admin_logger',level=logging.INFO)
    logger1.addHandler(file_handler)
    return logger1