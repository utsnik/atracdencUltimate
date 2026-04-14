
======================================================================
This package includes at3tool.  
The at3tool is a tool in which the encoder and decoder for ATRAC3plus(TM)
are combined into one.  

----------------------------------------------------------------------
Contents of This Package
----------------------------------------------------------------------
devkit/
|---tool
|    +---at3tool
|          |---Readme-at3tool-English.txt
|          |---windows
|          |     |---at3tool.exe
|          |     +---msvcr71.dll
|          +---linux
|                |---at3tool
|                +---libatrac.so.1.2.0
+---document
     +---tool
          +---at3tool-Tool-English.pdf

at3tool-Tool-English.pdf can be viewed with Adobe Acrobat 5.0 
or later, or with Adobe Acrobat Reader 5.0 or later.  
The latest Adobe Reader (formerly Adobe Acrobat Reader) can be 
downloaded from the Adobe website.  

----------------------------------------------------------------------
Changes in Release 3.0.0.0
----------------------------------------------------------------------
- In at3tool, an encode processing that reduces a noise in the loop 
  sound source has been added.

<Document Changes>
- The document has been changed accordingly to the change in the tool.

----------------------------------------------------------------------
Changes in Release 2.2.0.0
----------------------------------------------------------------------
- A linux command has been added.

- The file format of the ATRAC3plus(TM) file that is created by at3tool
  (PSP(TM) development tool) and the Riff header file that the PS3at3tool
  (PLAYSTATION(R)3 development tool) handles has been unified. 
  Specifically, the fact chunk format in the Riff header file has been 
  changed to the same format.

<Document Changes>
- Due to the addition of a linux command, a section "5 Precautions 
  Shared library in the Linux version" has been added.

----------------------------------------------------------------------
Changes in Release 2.0.0.0
----------------------------------------------------------------------
- Some at3tool bit rates are now newly supported as shown below: 

  ATRAC3(TM) Monaural(1ch) 52kbps
  ATRAC3(TM) Monaural(1ch) 66kbps

  ATRAC3plus(TM) Stereo(2ch) 160kbps
  ATRAC3plus(TM) Stereo(2ch) 320kbps
  ATRAC3plus(TM) Stereo(2ch) 352kbps

<Changes of Document>
- In ATRAC3(TM) and ATRAC3plus(TM) files created by at3tool, 
  the sizes of the bit rate and the elementary stream have been added.

----------------------------------------------------------------------
Changes in Release 1.0.0.0
----------------------------------------------------------------------
- The version of the encode core for ATRAC3plus has been upgraded.
  By this change, quality of the sound of ATRAC3plus has been improved.
  (For the encode core for ATRAC3, there's no change.)

----------------------------------------------------------------------
Changes in Release 0.9.0.0
----------------------------------------------------------------------
- When encoding in ATRAC3 mode, encoding might not be properly 
  performed if the bit rate is 132kbps, 105kbps, or 66kbps.  
  This problem has been fixed.  

  In the bit rate above, when a loop is enabled and the end of the loop 
  corresponds with that of the music, a problem may occur.  Because of 
  this problem, please re-encode a data file with a tool of this version
  if the data file was encoded with the bit rate above using an upgrade 
  tool with a previous version. 

- When encoding in ATRAC3plus mode, and if the bit rate is 256kbps, 
  192kbps, 128kbps, 96kbps, 64kbsp, 48kbps or 32kbps, the encoding might
  not performed properly.  This problem has been fixed.

  In the bit rate above, when a loop is enabled and the end of the loop
  corresponds with that of the music, and if the length of the loop part
  is below 20000-sample, a problem may occur.
  Because of this problem, please re-encode a data file with a tool of
  this version, if the data file was encoded with the bit rate above using
  an upgrade tool with a previous version.

- The following option has been added.
  -wholeloop : Specifying a loop for the whole file

<Changes of Document>
- Description of wholeloop option has been added.  
  Also, the description of -d option has been changed.

----------------------------------------------------------------------
Changes in Release 0.8.0
----------------------------------------------------------------------
- In ATRAC3plus mode, the following bit rate has been added. 

  Mono:96kbps, 128kbps
  Stereo:48kbps, 192kbps, 256kbps

- When more than one smpl chunks existed in an input Wav file, "more than
 one smpl chunks exist.  The last chuck will be used."  message was 
displayed. This problem has been fixed.  When more than one smpl chunks
exist in an input Wav file, "more than one smpl chunks exist.  The first
chunk will be used." message will be displayed.


<Changes of Document>
- The following description about the bit rate has been added in ATRAC3plus
  mode.

    Mono:96kbps, 128kbps
    Stereo:48kbps, 192kbps, 256kbps

----------------------------------------------------------------------
Changes in Release 0.7.0
----------------------------------------------------------------------
- A line feed was missing in the log message of when an invalid 
  parameter was specified.  This problem has been fixed.  

- A function to create data with loop information using smpl chuck of the
  input wav data has been added.
  When smpl chuck and -loop options are specified at the same time, -loop 
  option will be prioritized.

<Changes of Document>
- A note on usage has been added.  

- A description of the file supported by at3tool has been added.  
