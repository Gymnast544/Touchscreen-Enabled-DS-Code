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
    ser = serial.Serial(comport)
    ser.baudrate = 115200

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

initSerial(chooseDevice())



mousepos  = 0, 0
mousestate = 1 #1 means not clicked, 0 means clicked







def getResponse():
    while ser.in_waiting == 0:
        pass
    for byte in ser.read():
        print(byte)
        return byte

def sendPos(xposlist):
    sendByte(30)
    numsent = 0
    while numsent<15:
        sendByte(xposlist[numsent]+50)
        numsent = getResponse()
    sendByte(68)


def sendMousePos(pos):
    pass

postry = [0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0]
sendPos(postry)

pygame.init()
size = width, height = 256, 256
screen = pygame.display.set_mode(size)
print("Setted up")
pygame.display.update()
"""
while True:
    pygame.display.update()
    events = False
    for event in pygame.event.get():
        events = True
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
            #released
    
"""
