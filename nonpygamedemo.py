import serial
from serial.tools import list_ports
import time
from initlookups import *
import win32api
import win32con
import win32gui
from pynput.mouse import Listener
import pygame
pygame.init()



buttontochar = {0:"B", 1:"A", 2:"Y", 3:"X", 4:"W", 5:"E", 7:"T", 6:"S", 12:"C"}


def initjoysticks():
    controllers=[]
    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        if joystick.get_name()=="Wireless Controller" and joystick.get_numaxes()==6 and joystick.get_numbuttons()==14 and joystick.get_numhats()==1:
            print("Valid controller")
        controllers.append(joystick)

    print("Press cross on the desired joystick")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type==pygame.JOYBUTTONDOWN:
                print(event.button)
                if event.button == 1 or event.button==0:
                    if event.button==1:
                        global buttontochar
                        buttontochar = {0:"Y", 1:"B", 2:"A", 3:"X", 4:"W", 5:"E", 9:"T", 8:"S", 12:"C"}
                    joystick = event.joy
                    for controller in controllers:
                        if controller.get_id()!=joystick:
                            controller.quit()
                            #de-inits all irrelevant controllers
                    running = False


def chooseDevice():
    serialdevices = []
    while len(serialdevices)==0:
        for index, serialport in enumerate(list_ports.comports()):
            print(str(index+1)+": "+serialport.description)
            serialdevices.append(serialport.device)
        if len(serialdevices) == 1:
            serialindex = 0
        elif len(serialdevices)>1:
            serialindex = int(input("Choose the serial port to use (Enter the number) "))
        else:
            input("No devices found, press enter to try again")
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
sendingmousepos = False
def sendMousePos(pos):
    global sendingmousepos
    if not sendingmousepos:
        sendingmousepos = True
        stringToSend = mousePosToLine(pos[0], pos[1])
        transmitData(stringToSend)
        sendingmousepos = False

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
    buttonstring = ""
    for char in charspressed:
        buttonstring = buttonstring+char
    if not mousestate:
        return buttonstring+"||P "+str(x).zfill(3)+" "+str(y).zfill(3)+" 0|"
    else:
        return buttonstring+"|| "+str(x).zfill(3)+" "+str(y).zfill(3)+" 0|"

def getAllRead():
    for i in range(ser.in_waiting):
        #ser.read()
        print(ser.read())

def transmitData(datastring, wait=True):
    #print("Transmitting" +datastring)
    bytesToSend = parseString(datastring)
    drainSerial()
    if wait:
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


# DS CAPTURE INPUT
def windowEnumerationHandler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))
    
global window_x, window_y, window_w, window_h, windowcapture
def getwindowproperties(hwnd):
    print(hwnd)
    rect = win32gui.GetWindowRect(hwnd)
    window_x = rect[0]
    window_y = rect[1]
    window_w = rect[2] - window_x
    window_h = rect[3] - window_y
    return window_x, window_y, window_w, window_h, windowcapture

def getwindowcaptureproperties():
    global windowcapture
    x, y, x1, y1 = win32gui.GetClientRect(windowcapture)
    x, y = win32gui.ClientToScreen(windowcapture, (x, y))
    x1, y1 = win32gui.ClientToScreen(windowcapture, (x1 - x, y1 - y))
    return x, y, x1, y1

def setForeground():
    win32gui.SetForegroundWindow(windowcapture)

d = None
windowcapture = None

def initCapture():
    global windowcapture
    foundwindow = False
    while foundwindow == False:
        #Initializing stuff for finding the top window
        results = []
        top_windows = []
        win32gui.EnumWindows(windowEnumerationHandler, top_windows)
        for i in top_windows:
            #print(i)
            if "DS Capture" in i[1]:
                #print(getwindowproperties(i[0]))
                if getwindowproperties(i[0])[3]>getwindowproperties(i[0])[2]:
                    #checks if the window is tall, not wide (there's two DS Capture windows, the tall one is the correct one)
                    print("Found the frame named \" DS Capture\"")
                    windowcapture = i[0]
                    win32gui.ShowWindow(i[0],5)
                else:
                    print("DS Capture found, but it didn't fit the requirements. It seems like there might be something up. This might be just the skinny window instead of the tall one selected (the one for recording) This might be useless")
        #sets the top window to DS Capture. If it's not found then it prompts the user to open it up
        try:
            setForeground()
            foundwindow = True
        except:
            input(""""There was an error
A frame with the name \"DS Capture\" wasn't found
This usually means you forgot to open it\nPress enter to try again""")
    #Doing some stuff to properly get the window rect (normal method doesn't do it right)
    print(getwindowcaptureproperties())
    
