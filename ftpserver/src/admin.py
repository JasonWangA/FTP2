#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  Author: Jason Wang
import sys,os
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import json
from conf import conf
from libs import lib
class FTPUsers(object):
    def __init__(self):
        self.users = []

    def add_account(self,):
            """
            添加客户端账户
            :param username: 账户名
            :param password: 账户密码
            :param homedir: 账户家目录
            :param maxsize: 账户分配磁盘额度
            :return:
            """
            if not os.path.exists(conf.USERS_FILE):
                os.makedirs(conf.USERS_FILE)
            while True:
                username = input("请输入用户的名字：").strip()
                if not username:
                    print("名字为空，请重新输入")
                    continue
                if username in os.listdir(conf.USERS_FILE):
                    print("用户名，已经存在，请重新输入")
                    continue
                name = username
                break
            while True:
                password = input('please input your password').strip()
                if not password:
                    print('密码为空，请重新输入')
                verify_password = input('please confirm your passwd').strip()
                if password != verify_password:
                    print('两次密码输入不一致，请重新输入！')
                    continue
                passwd = lib.md5(verify_password)
                break
            while True:
                quota_input = input("请输入用户的磁盘额度（GB):").strip()
                if not quota_input:
                    print('配额不能为空或为0')
                    continue
                quota = quota_input
                break

            homedir_abs_path = os.path.join(conf.USERS_HOME_DIR,name)
            os.makedirs(homedir_abs_path)
            base_info = {'username':name,
                         'password': passwd,
                         'homedir': homedir_abs_path,
                         'maxsize': quota,
            }
            # users = self.read_user()
            # self.users.append(username)
            # json.dump(self.users,open(conf.USERS_LIST),'w')
            os.makedirs(os.path.join(conf.USERS_FILE,name))
            json.dump(base_info,open(os.path.join(conf.USERS_FILE,name,"base_info.json"),'w'))

    def remove_client_account(self):
        """
        删除用户
        :return:
        """
        import shutil
        if not os.path.exists(conf.USERS_FILE):
            print('未发现用户存在')
            return
        while True:
            user_name = input('please input the user your want to delete:').strip()
            if not user_name:
                print("username shouldn't be empty")
            if user_name in os.listdir(conf.USERS_FILE):
                homedir_abs_path = os.path.join(conf.USERS_HOME_DIR,user_name)
                useinfo_json = os.path.join(conf.USERS_FILE,user_name,)
                shutil.rmtree(homedir_abs_path)
                shutil.rmtree(useinfo_json)
                print("用户【%s】删除成功"%user_name)
                break

    def read_user(self):
        self.users = json.load(open(conf.USERS_LIST),'r')
        return self.users
    def change_password(self):
        """
        修改用户密码
        :return:
        """
        if not os.path.exists(conf.USERS_FILE):
            print("无用户存在")
        while True:
            user_name = input("请输入要修改用户密码的账户").strip()
            if not user_name:
                print('名字不能为空')
            if user_name in os.listdir(conf.USERS_FILE):
                user_info_dict = json.load(open(os.path.join(conf.USERS_FILE,user_name,'base_info.json'),'r'))
                print('用户存在')
            name = user_name
            break
        while True:
            password_1 = input('please input the password to change:')
            if not password_1:
                print('密码不能为空')
                continue
            verify_password = input('please confirm passwd :\n')
            if password_1 == verify_password:
                passwd_md5 = lib.md5(verify_password)
                user_info_dict['password'] = passwd_md5
                break
        with open(os.path.join(conf.USERS_FILE,user_name,'base_info.json'),'w') as f:
            json.dump(user_info_dict,f,'w')
    def change_quota(self):
        """
        修改磁盘配额
        :return:
        """
        if not os.path.exists(conf.USERS_FILE):
            print("无用户存在")
            return
        while True:
            user_name = input("请输入要变更配额的用户的名字：  ").strip()
            if not user_name:
                print("名字不能为空！")
                continue
            if user_name in os.listdir(conf.USERS_FILE):
                user_info_dict = json.load(open(os.path.join(conf.USERS_FILE,user_name,'base_info.json'),'r'))
                name = user_name
            break
        while True:
            quota_limit = input('请输入新的配额： ').strip()
            if not quota_limit:
                print('配额不能为空或小于0！')
                continue
            quota = quota_limit
            break
        user_info_dict['maxsize'] = quota
        with open(os.path.join(conf.USERS_FILE,user_name,'base_info.json'),'w') as f:
            json.dump(user_info_dict,f,'w')
        print('【\033[32;0m配额修改成功，当前磁盘配额为%sG！\033[0m】'% quota)
    def exit_system(self):
        exit('退出系统')
    def main(self):
        menu_dict = {
            "1": self.add_account,
            "2": self.change_password,
            "3": self.change_quota,
            "4": self.remove_client_account,
            "5": self.exit_system,
        }
        while True:
            msg = """__________________________________
MyFtp后台管理系统
-------------------
【1】     创建用户
【2】     修改密码
【3】     修改配额
【4】     删除用户
【5】     退出系统
-------------------"""
            print(msg)
            choice = input("请按数字对应的功能进行选择：").strip()
            if choice in menu_dict:
                menu_dict[choice]()
            else:
                print("invalid choice!")

# f1 = FTPUsers()
# f1.main()
# # f1.init()
# f1.main()