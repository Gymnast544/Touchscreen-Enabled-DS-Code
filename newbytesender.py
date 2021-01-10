import serial
from serial.tools import list_ports
import time
from initlookups import *

import DSMplusreader
workfile = "workfile.dsm"
originalfile = "SoigNSMB.dsm"
DSMplusreader.parseFile(originalfile, workfile)

startline = 2600
"""
TAS protocol
PC: 50 (tell it we’re TASING)
PC: pollsperframe (currently only 4 is implemented)
PC: 65 or anything (65 signals that we’re starting without battery insertion, anything else signals we’re not)
RPLY: queue_size (80 for now)
RPLY: num in queue
PC: frame data transfer
Repeat last two steps until RPLY says 180 (buffer full)
PC: anything (signal starting)
Starts replaying
At the beginning of frame:
RPLY: 190 if touchscreen isn’t being spoofed, 189 if it is (timing is tight if we are spoofing touchscreen)
RPLY: # of frames in queue
RPLY: 191 whenever a poll is done
PC: responsible for sending frames at the right time depending on Replay device output
"""
    
def chooseDevice():
    serialdevices = []
    for index, serialport in enumerate(list_ports.comports()):
        print(str(index+1)+": "+serialport.description)
        serialdevices.append(serialport.device)
    serialindex = int(input("Choose the serial port to use (Enter the number) "))
    comport = serialdevices[serialindex-1]
    return comport

ser = None
def initSerial(comport):
    global ser
    print("Started serial")
    ser = serial.Serial(comport)
    print("Connected Serial")
    ser.baudrate = 115200
    print("Baudrate adjusted")

def closeSerial():
    global ser
    ser.close()

def sendByte(byteint):
    global ser
    ser.write([byteint])
def verifyDevice(comport):
    verified = False
    tempser = serial.Serial(comport)
    tempser.baudrate = 115200
    tempser.write(bytes(chr(100), 'utf-8'))
    starttime = time.time()
    while time.time()-starttime<.5 and verified==False:
        if tempser.in_waiting>0:
            read = tempser.read(1)
            if ord(read)==101:
                verified = True
                tempser.close()
                return True
    tempser.close()
    print("Verification status of "+comport+" is "+str(verified))
    return verified
    

def getLookupPos(xpos, ypos):
    found = False
    index = 0
    while not found:
        currentlookupx = xlookup[index]
        #print(currentlookup)
        if currentlookupx[0] == xpos:
            found = True
        index+=1
    found = False
    index = 0
    while not found:
        currentlookupy = ylookup[index]
        #print(currentlookup)
        if currentlookupy[0] == ypos:
            found = True
        index+=1
    return currentlookupx[1], currentlookupy[1]

def getResponse():
    while ser.in_waiting == 0:
        #print("waiting")
        pass
    for byte in ser.read():
        #print(byte, chr(byte))
        return byte

def drainSerial():
    ser.read(ser.in_waiting)

datastringsample = "|0|.............000 000 0|"
datastringsample2 = "|0|........P....191 128 0|"

byte1buttons = ["A", "B", "X", "Y", "L"] #A, B, X, Y, DPADLEFT
byte2buttons = ["R", "U", "D", "W", "E"] #DPADRIGHT, DPADUP, DPADDOWN, L shoulder (east), R shoulder (west)
byte3buttons = ["T", "S", "C", "P", "Z"] #sTart, Select, Cover (lid), Pen, PWR (On/Off)


