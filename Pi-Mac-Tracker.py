import time
from subprocess import call


def scanLocalNet():
    print("Commencing Arp at time      ",int(time.time()))
    call("sudo arp-scan --interface=eth0 --localnet >arpOutput.txt", shell=True)
    print("Finished Arp, now logging at",int(time.time()))
    with open("arpOutput.txt") as textFile:
        lines = [line.split('\n')[0] for line in textFile]
    out=list()
    lines=lines[2:-3]
    #print(lines)
    for line in lines:
        values=line.split("\t")
        storeString=values[0]+","+values[1]
        out.append(storeString+"\n")
        #print(storeString)
    log=open("ipLog.txt","w")
    for line in out:
        log.write(line)
    log.close()

#Main code

while True:
    scanLocalNet()
    time.sleep(30)

