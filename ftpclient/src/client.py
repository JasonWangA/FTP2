#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  Author: Jason Wang
import sys,os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import socket
import json
from conf import conf
from libs import lib

class FTPClient(object):
    def __init__(self):
        """
        初始化客户端
        :return:无
        """
        self.current_user = 'guest'
        self.current_path = ''
        self.code_list = conf.CODE_LIST
        self.__sk = socket.socket()
        self.__conn = self.__sk.connect(conf.IP_PORT)#客户端连接服务器端ip
        self.__is_login = False#默认登录状态
        self.tmp_path = conf.TMP_DIR
        
    def start(self):
        """
        启动客户端进程
        :return:
        """
        print(lib.b2s(self.__sk.recv(200)))#显示欢迎信息
        self.auth()
        while True:#循环获取用户输入的命令，如果输入quit退出循环，并退出客户端
            user_input = input('%s:%s ftp>> '%(self.current_user,self.current_path)).strip()
            if len(user_input) == 0:continue
            user_input_split = user_input.split()#分割用户输入的命令
            # print(user_input_split)
            if user_input.startswith('quit'):#判断用户输入的命令，如果quit退出循环，并退出客户端
                self.__sk.sendall(lib.s2b("quit"))
                break
            # if user_input_split[0] == 'put' or user_input_split[0] == 'get' :
            if hasattr(self,user_input_split[0]):#判断用户命令是否有对应方法
                func = getattr(self,user_input_split[0])#获取方法
                func(user_input_split)
                # print(func)
            else:
                print("\033[31;0m无效的指令！\033[0m")
                FTPClient.print_help_msg()
                continue


    def auth(self):
        """
        认证方法。错误输入超过三次，退出程序
        :return:
        """
        times = 0
        while True:
            if times >= 3:
                self.__sk.sendall(lib.s2b("exit"))
                self.__sk.close()
                exit('输入密码错误已达三次，程序退出')
            username = input('username:\n').strip()#获取用户名
            if not username:
                print('用户名不能空')
                continue
            password = input('password:\n').strip()#获取用户密码
            if not password:
                print('密码不能为空')
                continue
            self.__sk.sendall(lib.s2b(('auth|%s|%s') %(username,lib.md5(password))))#调用服务端的验证方法，验证用户名密码
            res = lib.b2s(self.__sk.recv(200))#获取验证结果
            if res == '200':#如果通过验证，修改当前登录用户和状态
                self.current_user = username
                self.__is_login = True
                self.current_home_path = os.path.join(conf.USERS_HOME_DIR,self.current_user)
                if not os.path.exists(self.current_home_path):
                    os.makedirs(self.current_home_path)
                pwd = os.sep
                return pwd
            elif res == '201':
                print(conf.CODE_LIST['201'])
                times += 1
                continue

    def put(self,user_input):#客户端上传文件方法
        if len(user_input) == 2:
            abs_filepath = os.path.join(self.current_home_path,user_input[1])
            print(abs_filepath)
            if os.path.isfile(abs_filepath):#判断上传文件是否存在
                filesize = os.stat(abs_filepath).st_size#获取上传文件大小
                filename = abs_filepath.split("/")[-1]#获取上传文件名
                md5value = lib.show_md5(abs_filepath)#获取上传文件md5值
                print('file:%s size:%s' %(abs_filepath,filesize))#打印文件md5值
                msg_data = {"action":"put",
                            "filename":filename,
                            "filesize":filesize,
                            "md5value":md5value,
                          }
                print(msg_data)
                self.__sk.send(bytes(json.dumps(msg_data),encoding="utf-8"))#传送给服务器端要执行的操作及文件信息（大小，文件名等）
                server_confirmation_msg = self.__sk.recv(1024)#客户端接收到服务器端确认接收消息
                print(server_confirmation_msg)
                confirm_data = json.loads(server_confirmation_msg.decode())#将接收消息转化为字典
                if confirm_data['status'] =='normal':#确认可以接收后本地打开文件传输内容
                    print("start sending file ",filename)
                    send_size = confirm_data.get('filesize')
                    f = open(abs_filepath,'rb')
                    f.seek(send_size)
                    for line in f:
                        self.__sk.send(line)#一行一行传输文件
                        send_size += len(line)
                        lib.view_bar(send_size,filesize)#利用进度条工具，显示传输进度
                    f.close()#关闭文件
                    resonse = lib.b2s(self.__sk.recv(1024))
                    print('\nResponse code:%s'%resonse)
                    print("send file done ")
                elif confirm_data['status'] == 304:
                    print(self.code_list['304'])
                else:
                    self.code_list.get('307')
        else:
            print(self.code_list['401'])
            #s.send(bytes(send_data,encoding='utf8'))
            #收消息
            # recv_data=self.__sk.recv(1024)
            # print(str(recv_data,encoding='utf8'))

    def local_cmd(self,user_input_split):#定义模拟ssh远程执行命令函数
        user_cmd = user_input_split[0]#分割用户输入，获取要执行的操作命令
        if len(user_input_split) == 2:#如果包含参数，分割命令参数
            args = user_input_split[1]
            msg_data = {"action":user_cmd,"args":args}#将要执行的命令和参数封装到字典传送给客户端
        elif len(user_input_split) == 1:
            msg_data = {"action":user_cmd,}
        self.__sk.sendall(bytes(json.dumps(msg_data),encoding='utf8'))#发送Linux命令
        clinet_recv_ack_msg = self.__sk.recv(1024).decode()#客户端接收命令执行结果大小
        # print(clinet_recv_ack_msg)
        if clinet_recv_ack_msg.startswith('CMD_RESULT_SIZE'):#客户端接收到服务器端发送的命令执行结果大小后，准备发送确认接收消息
            cmd_result_size = int(clinet_recv_ack_msg.split('|')[1])
            self.__sk.sendall(lib.s2b('start'))#发送确认开始指令
            recv_size = 0#设定接收初始接收大小为0
            recv_msg = b''
            while recv_size < cmd_result_size:#当接收结果大小与命领结果大小一致时，停止接收
                recv_data = self.__sk.recv(1024)
                recv_msg += recv_data
                recv_size += len(recv_data)
                # print('Cmd result size:%s Receive size:%s'%(cmd_result_size,recv_size))
            print(lib.b2s(recv_msg))
    def get(self,user_input):
        if len(user_input) == 2:
            filename = user_input[1]
            dst_path = os.path.join(conf.USERS_HOME_DIR,self.current_user)
            if not os.path.exists(dst_path):
                os.makedirs(dst_path)
            dst_file = os.path.join(dst_path,filename)
            if os.path.exists(dst_file):
                 option = input('the file already exist, will override,if cancel, type any button ')
                 if option != "y":
                     print('cancel get task')
                     return

            if os.path.isfile(dst_file):
                recv_size = os.stat(dst_file).st_size#如果接收过程中断，保存接收文件大小
            else:
                recv_size = 0#设定第一次接收大小为0
            msg_data = {"action":"get","filename":filename,}#发送执行的方法和文件名
            self.__sk.send(bytes(json.dumps(msg_data),encoding='utf-8'))
            Response= json.loads(self.__sk.recv(1024).decode())
            if Response.get('status') == 300:
                filesize = int(Response.get('filesize'))
                md5 = Response.get('md5')
                # self.__sk.sendall(lib.s2b('start'))
                temp_path = os.path.join(conf.USERS_HOME_DIR,self.current_user,".tmp")
                if not os.path.exists(temp_path):
                    os.makedirs(temp_path)
                # md5_temp = lib.show_md5(os.path.join(temp_path,filename))
                temp_file = os.path.join(temp_path,filename,)
                if os.path.exists(temp_file):
                    print("there exist file didn't download completely")
                    recv_size = os.stat(temp_file).st_size
                    msg = {
                        "status":402,
                        "filesize":recv_size
                    }
                    json_str = json.dumps(msg)
                    self.__sk.sendall(bytes(json_str,encoding='utf8'))
                #没有临时文件存在，发送确认接收消息
                else:
                    msg = {"status":301}
                    msg_json = json.dumps(msg)
                    self.__sk.sendall(bytes(msg_json,encoding='utf8'))
                recv_msg = b''
                f = open(temp_file,'ab')
                while recv_size < filesize:#当接收结果大小与命领结果大小一致时，停止接收
                    try:
                        recv_data = self.__sk.recv(1024)
                        f.write(recv_data)
                        recv_size += len(recv_data)
                        # print('Cmd result size:%s Receive size:%s'%(filesize,recv_size))
                        lib.view_bar(recv_size,filesize)
                    except socket.socket.error as e:
                        print(self.code_list['306'])
                    except IOError as e:
                        print(self.code_list['305'])
                f.close()
                print('download file done')
                temp_file_md5 = lib.show_md5(temp_file)
                print('file md5:%s'%md5)
                print('temp md5:%s'%temp_file_md5)
                if temp_file_md5 == md5:
                    import shutil
                    shutil.copyfile(temp_file,dst_file)
                    os.remove(temp_file)
                    confirm = json.dumps({"status":206})
                    print(conf.CODE_LIST.get('206'))
                    self.__sk.sendall(bytes(confirm,encoding='utf8'))
                else:
                    confirm = json.dumps({"status":307})
                    print(self.code_list.get('307'))
                    self.__sk.sendall(bytes(confirm,encoding='utf8'))
            elif Response.get('status') == 404:
                print(self.code_list.get('404'))
        else:
            print(self.code_list['401'])
    def ls(self,user_input):
        """
        查看目录内容
        :param user_input:
        :return:
        """
        if len(user_input) == 1:
            self.local_cmd(user_input)#用self.localcmd执行linux原生命令
        else:
            print(self.code_list.get('401'))

    def du(self,user_input):
        """
        查看剩余磁盘额度
        :return:
        """
        msg_dict = {
            "action": "du",
        }
        self.__sk.sendall(bytes(json.dumps(msg_dict),encoding='utf8'))
        print(lib.b2s(self.__sk.recv(1024)))

    def mkdir(self,user_input):
        """
        新建文件夹
        :param user_input:
        :return:
        """
        if len(user_input) == 1:
            print("未确定要切换的目录")
            return
        else:
            path = user_input[1]
        client_msg = {
            "action": "mkdir",
            "path": path,
        }
        self.__sk.sendall(bytes(json.dumps(client_msg),encoding='utf8'))
        ##确认服务器发送信息
        confirm = self.__sk.recv(1024).decode()
        if confirm == '305':
            print('305 %s'%self.code_list.get('305'))
        else:
            print('308 %s'%self.code_list.get('308'))
    def cd(self,user_input):
        """
        切换服务器端路径
        :param user_input:
        :return:
        """
        if len(user_input) == 1:
            path = "."
        else:
            path = user_input[1]
        msg_dict = {
            "action": "cd",
            "path": path,
        }
        self.__sk.sendall(bytes(json.dumps(msg_dict),encoding='utf8'))
        response = lib.b2s(self.__sk.recv(4096))
        if response== "401":
            print("401 %s" % self.code_list["401"])
        else:
            # 如果服务器返回正常，将当前目录进行修改
            self.current_path = response
    def help(self, cmd_list):
        """
        打印帮助信息
        :param cmd_list:
        :return:
        """
        FTPClient.print_help_msg()
    @staticmethod
    def print_help_msg():
        """
        提供帮助信息的静态方法
        :return:
        """
        msg = """
【帮助信息】：
    可执行命令：
    ls：      查看目录内容
    cd：      切换目录
    mkdir：   新建目录（因为平台的原因，暂不支持递归建立）
    du：      查看用户当前已用磁盘容量
    get：     下载文件
    put：     上传文件
    """
        print(msg)
def run():
    client = FTPClient()
    client.start()
    # def rm(self,user_input_split1):
    #     msg_data = {"action":"rm"}
    #     self.__sk.send(bytes(json.dumps(msg_data),encoding='utf8'))
if __name__ == '__main__':
    client = FTPClient()
    client.start()