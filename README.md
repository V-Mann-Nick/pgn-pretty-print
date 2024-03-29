# pgn-pretty-print
generate good looking pdf documents from chess game (pgn). It can currently only handle pgn files with one game. 
There's an example pdf-Document in the files generated by the programm.

### In action

This tool is integrated into my hobby chess website:

https://www.gambitaccepted.com

### Requirements:
- reportlab
- python-chess

### Planned features:
- more options for styling the document
- intelligent content splitting
- support for pgn-files with more than one game.


```
positional arguments:
  pgnPath               specify the path to the pgn

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUTPATH, --outputPath OUTPUTPATH
                        defines the output path
  -n FILENAME, --filename FILENAME
                        Specify a filename. Default: "[White] - [Black].pdf"
  -p PRINTBOARD, --printBoard PRINTBOARD
                        Give a string of moves to be printed (e.g. "2w 3b
                        10w")
  -fs FONTSIZE, --fontSize FONTSIZE
                        Set the font size
  -fn FONTNAME, --fontName FONTNAME
                        set the font. Available: Helvetica, Times-Roman,
                        Courier
  -sb SPACEBEFORE, --spaceBefore SPACEBEFORE
                        Set amount of space before every paragraph
  -sa SPACEAFTER, --spaceAfter SPACEAFTER
                        Set amount of space after every paragraph
  -pm PAGEMARGIN, --pageMargin PAGEMARGIN
                        Set margin (left, right, bottom, up) of page
  -cg COLUMNGAP, --columnGap COLUMNGAP
                        Set the width (in cm) between columns in two-column-
                        layout
```
