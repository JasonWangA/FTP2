#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  Author: Jason Wang
import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.client import FTPClient
from src import client
import sys
if sys.argv[1] == 'start':
    # ftpclient = FTPClient()
    # ftpclient.start()
    client.run()
elif sys.argv[1] == 'stop':
    exit()