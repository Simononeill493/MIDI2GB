"""
Main program. Assembles and plays a Game Boy song from the provided MIDI file. 
Takes three arguments: the MIDI file to parse, a number from 1-255 which control's the song's tempo,
and a number which controls the pitch. 
"""

import sys 
import re
import math
from collections import Counter 
import subprocess
from ByteUtils import *

MIN_PITCH = -6
MAX_PITCH = 2

#http://www.music.mcgill.ca/~ich/classes/mumt306/StandardMIDIfileformat.html#BMA1_
EVENT_NOTE_OFF = 0x80
EVENT_NOTE_ON = 0x90
EVENT_CONTROL_CHANGE = 0xB0
EVENT_PROGRAM_CHANGE = 0xC0

STRING_NOTE_OFF = "Note Off"
STRING_NOTE_ON = "Note  On"
STRING_CONTROL_CHANGE = "Control Change"
STRING_PROGRAM_CHANGE = "Program Change"
STRING_EVENT_UNKNOWN = "Unknown"

HighestNoteIndex = 38


""" Contains all the tracks of a single MIDI file, plus the file header. 
There's also some metadata relating to tempo and timing, which this program doesn't use."""
class MidiFile:
    header = -1
    metricalTiming = -1
    globalTempoTrack = -1
    tracks = -1
    
    def __init__(self, header, metricalTiming,globalTempoTrack,tracks):
        self.header = header
        self.metricalTiming = metricalTiming
        self.globalTempoTrack = globalTempoTrack
        self.tracks = tracks
        
    def PrintTracks(self):
        for i in range(0,len(self.tracks)):
            track = self.tracks[i]
            highestNote = max([e.note for e in track.events])
            lowestNote = min([e.note for e in track.events])
            outOfBoundsCount = (len([e for e in track.events if e.note>HighestNoteIndex or e.note<0]))
            print(str(i) + "\t" + track.title)
            print("Length: " + str(len(track.events)))
            print("Highest:" + str(highestNote))
            print("Lowest: " + str(lowestNote)) 
            print("Num out of bounds: " + str(outOfBoundsCount))
            print('\n')
            
    def MergeTracks(self):
        title = ""
        events = list()
        for t in self.tracks:
            events = events + t.events
            title = title + t.title + ", "
        list.sort(events,key=lambda x: x.timeStamp)
        self.tracks = [MidiTrack(title,events)]
        
    def RemoveDrums(self):
        """ Can't map drum tracks to a melody, unless you want your songs turned into hardcore Eurobeat.
        They should probaly be implemented by the Game Boy's noise channel. 
        I haven't done that yet, so I just get rid of drums for now."""
        
        drums = [t for t in self.tracks if "drum" in t.title.lower()]
        print("Removing " + str(len(drums)) + " drum tracks.")
        
        self.tracks = [t for t in self.tracks if "drum" not in t.title.lower()]
        #Yes, it's a hack. A better solution would be to check the patch number
        #(http://www.music.mcgill.ca/~ich/classes/mumt306/StandardMIDIfileformat.html#BM1_4)
        
    def RemoveEmptyTracks(self):
        self.tracks = [t for t in self.tracks if len(t.events) > 0]
            

    def PeekTrack(self,index,maxlength):
        print("Peeking track: " + self.tracks[index].title)
        length = min(maxlength,len(self.tracks[index].events))
        
        for i in range(0,length):
            print(self.tracks[index].events[i])

"""Single track of a MIDI. Usually a single instrument."""
class MidiTrack:
    title = ""
    events = []
    lastProgramChangeTime = 0
    def __init__(self, title, events):
        self.title = title
        self.events = events
        
        pcs = sorted((e for e in events if e.eventType == STRING_PROGRAM_CHANGE), key=lambda e: e.timeStamp)
        if(len(pcs) > 0):
            self.lastProgramChangeTime = pcs[0].timeStamp
        


"""MIDI event. Beginning of note, end of note, etc. 
We don't do sustained notes, so we're only really interested in note beginnings."""
class MidiEvent:
    eventType = "none"
    note = -1
    deltaTime = -1
    timeStamp = -1
    
    eventBytes = []
    def __init__(self, eventType, note):
        self.eventType = eventType
        self.note = note
    def __str__(self):
        return "TimeStamp:" + str(self.timeStamp) + "\t\t" + str(self.eventType) + "\t\tNote:" + str(self.note) + "\t\tDeltaTime:" + str(self.deltaTime)

