#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  Author: Jason Wang
import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import admin

if __name__ == '__main__':
    manger = admin.FTPUsers()
    manger.main()