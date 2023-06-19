


import CBstate 
mydir = CBstate.mydir
#import inversekinematics
import sys    
import pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 125) 
from subprocess import call                         

import time     
from math import sin, cos, atan2, sqrt, atan

import serial

axistorow8 = 96  # mm
servoonleft = True
#squaresize = 31    # mm
squaresize = 36 # mm
gripperfloatheight = 100
grippergrabheight = 30 
gripperoffset = 26
openamount = 37 #degrees
closeamount = 2 #degrees
graveyard = "i6"
msgcount = 0

if CBstate.SCARA:
    debugrobot = False
    axistorow8 = 35
    gripperfloatheight = 40
    grippergrabheight = -15
    gripperfloatheight = 230  # do not change
    grippergrabheight = -63
    halfway = (gripperfloatheight + grippergrabheight) / 2
    gripperoffset = 0  
    openamount = 50 
    closeamount = 15
   
    shank1 = 153.0
    shank2 = 161.0    
    totalarmlength = shank1 + shank2   
    elbow = 0
    oldelbow = 0

xmtrans = {
    "a": 3.5,
    "b": 2.5,
    "c": 1.5,
    "d": 0.5,
    "e": -0.5,
    "f": -1.5,
    "g": -2.5,
    "h": -3.5,
    "i": -4.5,
    "j": -5.5
}

xtrans = {
    "a": 0,
    "b": 1,
    "c": 2,
    "d": 3,
    "e": 4,
    "f": 5,
    "g": 6,
    "h": 7,
    "i": 8,
    "j": 9
}

pieceheights = {
    "p": 2.7,   
    "r": 3.0,
    "n": 3.2,   
    "b": 4.1,   
    "q": 4.6,   
    "k": 5.3    
}
maxpieceheight = 2.5    

piecewidths = {
    "p": 0,     
    "r": 3,
    "n": 0,
    "b": 3,
    "q": 4,
    "k": 4
}

gameresult = ("No result", "Checkmate! White wins", "Checkmate! Black wins", "Stalemate", "50 moves rule", "3 repetitions rule")
lastmovetype = (
    "Normal",
    "En passant available",
    "Capture en passant",
    "Pawn promoted",
    "Castle on king's side",
    "Castle on queen's side")

firsttime = 1

sp = 0

def waiter(dur):
    time.sleep(dur)
    
def receivemsg(sp):
    global msgcount
    msgcount += 1
    
    line=sp.read_until().decode('utf-8').rstrip()
    sp.flush()
    print(msgcount, line)
    
def scaraviastraight(xmm, adjymmint, zmm):
    global elbow, oldelbow
    
    oldelbow = elbow
    
    if xmm > 0 and adjymmint < totalarmlength:
        elbow = 0
    
    if xmm > 135:   
        elbow = 0
    
    if xmm < 0 and adjymmint < totalarmlength:
        elbow = 1

    if elbow != oldelbow:
        print ("elbow: " + str(elbow) + " oldelbow: " + str(oldelbow))
        
        gstring = "G1" + " X0" + " Y" + str(totalarmlength) + " Z" + str(zmm) + "\r"
        print (gstring)
        sp.write(gstring.encode())
        receivemsg(sp)
        

def movearmcoord (xmm, ymm, zmm):  
    adjymmint = int(ymm)+axistorow8
    theta = atan2(adjymmint, int(xmm))
    adjxmm = str(int(round(int(xmm) - (gripperoffset*cos(theta)))))   
    adjymm = str(int(round(adjymmint - (gripperoffset*sin(theta)))))  
    if CBstate.SCARA:
        armreach = sqrt((xmm*xmm) + (int(adjymmint)*int(adjymmint)))
        if armreach > totalarmlength:
            print ("Too far away! " + str(armreach))
        
        scaraviastraight(xmm, adjymmint, zmm)
        
    if CBstate.motorsareservos:
       
        theangles = inversekinematics.inversekinematics(sqrt((adjxmm * adjxmm) + (adjymm * adjymm)), zmm, 90 + (rtod * (atan(x/y))), 0, -90, 0)
       
        gstring = "A 10 " + theangles[1] + " " + theangles[0]  + " " + theangles[3] + theangles[2] + "\r"
        print (gstring)
    else:
        gstring = "G1" + " X" + adjxmm + " Y" + adjymm + " Z" + str(zmm) + "\r"
        print (gstring) 
    
    
    sp.flush()
    sp.reset_input_buffer()
    sp.write(gstring.encode())
    receivemsg(sp)
   

