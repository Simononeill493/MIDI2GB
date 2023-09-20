# MIDI2GB
<br/>
Python program which converts a MIDI file into a GBZ80 assembly file, and attempts to build and run it as a Game Boy ROM. <br/>
Tested with vasmz80_oldstyle v1.9d and BGB v1.5.8. Both will need to be downloaded separately. <br/>
<br/>
The script to run is MIDI2GB.py. It takes three arguments: the MIDI file to play, a number from 1 to 255 which control's the song's tempo, and a number from -6 to 2 which controls the pitch. <br/>
<br/>
The Python program generates the required assembly instructions, then runs makegame.bat, which uses VASM (http://sun.hasenbraten.de/vasm/) to compile those instructions into a ROM. <br/>
You can open this ROM in any Game Boy emulator, but by default, the script will automatically try and boot it in an instance of BGB (https://bgb.bircd.org/). If you're using another emulator, you'll need to change that line in the batch script. <br/>
<br/>
In order for VASM to compile the ROM successfully, you'll also need the ChibiAkumas headers. Specifically you'll need VasmBuildCompat.asm, GB_V1_Header.asm, GB_V1_Functions.asm and GB_V1_Footer.asm. <br/>
You can find them all at https://www.chibiakumas.com/z80/helloworld.php (scroll down on the sidebar for sources.7z) <br/>
Stick all four in a directory named 'ResourceFIles', and put it in the same directory as the Python script.  <br/>
<br/>
The converter only uses two of the Game Boy's audio tracks, so any MIDI which plays more than two notes simultaneously will fail to play some of its notes. Also, notes will end immediately, as I haven't implemented sustained notes. <br/>
Generally speaking, this program ignores a lot of MIDI metadata, and will likely break on complex MIDI files. You might have to edit the MIDI a little, with these constraints in mind, to get it to sound nice.  To get started, try setting delay to 120, and pitch to zero, and see how it sounds. <br/>
<br/>
MIDI file format information can be found at https://ccrma.stanford.edu/~craig/14q/midifile/MidiFileFormat.html<br/>
and http://www.music.mcgill.ca/~ich/classes/mumt306/StandardMIDIfileformat.html<br/>
<br/>
Special thanks to https://www.chibiakumas.com/ for all the tutorials and resources he provides on programming with the GBZ80<br/>
