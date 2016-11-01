#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  Author: Jason Wang

import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.server import FTPServer
from src import server
import sys
if sys.argv[1] == 'start':
    # server = socketserver.ThreadingTCPServer((conf.IP_PORT),FTPServer)
    # server.serve_forever()
    server.run()
elif sys.argv[1] == 'stop':
    exit()