import pygame
import serial
from serial.tools import list_ports
import time
from initlookups import *
clock = pygame.time.Clock()

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
    print("Baudrate adjusted")

def closeSerial():
    global ser
    ser.close()

def sendByte(byteint):
    global ser
    #print("Sending", byteint)
    ser.write(bytes(chr(byteint), 'utf-8'))
    
def verifyDevice(comport):
    verified = False
    tempser = serial.Serial(comport)
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
        #print(byte)
        return byte


datastringsample = "|0|.............000 000 0|"

byte1buttons = ["A", "B", "X", "Y", "W"] #A, B, X, Y, DPADLEFT (west)
byte2buttons = ["E", "U", "D", "L", "R"] #DPADRIGHT (east), DPADUP, DPADDOWN, L shoulder, R shoulder
byte3buttons = ["T", "S", "C", "P", "O"] #sTart, Select, Cover (lid), Pen, PWR (On/Off)


def parseString(datastring):
    datafield = datastring.split("|")[2]
    touchdata = datafield[-9:]
    touchlist = touchdata.split()
    touchx = int(touchlist[0])
    touchy = int(touchlist[1])
    touchpen = int(touchlist[2])

    byte1=0
    byte2=4
    byte3=2
    for (i, j) in enumerate(byte1buttons):
        if not (j in datastring):
            #this button is being pressed
            byte1+=2**(i+3)
        else:
            #print(j)
            pass
    for (i, j) in enumerate(byte2buttons):
        if not(j in datastring):
            #this button is being pressed
            byte2+=2**(i+3)
        else:
            #print(j)
            pass
    for (i, j) in enumerate(byte3buttons):
        if not(j in datastring or (j=="P" and touchpen==1)):
            #this button is being pressed
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
  
print(parseString(datastringsample))



def transmitData(datastring):
    bytesToSend = parseString(datastring)
    sendByte(245)
    sendByte(bytesToSend[0])
    sendByte(bytesToSend[1])
    sendByte(bytesToSend[2])
    sendByte(255)
    for i in range(3, 9):
        sendByte(bytesToSend[i])#sends indexes 3-9 in the list
    sendByte(255)
    #probably want to add input verification, not for now though
    

print("Initing serial")
initSerial(chooseDevice())
print("Serial Inited")
print(ser.in_waiting)




timelist = []
print("Starting")
for i in range(1000):
    starttime = time.time()
    transmitData(datastringsample)
    timelist.append(time.time()-starttime)
    #print("Done", i)
numsum = 0
for i in timelist:
    numsum = numsum+i


print(numsum/len(timelist))



