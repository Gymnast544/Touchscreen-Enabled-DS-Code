import serial
from serial.tools import list_ports
import time
from initlookups import *
import win32api
import win32con
import win32gui
from pynput.mouse import Listener

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
    

initCapture()
print("Initing serial")
initSerial(chooseDevice())
print("Serial Inited")



mousepos  = 0, 0
mousestate = 1 #1 means not clicked, 0 means clicked
mousechange = True


sendByte(32)#just pen down
currentval = 0


def getCorrectedPos(inputx, inputy):
    win32gui.ShowWindow(windowcapture, win32con.SW_MAXIMIZE)
    window_x, window_y, width, height = getwindowcaptureproperties()
    print(window_x, window_y, width, height)
    window_y+=192#correcting for top screen
    height-=192
    x = inputx-window_x
    y = inputy-window_y
    if x<0:
        x=-1
    elif x>=width:
        x=-1
    if y<0:
        y=-1
    elif y>=height:
        y=-1
    if (x==-1 and mousepos[0]!=-1) or( y==-1 and mousepos[1]!=-1):
        #mouse is off the screen
        print("Using corrected pos override")
        mousestate = 1
        sendMousePos((0, 0))
    return x, y


def on_move(x, y):
    global mousepos, mousechange
    mousepos = getCorrectedPos(x, y)
    if mousestate == 0 and not(mousepos[0]==-1 or mousepos[1]==-1):
        sendMousePos(mousepos)

def on_click(x, y, button, pressed):
    global mousepos, mousestate, mousechange
    mousepos = getCorrectedPos(x, y)
    if pressed:
        mousestate = 0
    else:
        mousestate = 1
    if not(mousepos[0]==-1 or mousepos[1]==-1):
        sendMousePos(mousepos)  


with Listener(on_move=on_move, on_click=on_click) as listener:
    listener.join()

while True:
    pass

        
    