def opengripper(amount):
    adjamount = amount
    if servoonleft:
        adjamount = 90 - amount
    if CBstate.motorsareservos:
        mycode = "G0\r"
    else:
        mycode = "M5 T" + str(adjamount) + "\r"
    print ("Open gripper")
    sp.flush()
    sp.write(mycode.encode())
    receivemsg(sp)
    waiter(0.5)

def closegripper(amount, piecetype):
    adjamount = amount + piecewidths[piecetype]
    if servoonleft:
        adjamount = 90 - (adjamount)
    if CBstate.motorsareservos:
        mycode = "G1\r"
    else:
        mycode = "M3 T" + str(adjamount) + "\r"
    print ("Close gripper")
    sp.flush()
    sp.write(mycode.encode())
    receivemsg(sp)
    waiter(0.5)

def speaker(text):
    if True:
        
        engine.setProperty('voice', 'english_rp+f3')
        engine.say(text)
        engine.runAndWait()
    else:
        cmd_beg= 'espeak -ven+f4 -s100 '
        cmd_end= ' | aplay ' + mydir + 'Text.wav  2>/dev/null' 
        cmd_out= '--stdout >' + mydir + 'Text.wav ' 
        text = text.replace(' ', '_')
        call([cmd_beg+cmd_out+text], shell=True)
        call(["aplay", mydir + "Text.wav"])

    
def quitter():
    global sp
    if sp:
        if CBstate.SCARA:
            gohome()
        print ("reset all steppers")
        sp.flush()
        sp.write(("M18" + "\r").encode())
        receivemsg(sp)
        sp.close()               
        time.sleep(2)
        print ("Game ends")
        speaker ("Game ends. Thankyou for playing.") 
    engine.stop()
    sys.exit()
    

def pickuppiece(xmm, ymm, piecetype):
    global pieceheights
    opengripper(openamount)
    print("go down to pick up")
    movearmcoord (xmm, ymm, grippergrabheight + (pieceheights[piecetype]*10))  

    waiter(1)
    print (grippergrabheight)
    input ("press enter")
    movearmcoord (xmm, ymm, grippergrabheight) 
    closegripper(closeamount, piecetype)
    
    print("go up")
    
    movearmcoord (xmm, ymm, gripperfloatheight) 
    
def droppiece(xmm, ymm):
    
    print("go down to drop piece")
    
    movearmcoord (xmm, ymm, grippergrabheight + 3)  
    waiter(1.2)
    opengripper(openamount)
    
    print("go up")
    
    movearmcoord (xmm, ymm, gripperfloatheight) 
    
def takepiece (xmm, ymm, targetpiece):
    speaker("Take piece.")
    movearmcoord (xmm, ymm, gripperfloatheight)
    pickuppiece(xmm,ymm, targetpiece)
    gravex = (xmtrans[graveyard[0]] * squaresize)-20
    gravey = (8-int(graveyard[1])) * squaresize
    movearmcoord (gravex, gravey, gripperfloatheight)
    droppiece(gravex, gravey)
    gohome()

def iscastling (sourcesquarename):
    
    if CBstate.cbstate == 4:
        rsourcexmm = xmtrans["h"] * squaresize
        rsourceymm = (8-int("8")) * squaresize
        rtargetxmm = xmtrans["f"] * squaresize
        rtargetymm = (8-int("8")) * squaresize
    elif CBstate.cbstate == 5:
        rsourcexmm = xmtrans["a"] * squaresize
        rsourceymm = (8-int("8")) * squaresize
        rtargetxmm = xmtrans["d"] * squaresize
        rtargetymm = (8-int("8")) * squaresize
    else:
        return()
    print("Castling " + sourcesquarename)   
    movearmcoord (rsourcexmm, rsourceymm, gripperfloatheight)
    
    pickuppiece(rsourcexmm, rsourceymm, "r")
    movearmcoord (rtargetxmm, rtargetymm, gripperfloatheight)
    droppiece(rtargetxmm, rtargetymm,)
    opengripper(openamount)
    print("go up")
    movearmcoord (rtargetxmm, rtargetymm, gripperfloatheight)
    gohome()
    