""" Parse an entire MIDI blob."""
def ReadRawMidiData(dump):
    print("Reading MIDI file.")
    txt = ReadAsText(dump,0,len(dump),printWhileReading=False)
    splits = re.split('MThd|MTrk',txt)
    splits = [[ord(s) for s in split] for split in splits if len(split) > 0]
    header = splits[0][4:10]
    print(str(header[3]) + " tracks discovered.") 
    
    
    if(header[1] == 2):
        print("Midi Header format 2: cannot parse.")
        return False
    elif(header[1] == 1 or header[1] == 0):
        metricalTiming = (header[4]*256)+header[5]
        globalTempoTrack = splits[1]
        
        tracks = list()
        startOfTracks = 1
        #if(header[1] == 0):
        #    startOfTracks = 1
        #startOfTracks = 1   
        for i in range(startOfTracks,len(splits)):
            track = splits[i][5:]
            
            titleLength = track[2]
            title = "".join([chr(c) for c in track[3:3+titleLength]])
            trackWithoutTitle = track[4+titleLength:]
            trackEvents = ReadMidiTrack(trackWithoutTitle)
            
            track = MidiTrack(title,trackEvents)
            tracks.append(track)
            
        return MidiFile(header,metricalTiming,globalTempoTrack,tracks)
    else:
        print("Unknown header type " + str(header[1]) + ", could not make midi object.")


""" Parse an individual MIDI track."""
def ReadMidiTrack(track):
    events = []
    cursor = 0
    totalTime = 0
    while(cursor<len(track)):
        (event,cursor)= ReadNextEvent(track,cursor)
        prev = totalTime
        totalTime += event.deltaTime
        event.timeStamp = prev

        events.append(event)
    return events



"""Parses a single MIDI event, starting at the position provided.
Returns the location of the next event, or the end of the track."""
def ReadNextEvent(track,start=0):
    eventType = ''
    cursor = start
    firstNibble = track[start] & 0xF0
    
    (event,cursor) = SwitchOnEvent(track,cursor,firstNibble)
    (deltaTime,length) = ResolveDeltaTime(track,start=cursor)
    cursor+=length
    
    event.deltaTime = deltaTime
    event.eventBytes = track[start:cursor]
    
    return (event,cursor)

""" Creates the MidiEvent object and moves cursor forward"""
def SwitchOnEvent(track,cursor,firstNibble):
    if(firstNibble == EVENT_NOTE_OFF):    #Note off
        return (MidiEvent(STRING_NOTE_OFF,track[cursor+1]),cursor+3)
    elif(firstNibble == EVENT_NOTE_ON):    #Note off    
        return (MidiEvent(STRING_NOTE_ON,track[cursor+1]),cursor+3)
    elif(firstNibble == EVENT_PROGRAM_CHANGE):    #Program Change    
        return (MidiEvent(STRING_PROGRAM_CHANGE,-1),cursor+2)
    elif(firstNibble == EVENT_CONTROL_CHANGE):    #Control Change    
        return (MidiEvent(STRING_CONTROL_CHANGE,-1),cursor)
    else: #We don't care about other events
        return(MidiEvent(STRING_EVENT_UNKNOWN + " (" + str('%x' % firstNibble) + ")",-1),cursor)
        
""" Decodes the variable-length time format of a MIDI event.
http://www.music.mcgill.ca/~ich/classes/mumt306/StandardMIDIfileformat.html#BM1_1""" 
def ResolveDeltaTime(track,start=0):
    track = track[start:]
    numBytes = 0
    for num in track:
        numBytes = numBytes+1
        if(num<128):
            break
    totalDeltaTime = 0
    
    trueList = track[0:numBytes]


    trueList.reverse()
    for i in range(0,numBytes):
        bitOff = trueList[i] & 0x7F
        factor = int(math.pow(128,i))
        totalDeltaTime = totalDeltaTime + (bitOff * factor)
        
    return (totalDeltaTime,numBytes)

