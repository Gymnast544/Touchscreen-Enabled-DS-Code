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

def getResponse():
    while ser.in_waiting == 0:
        #print("waiting")
        pass
    for byte in ser.read():
        #print(byte)
        return byte

def sendPos(xposlist, yposlist):
    ser.read(ser.in_waiting)
    #print(xposlist, "sending pos")
    sendByte(30)
    numsent = 0
    running = True
    while running:
        response = getResponse()
        if response == 16:
            running = False
        else:
            numsent = response
            sendByte(xposlist[numsent]+50)
        
    sendByte(68)
    ser.read(ser.in_waiting)
    sendByte(31)
    numsent = 0
    running = True
    while running:
        response = getResponse()
        if response == 16:
            running = False
        else:
            numsent = response
            sendByte(yposlist[numsent]+50)
        
    sendByte(68)


def sendLookupPos(xpos, ypos):
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
    sendPos(currentlookupx[1], currentlookupy[1])
    
def changeBits(poslist, amount):
    string = ""
    for bit in poslist:
        string=string+str(bit)
    intval = int(string, 2)
    intval = intval+amount
    if intval<0:
        intval = 0
    string = "{0:b}".format(intval)#converting it back to binary
    string = "0"*(16-len(string))+string#padding with 0s to get to 16 bits
    toReturn = []
    for bit in string:
        toReturn.append(int(bit))
    #print(toReturn)
    return toReturn


def sendMousePosOld(pos):
    sendLookupPos(pos[0], pos[1])

def sendMousePos(pos):
    stringToSend = mousePosToLine(pos[0], pos[1])
    transmitData(stringToSend)

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

def drainSerial():
    ser.read(ser.in_waiting)

datastringsample = "|0|.............000 000 0|"
datastringsample2 = "|0|........P....191 128 0|"

byte1buttons = ["A", "B", "X", "Y", "L"] #A, B, X, Y, DPADLEFT (west)
byte2buttons = ["R", "U", "D", "W", "E"] #DPADRIGHT (east), DPADUP, DPADDOWN, L shoulder, R shoulder
byte3buttons = ["T", "S", "C", "P", "O"] #sTart, Select, Cover (lid), Pen, PWR (On/Off)


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
        print("Error with '|' characters")
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

def mousePosToLine(x, y):
    if not mousestate:
        return "||P "+str(x).zfill(3)+" "+str(y).zfill(3)+" 0|"
    else:
        return "|| "+str(x).zfill(3)+" "+str(y).zfill(3)+" 0|"

def getAllRead():
    for i in range(ser.in_waiting):
        #ser.read()
        print(ser.read())

def transmitData(datastring):
    #print("Transmitting" +datastring)
    bytesToSend = parseString(datastring)
    drainSerial()
    while(getResponse()!=15):
        pass
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



mousepos  = 0, 0
mousestate = 1 #1 means not clicked, 0 means clicked

pygame.init()
size = width, height = 256, 192
screen = pygame.display.set_mode(size)
print("Setted up")
pygame.display.update()

sendByte(32)#just pen down


#f = open("ylookup.txt", "w")
currentval = 0
#ylookup = []

font = pygame.font.Font('freesansbold.ttf', 32)

while True:
    pygame.display.update()
    #pygame.clock.tick(30)
    events = False
    for event in pygame.event.get():
        events = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            mousepos = event.pos
            mousestate = 0
            #print("MOUSEDOWN", event.pos)
            #sendByte(32)
            sendMousePos(event.pos)
            #clicked
        elif event.type == pygame.MOUSEBUTTONUP:
            mousepos = event.pos
            mousestate = 1
            sendMousePos(event.pos)
            #print("MOUSEUP")
            #sendByte(33)
            #released
        elif event.type == pygame.MOUSEMOTION and (not mousestate):
            mousepos = event.pos
            #print("MOVE", event.pos)
            sendMousePos(event.pos)
            #released
        
    