def enpassant (targetxmm, targetymm):
    if CBstate.cbstate == 2:
        
        takepiece(targetxmm, targetymm - squaresize, 'p') 

def updateboard(source, target, boardbefore):
   
    sourcex = xtrans[source[0]]
    sourcey = 8-int(source[1])
    targetx = xtrans[target[0]]
    targety = 8-int(target[1])
    print (boardbefore)
    boardbefore[targety][targetx] = boardbefore[sourcey][sourcex] 
    boardbefore[sourcey][sourcex] = "." 
    print (boardbefore) 
    return (boardbefore)

def movepiece (sourcesquarename, targetsquarename, boardbefore):
    
    sourcexmm = xmtrans[sourcesquarename[0:1]] * squaresize
    sourceymm = (8 - int(sourcesquarename[1:2])) * squaresize
    
    targetxmm = xmtrans[targetsquarename[0:1]] * squaresize
    targetymm = (8 - int(targetsquarename[1:2])) * squaresize
    
   
    sourcex = xtrans[sourcesquarename[0]]
    sourcey = 8-int(sourcesquarename[1])
    targetx = xtrans[targetsquarename[0]]
    targety = 8-int(targetsquarename[1])
    
    if boardbefore[targety][targetx] != ".":        
        
        print("Take piece!")
        takepiece(targetxmm, targetymm, boardbefore[targety][targetx].lower())      
    print ("sourcex= ", sourcex)
    
    movearmcoord (sourcexmm, sourceymm, gripperfloatheight)
    sourcepiece = boardbefore[sourcey][sourcex].lower()
    print("sourcepiece " + sourcepiece)

    pickuppiece(sourcexmm, sourceymm, sourcepiece)
    
    movearmcoord (targetxmm, targetymm, gripperfloatheight)

    droppiece(targetxmm, targetymm) 
    print("go home")
    gohome()
    
    iscastling(sourcesquarename)
    enpassant (targetxmm, targetymm) 

def calibrategripper():
    while True:
        angle = input("Provide angle in degrees, or q:")
        if angle == "q":
            quitter()
        opengripper(angle)
        
def gohome():
    if CBstate.SCARA:
        
        scaraviastraight(totalarmlength, 0, gripperfloatheight)
        gstring = "G1" + " X" + str(totalarmlength) + " Y0" + " Z" + str(gripperfloatheight) + "\r"
        waiter(1.2)
        print (gstring) 
        sp.flush()
        
        sp.write(gstring.encode())
        receivemsg(sp)
        time.sleep(0.2)
        receivemsg(sp)
    else:
        movearmcoord (0, -10+gripperoffset, 180)

def initsteppers():
    time.sleep(0.2)
    sp.write(("G28" + "\r").encode())   
    time.sleep(0.2)
    receivemsg(sp)
    time.sleep(0.2)
    receivemsg(sp)
    
def steppers_on():
    input("Press Enter to switch on steppers and start game")
    sp.write(("M17" + "\r").encode())  
    time.sleep(0.2)
    receivemsg(sp)
    time.sleep(0.2)
    receivemsg(sp)
def init():
    global sp
    try:
        sp = serial.Serial(CBstate.serialport, 9600, timeout=2.0)
        sp.reset_input_buffer()                
    except serial.SerialException as e:
        print("No serial port")
        print (e)
        quitter()
    time.sleep(0.2)
    
    try:
        print ("Start")        
        receivemsg(sp)
        receivemsg(sp)
        calirob = input("Calibrate robot manually? y/n")
        if calirob == "y":
            print ("Calibrate robot now ...")
            initsteppers()   
            steppers_on()    

            if CBstate.SCARA:
                gohome()   
                gstring = "G1" + " X0" + " Y" + str(totalarmlength) + " Z" + str(gripperfloatheight) + "\r"
                sp.write(gstring.encode())
                receivemsg(sp)
            else:
                movearmcoord (0, (squaresize*3.5), grippergrabheight)
            input("Adjust robot position slightly if not in centre of board. Press Enter to continue")
        gohome()

                      
    except KeyboardInterrupt:
        quitter()   
    


