#!/usr/bin/env python
# -*- coding:utf-8 -*-
#  Author: Jason Wang
import os,sys
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import socketserver
import json,socket
from conf import conf
from libs import lib

class FTPServer(socketserver.BaseRequestHandler):
    def handle(self):
        #print(self.request,self.client_address,self.server)
        self.__logger = lib.ftp_logger()
        self.request.sendall(bytes('欢迎使用Jason的ftp',encoding='utf-8'))#发送服务器端欢迎信息
        self.__command = ['put','get','cd','rm','du','mkdir']
        while True:
            try:
                data = self.request.recv(4096)#接收客户端传送命令信息
                if len(data) == 0:#接收信息为空，防止进程阻塞，退出此次连接
                    break
                print("data",data)
                print("[%s] says:%s" %(self.client_address,data.decode()))
                # cmd_data = json.loads(data.decode())
                cmd_data = data.decode()#解码二进制信息
                if cmd_data.startswith('auth'):#如果传送信息以auth开始，此为用户验证
                    self.master_auth(cmd_data)#调用服务器端验证方法处理此消息
                elif cmd_data == 'quit':
                    print("来自%s:%s的客户端主动断开连接。。"%(self.client_address[0],self.client_address[1]))
                    self.__logger.info('%s disconnect with ftp server'%self.client_address)
                else:
                    cmd_data = json.loads(cmd_data)
                    print(cmd_data)
                    cmd_action = cmd_data.get("action")#其他情况，获取用户要执行的命令
                    if cmd_action in self.__command:#服务器端定制命令
                        if hasattr(self,"master_%s"%cmd_action):
                            func = getattr(self,"master_%s"%cmd_action)
                            func(cmd_data)
                            print(cmd_data)
                        else:
                            print('cmd is not supported',cmd_action)
                    else:
                        self.__localcmd(cmd_action)
            except Exception as e:
                print(e)
                print("来自%s:%s的客户端主动断开连接..." % (self.client_address[0], self.client_address[1]))
                break
    def master_put(self,client_cmd):#服务器端上传命令
        import shutil
        print("----------put",client_cmd)
        filename = client_cmd.get('filename')#获取上传文件名
        filesize = client_cmd.get('filesize')#获取上传文件大小
        md5value = client_cmd.get('md5value')#获取上传文件md5值
        space_judge = self.judgespace(filesize)#调用checkfreesize函数检查上传文件大小是否超过分配额度
        if space_judge:#空间足够
            # sever_response = {"status":"normal"}
            # self.request.send(bytes(json.dumps(sever_response),encoding='utf-8'))#给客户端发送正常转态，准备接受客户端传送文件
            #定义临时接收文件，用于断点续传
            tmp_filename = '%s.tmp' %filename
            tmp_f_abspath = os.path.join(self.__current_path,tmp_filename)
            real_f_abspath = os.path.join(self.__current_path,filename)
            #如果临时文件存在，获取文件大小，传送给客户端，继续上次传送位置传输
            if os.path.exists(tmp_f_abspath):
                tmp_f_size = os.stat(tmp_f_abspath).st_size
                f = open(tmp_f_abspath,'ab')
            else:
                tmp_f_size = 0#如果为第一次传送的文件，临时文件大小为0
                f = open(tmp_f_abspath,'wb')
            #服务器端发送接收到客户端传送文件的大小，并让客户端确认发送
            sever_response = {"status":"normal","filesize":tmp_f_size,}
            self.request.send(bytes(json.dumps(sever_response),encoding='utf-8'))#给客户端发送正常转态，准备接受客户端传送文件
            # recv_size = 0
            while tmp_f_size < filesize:#当接受文件大小与客户端传送文件大小一致时，停止传送文件
                try:
                    data = self.request.recv(4096)
                    f.write(data)
                    tmp_f_size += len(data)
                    print('filesize: %s receive:%s'%(filesize,tmp_f_size))
                    print('current directory:%s'%self.__current_path)
                except socket.socket.error as e:
                    print(self.code_list['306'])
                    f.close()
                    break
                except IOError as e:
                    print(self.code_list['305'])
            f.close()
            tmp_f_md5 = lib.show_md5(tmp_f_abspath)
            print(tmp_f_md5)
            if tmp_f_md5 == md5value:
                # print('here')
                os.rename(tmp_f_abspath,real_f_abspath)
                print("file recv sucess")
                self.request.sendall(lib.s2b('308'))
                self.__logger.info('[%s]  %s'%(filename,self.code_list['308']))
            else:
                self.request.sendall(lib.s2b('309'))
                self.__logger.info('[%s]  %s'%(filename,self.code_list['309']))
            # f.close()
        else:
            msg = {
                "status":304,
            }
            self.request.sendall(bytes(json.dumps(msg),encoding='utf8'))
    def master_get(self,cmd_data_dict):
        print("-----------get",cmd_data_dict)
        filename = cmd_data_dict.get('filename')#获取客户端发送的文件名
        # send_size = cmd_data_dict.get('recvsize')
        if os.path.exists(self.__current_path + '/' + filename):#判断是否存在用户要下载的文件
            abs_filepath = os.path.join(self.__current_path,filename)#拼接文件的绝对路径
            if not os.path.isdir(abs_filepath):#判断文件不是目录
                filesize = os.stat(abs_filepath).st_size#获取文件的大小
                md5 = lib.show_md5(abs_filepath)
                print(filesize,md5)
                msg = {
                    "filesize":filesize,
                    "md5":md5,
                    "status":300,
                }
                json_str = json.dumps(msg)
                self.request.sendall(json_str.encode())#给客户端发送确认下载信息
                Client_msg = json.loads(self.request.recv(1024).decode())#获取客户端返给服务器端的确认信息
                print(Client_msg)
                if Client_msg.get('status')== 301:#收到确认消息，服务器端开始传送文件
                    f = open(abs_filepath,'rb')
                    # f.seek(send_size)#判断文件传输的位置，如果未传完，到上次传送的位置继续传文件
                    for line in f:
                        self.request.send(line)#读取并传送文件
                    # print('transfer file down')
                    f.close()
                    Client_final_msg = json.loads(self.request.recv(1024).decode())
                    # print(Client_final_msg)
                    if Client_final_msg.get('status') == 206:
                        print(self.code_list.get('206'))
                    elif Client_final_msg.get('status') == 307:
                        print(self.code_list.get('307'))
                elif Client_msg.get('status') == 402:
                    send_size = Client_msg.get('filesize')
                    f = open(abs_filepath,'rb')
                    f.seek(send_size)#判断文件传输的位置，如果未传完，到上次传送的位置继续传文件
                    for line in f:
                        self.request.send(line)#读取并传送文件
                    print('transfer file down')
                    f.close()
                    Client_final_msg = json.loads(self.request.recv(1024).decode())
                    if Client_final_msg.get('status') == 206:
                        print(self.code_list.get('206'))
                    elif Client_final_msg.get('status') == 307:
                        print(self.code_list.get('307'))
                else:
                    print('invalid response')
        else:
            msg = {"status":404}
            json_str = json.dumps(msg)
            self.request.sendall(json_str.encode())
    def master_rm(self,cmd_data_dict):#服务器端删除文件方法
        filename = cmd_data_dict.get('args')#获取删除命令后对象参数
        if os.path.isfile(self.__current_path + '/' + filename):#验证文件是否存在
            abs_file_path = self.__current_path + '/' + filename
            os.remove(abs_file_path)#存在则删除文件
            self.request.send(lib.s2b('ok'))
        else:
            print('the file to delete is not exist')
            self.request.send(lib.s2b('file not found'))


    def judgespace(self,filesize):
        """
        检查剩余空间是否足以上传文件
        :param client_cmd:
        :return:
        """
        freesize = int(int(self.__current_user_maxsize)*1024**3 - int(lib.get_dir_size_for_linux(self.__current_path)))#判定用户剩余空间大小
        if filesize < freesize:
            # self.request.sendall(lib.s2b('space enough to use'))
            return True
        else:
            # self.request.sendall(lib.s2b('space not enough to use, try another small file'))
            return False
    def master_du(self,cmd_data):
        path = os.path.join(conf.USERS_HOME_DIR, self.__current_user)
        # 递归遍历家目录下的所有目录和文件，计算文件大小的总和
        size = 0
        for root, dirs, files in os.walk(path):
            size += sum([os.stat(os.path.join(root, name)).st_size for name in files])
        free_size = (int(self.__current_user_maxsize)*1024**3 - size)/(1024**2)
        mb_size = size / 1024 / 1024
        msg = "当前已用空间：%.2f MB\n当前可用空间：%.2f MB\n用户磁盘限额： %sGB"\
              % (mb_size, free_size, self.__current_user_maxsize)
        self.request.sendall(lib.s2b(msg))
    def master_cd(self,client_cmd):#服务器端切换目录方法
        """
        服务器端切换目录方法
        :param client_cmd:
        :return:
        """
        print(client_cmd)
        path = client_cmd.get('path')
        base_path = os.path.join(conf.USERS_HOME_DIR,)
        print(self.__current_path)
        if path == '.':
            pass
        if path == '..':
            relative_path = self.__current_path.replace(base_path,"")
            print(relative_path)
            if os.path.split(self.__current_path)[1]  == self.__current_user:#如果已经在此用户根目录，不做任何操作
                self.request.sendall(lib.s2b(relative_path))
            else:
                # print(os.path.split(relative_path)[1])#若果当前目录包含../db/users/Jason()，则可以切换目录
                if relative_path.split('/')[0] == self.__current_user :
                    self.__current_path = os.path.split(self.__current_path[0:len(self.__current_path)-1])[0]
                    print(os.path.split(self.__current_path[0:len(self.__current_path)-1])[0])
                    relative_path = self.__current_path.replace(base_path,"")
                    self.request.sendall(lib.s2b(relative_path))
                else:
                    self.__current_path = os.path.join(base_path,self.__current_user)
                    relative_path = os.sep
                    self.request.sendall(lib.s2b(relative_path))
        else:
            if os.path.isdir(self.__current_path + '/' + path):
                self.__current_path += '/' + path + '/'
                relative_path = self.__current_path.replace(base_path,"")
                self.request.sendall(lib.s2b(relative_path))
            else:
                relative_path = os.sep
                self.request.sendall(lib.s2b(relative_path))
    def master_mkdir(self,client_cmd):
        home_path = self.__current_path
        print(home_path)
        if client_cmd.get('path').startswith("/"):
            dir_path = os.path.join(home_path + client_cmd['path'].lstrip("/"))
        else:
            dir_path = os.path.join(home_path,client_cmd['path'])
            # print(dir_path)
        if not dir_path.startswith(home_path):
            self.request.sendall("401".encode())
            return
        if os.path.exists(dir_path):
            self.request.sendall("305".encode())
            # print(dir_path)
            return
        else:
            os.mkdir(dir_path)
            self.request.sendall("308".encode())
    def master_auth(self,client_cmd):
        """
        验证客户端账户
        :return:
        """
        client_cmd = client_cmd.split('|')
        #判断用户是否存在
        if os.path.exists(os.path.join(conf.USERS_FILE,client_cmd[1])):
            userinfo = json.load(open(os.path.join(conf.USERS_FILE,client_cmd[1],'base_info.json'),'r'))
            #判断用户密码是否正确
            if userinfo['password'] == client_cmd[2]:
                #验证通过设置当前用户为认证用户
                self.__current_user = userinfo['username']
                #当前用户为用户家目录
                self.__current_path = userinfo['homedir']
                #设定当前用户的磁盘配额
                self.__current_user_maxsize = userinfo['maxsize']
                # print(self.__current_user_maxsize)
                #告诉客户端验证成功
                self.code_list = conf.CODE_LIST
                confirm = '200'
                self.request.sendall(lib.s2b(confirm))
                self.__logger.info('user [%s] logged in successfully'% self.__current_user)
            else:
                confirm = '201'
                self.request.sendall(lib.s2b(confirm))
        else:
            confirm = '201'
            self.request.sendall(lib.s2b(confirm))


    def __localcmd(self,cmd):
        import subprocess
        cmd_call = subprocess.Popen(cmd,shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE,cwd=self.__current_path)
        cmd_res = cmd_call.stdout.read()
        if not cmd_res:
            cmd_res = cmd_call.stderr.read()
        if len(cmd_res) == 0:#如果命令执行结果为空
            cmd_res = bytes('cmd exist output but null',encoding='utf-8')
        cmd_result_size_msg = lib.s2b('CMD_RESULT_SIZE|%s'%len(cmd_res))#给客户端传送命令执行结果大小，以防出现粘包情况
        self.request.send(cmd_result_size_msg)
        client_ack = self.request.recv(200)
        if client_ack.decode().startswith('start'):#如果收到客户端发送的确认消息，传送命令执行结果
            self.request.send(cmd_res)
def run():
    server = socketserver.ThreadingTCPServer((conf.IP_PORT),FTPServer)
    server.serve_forever()
if __name__ == '__main__':
    server = socketserver.ThreadingTCPServer((conf.IP_PORT),FTPServer)
    server.serve_forever()
