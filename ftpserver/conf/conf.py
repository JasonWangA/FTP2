#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  Author: Jason Wang
import os,sys
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IP_PORT = ('127.0.0.1',9009)

USERS_FILE = '../db/userinfo'

FILE_TRANSFR_SIZE = 1024

USERS_HOME_DIR = '%s/home/users/' %BASE_DIR

TMP_DIR = '%s/tmp' %BASE_DIR

LOG_DIR = '%s/log' %BASE_DIR

USER_DIR_SIZE = 1024 * 1024 * 1024


CODE_LIST = {
    '200': "Pass authentication!",
    '201': "Authentication fail wrong username or password",
    '206':  "transfer file successfuly",
    '300': "Ready to send file to client",
    '301': "Client ready to receive file data ",
    '302': "File doesn't exist",
    '303': "Path doesn't exist",
    '304': "space not enough",
    '305': "IO error",
    '306': "Socket error",
    '307': "Transfer file partically",
    "308": "Validate upload file successful",
    "309": "Validate upload file fail",
    "310": "Path or file doesn't exixt",
    '401': "Invalid instruction!",
    '404': "file didn't exist",
    '500': "Invalid execute successful",
    '501': "Invalid execute fail",
}

