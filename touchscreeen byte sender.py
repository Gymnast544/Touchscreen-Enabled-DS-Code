import pygame
import serial
from serial.tools import list_ports
import time
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
    ser.write(bytes(chr(byteint), 'utf-8'))
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

print("Initing serial")
initSerial(chooseDevice())
print("Serial Inited")


mousepos  = 0, 0
mousestate = 1 #1 means not clicked, 0 means clicked







def getResponse():
    while ser.in_waiting == 0:
        print("waiting")
        pass
    for byte in ser.read():
        print(byte)
        return byte

def sendPos(xposlist):
    ser.read(ser.in_waiting)
    print(xposlist, "sending pos")
    sendByte(30)
    numsent = 0
    while numsent<15:
        numsent = getResponse()
        sendByte(xposlist[numsent]+50)
        
    sendByte(68)


def sendMousePos(pos):
    pass

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
    print(toReturn)
    return toReturn

#I think the appropriate amount to change by is 16
    

postry = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
print("sending pos")

sendPos(postry)
time.sleep(.5)
sendPos(postry)

pygame.init()
size = width, height = 256, 256
screen = pygame.display.set_mode(size)
print("Setted up")
pygame.display.update()

sendByte(32)#just pen down


f = open("xlookup.txt", "w")
currentval = 0
xlookup = []

font = pygame.font.Font('freesansbold.ttf', 32) 

while True:
    pygame.display.update()
    events = False
    for event in pygame.event.get():
        events = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                xlookup.append([currentval, postry])
                postry = changeBits(postry, 64)
                sendPos(postry)
                print(len(postry))
            elif event.key == pygame.K_LEFT:
                postry = changeBits(postry, -64)
                xlookup.append([currentval, postry])
                sendPos(postry)
            elif event.key == pygame.K_UP:
                currentval = currentval+1
            elif event.key == pygame.K_DOWN:
                currentval = currentval-1
            elif event.key==pygame.K_x:
                f.write(str(xlookup))
                f.close()
            screen.fill((0, 0, 0))
            text = font.render(str(currentval), True, (255, 255, 255))
            screen.blit(text, (0, 0))
            
                
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            mousepos = event.pos
            mousestate = 0
            print("MOUSEDOWN", event.pos)
            sendByte(32)
            sendMousePos(event.pos)
            #clicked
        elif event.type == pygame.MOUSEBUTTONUP:
            mousestate = 1
            print("MOUSEUP")
            sendByte(33)
            sendMousePos(event.pos)
            #released
        elif event.type == pygame.MOUSEMOTION and (not mousestate):
            mousepos = event.pos
            print("MOVE", event.pos)
            sendMousePos(event.pos)
            #released"""
    

