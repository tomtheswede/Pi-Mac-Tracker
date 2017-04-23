import socket, os, time
from subprocess import call

#TODO: Make an error handler for when there is no network connection

PORT=5009
sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('',PORT))
toPort=5007

#File presence checks
if os.path.isfile("monitorMacs.txt")==0:
    print("monitorMacs.txt file created.")
    log=open("monitorMacs.txt","a") #create if doesn't exist
    log.close()
if os.path.isfile("deviceLog.txt")==0:
    print("deviceLog.txt file created.")
    log=open("deviceLog.txt","a") #create if doesn't exist
    log.close()

def getLocalIP():
    gw = os.popen("ip -4 route show default").read().split()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((gw[2], 0))
    ipAddr = s.getsockname()[0]
    print("Local IP: ",ipAddr)
    return ipAddr;

def scanLocalNet():
    print("Commencing Arp...")
    call("sudo arp-scan --interface=eth0 --localnet >arpOutput.txt", shell=True)
    print("Finished Arp, now logging.")
    ipLog=open("arpOutput.txt","r")
    lines=ipLog.readlines()
    ipLog.close()
    out=list()
    for line in lines:
        if line[0:7]==IP[0:7]:
            values=line.split("\t")
            out.append(values[0]+","+values[1]+"\n")
    log=open("ipLog.txt","w")
    for line in out:
        log.write(line)
    log.close()

def refreshDevLogMacs():
    log=open("ipLog.txt","r")
    ipLog=log.readlines()
    log.close()
    log=open("deviceLog.txt","r")
    devLog=log.readlines()
    log.close()
    for i in range(0,len(devLog)):
        dev=devLog[i].split(",")
        for ipLine in ipLog:
            ip=ipLine.split(",")
            if dev[2]==ip[0] and dev[3]!=ip[1][:-1]:
                print("Updated mac address for",dev[0])
                devLog[i]=dev[0]+','+dev[1]+','+dev[2]+','+ip[1][:-1]+','+dev[4]+',online,'+time.strftime("%Y-%m-%d")+' '+time.strftime("%H:%M:%S") + ',' + dev[7]
    log=open("deviceLog.txt","w")
    for line in devLog:
        log.write(line)
    log.close()

def logMsg(msgType,devID,msg):
    global IP, toPort
    log=open("deviceLog.txt","r")
    devLog=log.readlines()
    log.close()
    msgflag=False
    for i in range(0,len(devLog)):
        line=devLog[i].split(",")
        if line[0]==devID:
            sendData=msgType+','+devID+','+msg
            #if line[5]=="online":
            sendThis=sendData.encode('utf-8') #Changing type
            sock.sendto(sendThis,(IP,toPort))
            print("Sent message:", sendData)
            msgflag=True
    if not msgflag:
        sendData=msgType+','+devID+','+msg
        print("Target device not device not found for this message: " + sendData)
    

def getIpFromMac(mac):
    log=open("ipLog.txt","r")
    lines=log.readlines()
    log.close()
    outIP = ""
    for line in lines:
        logSplit=line.split(",")
        if logSplit[1][:-1]==mac:
            outIP = logSplit[0]
            break
    return outIP;

def getMacFromIp(devIP):
    log=open("ipLog.txt","r")
    lines=log.readlines()
    log.close()
    outMac = ""
    for line in lines:
        logSplit=line.split(",")
        if logSplit[0]==devIP:
            outMac = logSplit[1][:-1]
            break
    return outMac;

def isOnNetwork(mac):
    log=open("ipLog.txt","r")
    lines=log.readlines()
    log.close()
    onNet=False
    for line in lines:
        logSplit=line.split(",")
        if logSplit[1][:-1]==mac:
            onNet = True
            break
    return onNet;

#Refresh that dev log
def refreshDevLog():
    offlineTimout = 4 #number of minutes till a device is registered as having left the network.
    log=open("ipLog.txt","r")
    ipLog=log.readlines()
    log.close()
    log=open("deviceLog.txt","a") #Create if it doesn't exist
    log.close
    log=open("deviceLog.txt","r")
    devLog=log.readlines()
    log.close()
    devOut=list()
    cmdList=list()
    if len(devLog)!=0:
        for devLine in devLog:
            dev=devLine.split(",")
            #print("New dev line: ", devLine)
            currentTime=float(time.strftime("%H"))+float(time.strftime("%M"))/60
            formattedTime=time.strftime("%Y-%m-%d")+' '+time.strftime("%H:%M:%S")
            lastUpdate=float(dev[6][11:13])+float(dev[6][14:16])/60
            readyForUpdate=currentTime-lastUpdate>(offlineTimout/60) #3 minutes timeout for offline devices
            #print("Time since update for",dev[0],"last updated",currentTime-lastUpdate)
            state="offline"
            for ipLine in ipLog:
                ip=ipLine.split(",")
                if dev[2]==ip[1][:-1]:
                    state="online"
                    break
            if state=="online":
                if dev[4]=="offline": #ie if there is a change in state from offline
                    cmdList.append("LOG,"+dev[0]+",online")
                    print("Prepped this message: LOG,"+dev[0]+",online")
                    devOut.append(dev[0]+','+dev[1]+','+dev[2]+','+dev[3]+','+dev[4]+',online,'+formattedTime+','+dev[7])
                else:
                    devOut.append(dev[0]+','+dev[1]+','+dev[2]+','+dev[3]+','+dev[4]+',online,'+formattedTime+','+dev[7])
            else: #state=="offline"
                if dev[4]=="online" and readyForUpdate:
                    cmdList.append("LOG,"+dev[0]+",offline")
                    print("Prepped this message: LOG,"+dev[0]+",offline")
                    devOut.append(dev[0]+','+dev[1]+','+dev[2]+','+dev[3]+','+dev[4]+',offline,'+formattedTime+','+dev[7])
                else:
                    devOut.append(dev[0]+','+dev[1]+','+dev[2]+','+dev[3]+','+dev[4]+','+dev[5]+','+dev[6]+','+dev[7])
    if len(devOut)!=0:
        log=open("deviceLog.txt","w")
        for line in devOut:
            log.write(line)
        log.close()
    if len(cmdList)!=0:
        for line in cmdList:
            cmd=line.split(",")
            logMsg(cmd[0],cmd[1],cmd[2])


def regMonDevs():
    log=open("monitorMacs.txt","r")
    lines=log.readlines()
    log.close()
    for line in lines:
        logSplit=line.split(",")
        if isOnNetwork(logSplit[1]):
            logIP(logSplit[0],getIpFromMac(logSplit[1]),logSplit[2][:-1])
    print("Monitor Macs registered")
    

def logIP( devID, devIP, devDescriptor):
    logDev=devID + "," + devIP + "," + devDescriptor + ","+getMacFromIp(devIP)+",online,lastValue," +time.strftime("%Y-%m-%d")+" "+time.strftime("%H:%M:%S") +','+'Blank'
    log=open("deviceLog.txt","r") #open to read in file contents
    lines=log.readlines() #stores file to memory
    log.close
    lines.append(logDev) #adds the new line
    lines.reverse()
    out=list()
    entries=set()
    for line in lines:
        if line[:6] not in entries:
            out.append(line)
            entries.add(line[:6])
    out.reverse()
    log=open("deviceLog.txt","w")
    for line in out:
        log.write(line)
    log.close()
    print("IP logged: " + logDev[:-1])
    return;

#Main code
IP=getLocalIP()
scanLocalNet()
regMonDevs()
time.sleep(1)
while True:
    scanLocalNet()
    refreshDevLogMacs()
    refreshDevLog()
    time.sleep(15)