def ForEachTrack(midi,eventsFunction):
    for track in midi.tracks:
        track.events = eventsFunction(track.events)
        

def SetStartTimeToFirstProgramChange(midi):
    for track in midi.tracks:
        for event in track.events:
            event.timeStamp = event.timeStamp - track.lastProgramChangeTime

def FilterToNoteOnOnly(events):
        return [e for e in events if e.eventType==STRING_NOTE_ON]
    
def FilterOutSimultaneousNotes(events):
    return [e for e in events if e.deltaTime>0]

"""Lowers the song's pitch so that the lowest note is at index 0, which is a C.
We only have a range of about three octaves, so we need to use everything we have!"""
def NormalizeNotes(events):
    minNote = min([e.note for e in events])
    for e in events:
        e.note-=minNote
    return events


def SetSongPitch(midi,pitchOffset):
    if(pitchOffset == 0):
        return
    elif(pitchOffset > 0 and pitchOffset <= 4):
        for i in range(0,pitchOffset):
            ForEachTrack(midi,PushNotesUpHalfOctave)
    elif(pitchOffset < 0 and pitchOffset >= -4):
        for i in range(0,abs(pitchOffset)):
            ForEachTrack(midi,PushNotesDownHalfOctave)
    else:
        print("Invalid pitch offset: " + str(pitchOffset))


def WrapNotesDownOneOctave(events):
    return WrapNotes(events,-12)
def WrapNotesUpOneOctave(events):
    return WrapNotes(events,12)

def PushNotesDownOneOctave(events):
    return PushNotes(events,-12)
def PushNotesUpOneOctave(events):
    return PushNotes(events,12)

def PushNotesDownHalfOctave(events):
    return PushNotes(events,-6)
def PushNotesUpHalfOctave(events):
    return PushNotes(events,6)

def WrapNotes(events,amount=0):
    return PushNotes(events,amount,36)

def PushNotes(events,amount=0,pushingFactor=12):
    for e in events:
        e.note+=amount
        while(e.note<0):
            e.note+=pushingFactor
        while(e.note>HighestNoteIndex):
            e.note-=pushingFactor
    return events

""" Recalculate the time gaps between notes after removing irrelevant MIDI events."""
def RecalculateDeltaTime(events):
    for i in range(0,len(events)-1):
        event = events[i]
        nextTimeStamp = events[i+1].timeStamp
        event.deltaTime = nextTimeStamp-event.timeStamp
    events[len(events)-1].deltaTime = next(e.deltaTime for e in events if e.deltaTime>0)
    return events

""" Try to downscale the time gaps between notes. 
Ideally we want to divide by the greatest common divisor - ie, if all time gaps are 100 or 200 units, we want to divide by 100.
Smaller intervals are neater, and easier to work with when messing with the song's tempo."""
def DivideDeltaTime(events):
    factor = GetDividingFactor(events)
    for e in events:
        e.deltaTime = round(e.deltaTime/factor)
    return events

def GetDividingFactor(events):    
    deltaTimes = [e.deltaTime for e in midi.tracks[0].events if e.deltaTime>0]
    mostCommon = Counter(deltaTimes).most_common(1)[0][0] 
    smallerThanMostCommonDeltaTimes = [t for t in set(deltaTimes) if t<mostCommon]
    if(len(smallerThanMostCommonDeltaTimes) == 0):
        return mostCommon
    factors = [f for f in factorlist(mostCommon) if f<(min(smallerThanMostCommonDeltaTimes)*1.2) and f>=mostCommon/16]
    
    ratiosTotal = dict()
    for f in factors:
        ratiosTotal[f] = 0
        for s in smallerThanMostCommonDeltaTimes:
            ratio = max([f,s])/min([f,s])
            ratio = ratio-math.floor(ratio)
            ratiosTotal[f]+=ratio
            
    if(len(ratiosTotal) == 0):
        return 1
    #print("Ratios total: " + str(len()))

    ratiosSorted = sorted(ratiosTotal.items(), key = lambda x: (x[1], -x[0]))
    return ratiosSorted[0][0]

def factorlist(n):  
    output = list()
    for i in range(2, int(n/2)+1):
        if n % i == 0:
            output.append(i)
    return output

