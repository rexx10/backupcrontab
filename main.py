#-*-coding:utf-8-*-

import paramiko
from paramiko import SSHClient
import requests
import time
import ast
import os

'''
需先要備份的主機作產生 ssh-key的動作
'''

rpath = "/home/tgesadmin"
machineTxt = rpath + "/.machine/machine.txt"
tempPath = rpath + "/back_Crontab"
targetFolder = rpath + "/backupCrontab"
getToday = time.strftime("%Y%m%d", time.localtime())
sshPort = 22
targetId = "tgesadmin"
targetIp = ""
backUpPrefix = "crontab-"
remotePath = "/home/<remotePath>"    #遠端目錄


def getMachineList(path):
    #Get Machine IPs and operator name
    #data type: dict
    data = open(path, "r", encoding="utf-8")
    datalist = data.read()
    redata = ast.literal_eval(datalist)

    return redata

#檢查資料夾是否存在
def chkBackUpFolder(path, folderNmae=""):
    if(os.path.isdir(path + "/" + folderNmae)):
        return path + "/" + folderNmae

    os.system("mkdir " + path + "/" + folderNmae)
    return path + "/" + folderNmae


#檢查檔案是否已存在
def chkBackUpDataName(path, prefixName, dfName="", tar="", num=1):
    for d in range(num, num+1):
        suffixNum = ("%03d")%(d)

    nTargetdfName = dfName + tar

    if(os.path.isfile(path+prefixName+suffixNum+nTargetdfName)):
        num += 1
        return chkBackUpDataName(path, prefixName, dfName, tar, num)

    fullName = prefixName+suffixNum+dfName
    
    return fullName


def telegramMsag(msg):
    oneCDNLoginAcc = "ppcaipiao123@3311.com"
    oneCDNLoginPass = "ppcaipiao123"

    telegramBot = "<telegramBot>"
    telegramBot2 = "<telegramBot2>"
    telegramToken = "<telegramToken_key>"
    telegramToken2 = "<telegramToken2_key>"
    telegramSendUrl = "https://api.telegram.org/" + telegramBot2 + ":" + telegramToken2 + "/sendMessage"
    telegramChatId = "@" + "a123485sw859"
    telegramPlData = {
                          "chat_id": telegramChatId, 
                          "text": "", 
    }

    telegramPlData["text"] = msg
    requests.get(telegramSendUrl, data=telegramPlData)

if __name__ == "__main__":

    if(os.path.isdir(targetFolder) == False):
        #沒有備份目標資料夾則退出程序
        print("Target folder does not exist ....")
        os._exit(0)

    if(os.path.isfile(machineTxt) == False):
        #沒有IP設定檔則退出程序
        print("Machine IPs does not exist ....")
        os._exit(0)
    
    #取得所有欲備份資料庫的伺服器
    machineList = getMachineList(machineTxt)

    for machine in machineList:

        targetFolderPath = chkBackUpFolder(targetFolder, machineList[machine]["Operator"])
        backupCronName = chkBackUpDataName(targetFolderPath+"/", backUpPrefix+getToday, "", ".tar.gz")

        msg = "現在開始備份"
        telegramMsag(msg)
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        sshIp = machineList[machine]["ip"]
        sshId = machineList[machine]["account"]
        sshPasswd = machineList[machine]["passwd"]
        ssh.connect(hostname=sshIp, port=sshPort, username=sshId, password=sshPasswd)

        cmd_cd = "cd " + remotePath
        cmd_cp = "cp /etc/crontab " + remotePath + "/" + backupCronName
        #使用絕對路徑壓縮，但不壓入路徑
        cmd_tar = "tar -C " + remotePath + " -zcPf " + remotePath + "/" + backupCronName + ".tar.gz " + backupCronName
        
        #執行ssh命令
        stdin, stdout, stderr = ssh.exec_command(cmd_cd+";"+cmd_cp+";"+cmd_tar,get_pty=True)
        cmd_tar_err = stderr.read()

        cmd_scp = "scp " + rpath + "/" + backupCronName + ".tar.gz "+targetId+"@"+targetIp+":"+targetFolder
        cmd_scp += "/"+machineList[machine]["Operator"]
        # print(cmd_scp)
        stdin, stdout, stderr = ssh.exec_command(cmd_scp,get_pty=True)
        cmd_scp_err = stderr.read()

        cmd_rm_rf = "rm -rf " + remotePath + "/" + backupCronName + "*"
        stdin, stdout, stderr = ssh.exec_command(cmd_rm_rf,get_pty=True)    
    
        ssh.close()
        backUpStatus = "失敗"

        if(os.path.isfile(targetFolder+"/"+ machineList[machine]["Operator"] + "/" + backupCronName+".tar.gz")):
            backUpStatus = "成功"

        getNowTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msg = "Crontab 備份 \n"
        msg += "主機： " + machineList[machine]["Operator"] + "\n"
        msg += "檔案： " + backupCronName+".tar.gz \n"
        msg += "時間： " + getNowTime + "\n"
        msg += "備份 " + backUpStatus

        telegramMsag(msg)
