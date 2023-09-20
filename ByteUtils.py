"""
Utility file for reading, writing, parsing and printing byte arrays as hexadecimal strings.
Libraries exist to do this already, but I wrote it myself as a learning exercise. 
"""

import sys

def PrintHexAsDex(inp):
    for i in range(0,len(inp)):
        sys.stdout.write(str(int(inp[i])) + ' ')
        if((i+1)%16 == 0):
            sys.stdout.write('\n')
 
def ReadHexDump(path):
    f = open(path,"rb")
    data = f.read()
    f.close()
    return bytearray(data)

def WriteHexDump(data,path):
    f = open(path,"wb")
    data = f.write(data)
    f.close()

def ReadAsHexShort(code):
    ReadAsHex(code,0,len(code))
    
def ReadAsHex(dump,start=0,length=-1,blocklength = 1):
    if(length == -1):
        length = len(dump)
    asHex = [('%02x'%i).upper() for i in dump[start:start+length]]
    if(blocklength == 1):
         print((' '.join(asHex)))
    else:
        for i in range(0,len(asHex)):
                sys.stdout.write(asHex[i])
                if i%blocklength == 1:
                    sys.stdout.write(' ')
    return asHex

def ReadAsText(dump,start,length,blocklength = 1,paddingLength=0,printWhileReading = True):
    asChar = "".join([chr(i) for i in dump[start:start+length]])
    if(printWhileReading):
        padding = "".join([' ' for i in range(0,paddingLength)])
        if(blocklength == 1):
             print((padding.join(asChar)))
        else:
            for i in range(0,len(asChar)):
                    sys.stdout.write(asChar[i])
                    if i%blocklength == 1:
                        sys.stdout.write(' ')
    return asChar
                    
def WriteHex(dump,start,data):
    for i in range(0,len(data)):
        dump[start+i] = data[i]


def CompareBytes(b1,b2):
    if(len(b1) != len(b2)):
        print("different lengths.")
        print("b1 is" + str(len(b1)))
        print("b2 is" + str(len(b2)))
        return
    diffs = list()
    for i in range(0,len(b1)):
        if(b1[i] != b2[i]):
            diffs.append(hex(i))
    return diffs

def StringListToHex(strList):
    return [int(s,16) for s in strList]