"""Converts the track into a format that can be injected into a Game Boy ASM file.
The format is extremely simple. Every note is represented by a pair of hexidecimal integers.
The first integer is the pitch, starting at C and working upwards. The second integer
is the delay before playing the next note. This delay is proportional to the speed
argument in RunSong(). 
If the Game Boy program reads a 255 for the note's pitch, it exits."""
def WriteTrackInAsmFormat(track):
    output = ''
    output+='\t'
    output+="db "
    for e in track.events:
        byteNote = '%02x'%(e.note)
        byteDeltaTime = '%02x'%(e.deltaTime)
        if(len(byteNote)>2):
            byteNote = "FF"
        if(len(byteDeltaTime)>2):
            byteDeltaTime = "FF"

        output+="&"
        output+=byteNote.upper()
        output+=",&"
        output+=byteDeltaTime.upper()
        output+=","
    output+="255,255"
    return output

def WriteTrackInPlaintext(track):
    song = ""
    for e in track.events:
        song+=(str(e.note)+ "," + str(e.deltaTime) + '\n')
    return song

"""Executes a batch script which compiles and plays the song. You need VASM and an emulator. An example script is provided,
but if you're using another emulator (or a different version of VASM) you can swap in your own.
The delay argument is a hex number in the range 00-FF which decides the tempo of the song.
Larger delay means a bigger gap between notes, and thus a slower song.
The actual delay between notes is proportional to the *square* of this value, so keep that in mind if you're adjusting it. Halving
the delay won't double the speed of the song, it'll quadruple it. 
"""
def RunSong(asm,noteDelay):
    asm+='\nSpeed:\n\tdb &'
    asm+=noteDelay
    f = open(songBytesFile,'w')
    f.write(asm)
    f.close()
    subprocess.check_output(runGameCommand)

usage_errmsg = "Usage: MIDI2GB.py <MIDIfile> <Note Delay [1:255]> <Pitch ["+ str(MIN_PITCH) + ":" + str(MAX_PITCH) + "]"
tempo_errmsg = "Note delay must be a number between 1 and 255."
pitch_errmsg = "Pitch must be a number between" + str(MIN_PITCH) + " and " + str(MAX_PITCH)+ "."

if(len(sys.argv) != 4):
    print(usage_errmsg)
    exit(-1)
    
speed = sys.argv[2]
if(not speed.isdigit()):
    print(tempo_errmsg)
    exit(-1)

speed = int(speed)
if(speed < 1 or speed > 255):
    print(tempo_errmsg)
    exit(-1)
    
pitch = sys.argv[3]
if(not pitch.lstrip("-").isdigit()):
    print(pitch_errmsg)
    exit(-1)

pitch = int(pitch)
if(pitch < MIN_PITCH or pitch > MAX_PITCH):
    print(pitch_errmsg)
    exit(-1)


speed = '%x' % speed
print("Playing song with delay " + speed + " and pitch " + str(pitch))

    
midiPath = sys.argv[1]
songBytesFile = r"Song_Bytes.asm"
GBSongFile = r"GB_Song.asm"
makeGameBat = r"makegame.bat"
runGameCommand = makeGameBat + " " + GBSongFile

dump = ReadHexDump(midiPath)
midi = ReadRawMidiData(dump)

midi.RemoveDrums()
#midi.PrintTracks()

ForEachTrack(midi,FilterToNoteOnOnly)
midi.RemoveEmptyTracks()

SetStartTimeToFirstProgramChange(midi)

midi.MergeTracks()

ForEachTrack(midi,RecalculateDeltaTime)
ForEachTrack(midi,DivideDeltaTime)
ForEachTrack(midi,NormalizeNotes)
SetSongPitch(midi,pitch)

#midi.PrintTracks()
#midi.PeekFirstTrack(30)

asm = WriteTrackInAsmFormat(midi.tracks[0])

RunSong(asm,speed)

#midi.MergeTracks()
#midi.PeekFirstTrack(30)

#ForEachTrack(midi,WrapNotes)
#ForEachTrack(midi,WrapNotesUpOneOctave)
#ForEachTrack(midi,WrapNotesDownOneOctave)
#ForEachTrack(midi,PushNotes)
#ForEachTrack(midi,PushNotesUpOneOctave)
#ForEachTrack(midi,PushNotesDownHalfOctave)