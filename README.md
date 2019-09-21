# pgn-pretty-print
generate good looking pdf documents from chess game (pgn). There's and example pdf-file generated.

Requirements:
- reportlab
- python-chess


```
Pretty print for pgn

positional arguments:
  pgn_path              specify the path to the pgn

optional arguments:
  -h, --help            show this help message and exit
  -p PRINTBOARD, --printBoard PRINTBOARD
                        Give a string of moves to be printed (e.g. "2w 3b
                        10w")
  -fs FONTSIZE, --fontSize FONTSIZE
                        Set the font size
  -fn FONTNAME, --fontName FONTNAME
                        Set the font name
  -sb SPACEBEFORE, --spaceBefore SPACEBEFORE
                        Set amount of space before every paragraph
  -sa SPACEAFTER, --spaceAfter SPACEAFTER
                        Set amount of space after every paragraph
  -ls LINESPACING, --lineSpacing LINESPACING
                        Set amount of space a single line takes
  -pm PAGEMARGIN, --pageMargin PAGEMARGIN
                        Set margin (left, right, bottom, up) of page
```