initjoysticks()
initCapture()
print("Initing serial")
initSerial(chooseDevice())
print("Serial Inited")



mousepos  = 0, 0
mousestate = 1 #1 means not clicked, 0 means clicked
statechange = True
if statechange:
    print("STATECHANGE")


sendByte(32)#just pen down
currentval = 0


def getCorrectedPos(inputx, inputy):
    #win32gui.ShowWindow(windowcapture, win32con.SW_MAXIMIZE)
    window_x, window_y, width, height = getwindowcaptureproperties()
    #print(window_x, window_y, width, height)
    scalefactor=height/384
    correctedwidth = 256*scalefactor
    correctedwindowx = window_x+int((width-correctedwidth)/2)

    window_y+=height*.5
    height-=height*.5
    #correcting for top screen
    x = int((inputx-correctedwindowx)/scalefactor)
    y = int((inputy-window_y)/scalefactor)
    #print(x, y, scalefactor, width, correctedwindowx, correctedwidth)
    if x<0:
        x=-1
    elif x>=256:
        x=-1
    if y<0:
        y=-1
    elif y>=192:
        y=-1
    if (x==-1 and mousepos[0]!=-1) or( y==-1 and mousepos[1]!=-1):
        #mouse is off the screen
        print("Using corrected pos override")
        mousestate = 1
        setFlag()
    return x, y

def on_move(x, y):
    global mousepos, statechange
    mousepos = getCorrectedPos(x, y)
    if mousestate == 0 and not(mousepos[0]==-1 or mousepos[1]==-1):
        setFlag()

def on_click(x, y, button, pressed):
    #no longer being used due to dualshock support
    global mousepos, mousestate, statechange
    mousepos = getCorrectedPos(x, y)
    if pressed:
        mousestate = 0
    else:
        mousestate = 1
    if not(mousepos[0]==-1 or mousepos[1]==-1):
        setFlag()

def setFlag():
    global statechange
    statechange = True
    #print(statechange)

#on_click=on_click - use this as a param in the above function to enable click support
print("Starting listener")
Listener(on_move=on_move, on_click=on_click).start()

"""
with  as listener:
    listener.start()"""

possiblebuttons = list(buttontochar)
chartobutton = {v: k for k, v in buttontochar.items()}
possiblechars = list(chartobutton)
charspressed = []
while True:
    for event in pygame.event.get():
        if event.type == pygame.JOYBUTTONDOWN:
            print("Button down", event.button)
            if event.button == 13:#touchpad click
                mousestate = 0
                statechange = True
            elif event.button == 12:#cover
                transmitData("C", wait=False)
                closed = True
                while closed:
                    for event in pygame.event.get():
                        if event.type == pygame.JOYBUTTONDOWN:
                            if event.button == 12:
                                transmitData("", wait=False)
                                closed = False
            elif event.button in possiblebuttons:
                print(charspressed)
                if not (buttontochar[event.button] in charspressed):
                    print("Adding char")
                    charspressed.append(buttontochar[event.button])
                    print(charspressed)
                    statechange = True
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == 13:#touchpad click
                mousestate = 1
                statechange = True
            elif event.button in possiblebuttons:
                if (buttontochar[event.button] in charspressed):
                    try:
                        charspressed.pop(charspressed.index(buttontochar[event.button]))
                        statechange = True
                    except:
                        print("Error removing from list")
        elif event.type == pygame.JOYHATMOTION:
            print(event.value)
            charstoadd = []
            charstoremove = []
            if event.value[0] == -1:
                charstoadd.append("L")
                charstoremove.append("R")
            elif event.value[0] == 1:
                charstoremove.append("L")
                charstoadd.append("R")
            elif event.value[0] == 0:
                charstoremove.append("L")
                charstoremove.append("R")
                
            if event.value[1] == -1:
                charstoadd.append("D")
                charstoremove.append("U")
            elif event.value[1] == 1:
                charstoremove.append("D")
                charstoadd.append("U")
            elif event.value[1] == 0:
                charstoremove.append("D")
                charstoremove.append("U")
            for char in charstoadd:
                if not (char in charspressed):
                    charspressed.append(char)
            for char in charstoremove:
                if char in charspressed:
                    try:
                        charspressed.pop(charspressed.index(char))
                    except:
                        print("Error removing char")
            statechange = True
            
    if statechange:
        if mousepos[0]<0 or mousepos[1]<0:  
            sendMousePos((0, 0))
        else:
            sendMousePos(mousepos)
        statechange = False

        
    