def parseString(datastring):
    try:
        datafield = datastring.split("|")[2]
        touchdata = datafield[-9:]
        touchlist = touchdata.split()
        touchx = int(touchlist[0])
        touchy = int(touchlist[1])
        touchpen = int(touchlist[2])
    except:
        touchx = 0
        touchy = 0
        touchpen = 0
        #print("Error with '|' characters")
    #print(touchx, touchy, touchpen)

    byte1=0
    byte2=4
    byte3=2
    for (i, j) in enumerate(byte1buttons):
        if not (j in datastring):
            #this button is not being pressed
            byte1+=2**(i+3)
        else:
            #print(j)
            pass
    for (i, j) in enumerate(byte2buttons):
        if not(j in datastring):
            #this button is not being pressed
            byte2+=2**(i+3)
        else:
            #print(j)
            pass
    for (i, j) in enumerate(byte3buttons):
        if not(j in datastring or (j=="P" and touchpen==1)):#second check is if it's checking pen and touchpen is saying it's already pressed
            #this button is not being pressed
            byte3+=2**(i+3)
        else:
            #print(j)
            pass
    toSend = [byte1, byte2, byte3]
    xbytes, ybytes = getLookupPos(touchx, touchy)

    #print(xbytes, ybytes)

    byte4list = [0, 0, 0, xbytes[0], xbytes[1], xbytes[2], xbytes[3], xbytes[4]]
    byte5list = [0, 0, 1, xbytes[5], xbytes[6], xbytes[7], xbytes[8], xbytes[9]]
    byte6list = [0, 1, 0, xbytes[10], xbytes[11], xbytes[12], xbytes[13], xbytes[14]]
    #print([byte4list, byte5list, byte6list])
    
    byte7list = [0, 1, 1, ybytes[0], ybytes[1], ybytes[2], ybytes[3], ybytes[4]]
    byte8list = [1, 0, 0, ybytes[5], ybytes[6], ybytes[7], ybytes[8], ybytes[9]]
    byte9list = [1, 0, 1, ybytes[10], ybytes[11], ybytes[12], ybytes[13], ybytes[14]]


    bytelists = [byte4list, byte5list, byte6list, byte7list, byte8list, byte9list]

    for bytelist in bytelists:
        toAdd = 0
        for i in range(8):
            toAdd+=bytelist[i]*(2**i)
        toSend.append(toAdd)

    return toSend


def getAllRead():
    for i in range(ser.in_waiting):
        #ser.read()
        print(ser.read())

def transmitData(datastring):
    global currentline
    currentline+=1
    #print("Transmitting" +datastring)
    bytesToSend = parseString(datastring)
    drainSerial()
    #while(getResponse()!=15):
        #print("waiting on response of 15")
    sendByte(245)
    sendByte(bytesToSend[0])
    sendByte(bytesToSend[1])
    sendByte(bytesToSend[2])
    sendByte(255)
    for i in range(3, 9):
        sendByte(bytesToSend[i])#sends indexes 3-9 in the list
    sendByte(255)
    #probably want to add input verification, not for now though


#I think the appropriate amount to change by is 16


print("Initing serial")
initSerial(chooseDevice())
print("Serial Inited")



f = open(workfile, "r")
TASlines = []
for line in f:
    TASlines.append(line)
f.close()
currentline=0


for i in range(startline):
    TASlines.pop(0)
    currentline+=1

sendByte(50)
getResponse()
sendByte(4)


if "BATTERYPOWERON" in TASlines[0]:
    TASlines.pop(0)
    sendByte(69)
else:
    sendByte(65)
queue_size = getResponse()
print("Queue size is", queue_size)
filling_queue = True
print("Filling queue")
while(filling_queue):
    response = getResponse()
    print(response)
    if response == 180:
        filling_queue = False
    else:
        data = TASlines.pop(0)
        print(data)
        transmitData(data)
        print("Finished transmission")

input("Press enter to start")
sendByte(69)
running = True
tighttiming = False
numframes = 100
amountframesneeded = 0
while(running):
    response = getResponse()
    if response==230:
        running=False
    elif response<100:
        print(response, "Current line is", currentline)
        #print("There are "+str(response)+" frames left")
        numframes = response
        if numframes<queue_size:
            amountframesneeded = queue_size-numframes
            if amountframesneeded>3:
                amountframesneeded == 3
                #capping number of frames transmitted over a frame to 3
            if not tighttiming:
                for i in range(amountframesneeded):
                    transmitData(TASlines.pop(0))
                    amountframesneeded = amountframesneeded-1
    elif response == 189:
        #print("no tight timing")
        tighttiming = False
    elif response == 190:
        #print("tight timing")
        tighttiming = True
    elif response==191:
        #print("good time to send")
        if amountframesneeded>0 and tighttiming:
            transmitData(TASlines.pop(0))
            amountframesneeded = amountframesneeded-1
    

