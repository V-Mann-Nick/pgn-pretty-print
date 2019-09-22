#!/usr/bin/python


import argparse
import chess
import chess.pgn
from reportlab.platypus import Table, Image, Frame, BaseDocTemplate, Paragraph, PageTemplate
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus.flowables import KeepTogether


# ------------- CONSTANTS -------------
BOARD_LENGTH = 15  # in cm
TILE_LENGTH = BOARD_LENGTH / 8  # in cm
TILE_PADDING = 0.1  # relative to TILE_LENGTH
PIECE_IMAGES_PATH = 'piece_images/merida/72/'

# ------------- OPTIONS -------------
DARK_TILE_COLOR = colors.brown
LIGHT_TILE_COLOR = colors.white
PAGE_MARGIN = 1.27  # in cm
HALFMOVES_TO_BE_PRINTED = list()
FONT_NAME = None
FONT_SIZE = None
LINE_SPACING = None
SPACE_BEFORE = None
SPACE_AFTER = None
LINE_SPACING = None
COL_GAP = None
# not yet implemented
PAGE_FORMAT = A4
PAGE_LAYOUT = None
PAGE_NUMBERING = None


def board_from_FEN(fen):
    # Generate Data for Table from FEN-Code
    board_setup_fen = fen.split(' ')[0]
    rank_setup_fen = board_setup_fen.split('/')
    board_setup = []
    for rank in rank_setup_fen:
        rank_setup = []
        for tile in rank:
            if tile.isalpha():
                piece = 'w{}'.format(tile.lower()) if tile.isupper() else 'b{}'.format(tile)
                img_size = TILE_LENGTH * (1 - TILE_PADDING) * cm
                img = Image('{}{}.png'.format(PIECE_IMAGES_PATH, piece), width=img_size, height=img_size)
                rank_setup.append(img)
            elif tile.isdigit():
                rank_setup += [None] * int(tile)
            else:
                print('{} is not valid in {}'.format(tile, board_setup_fen))
        board_setup.append(rank_setup)
    # Arrange chess board as table
    table_style = [('ALIGN', (0, 0), (7, 7), 'CENTER'),
                   ('VALIGN', (0, 0), (7, 7), 'MIDDLE'),
                   ('BOX', (0, 0), (7, 7), 0.5, colors.grey)]
    # Color cells according to a chess board
    dark_tile_coords = [(i, j) for j in range(8) for i in range(8) if j % 2 is 1 and i % 2 is 0 or j % 2 is 0 and i % 2 is 1]
    light_tile_coords = [(i, j) for j in range(8) for i in range(8) if j % 2 is 0 and i % 2 is 0 or j % 2 is 1 and i % 2 is 1]
    table_style += [('BACKGROUND', coord, coord, DARK_TILE_COLOR) for coord in dark_tile_coords]
    table_style += [('BACKGROUND', coord, coord, LIGHT_TILE_COLOR) for coord in light_tile_coords]
    return Table(board_setup, colWidths=[TILE_LENGTH * cm] * 8, rowHeights=[TILE_LENGTH * cm] * 8, style=table_style)


def print_move_and_variations(move, halfmove):
    # [move number (if white to move)] [move (san)] [comment]
    # examples: '1. e4', 'c5'
    move_number = int((halfmove + 2) / 2)
    white_to_move = halfmove % 2 is 0
    # Force print of move number for a black move
    text = '<strong>{}{}</strong>{}'.format('{}. '.format(move_number) if white_to_move else '',
                                            move.san(),
                                            ' {}'.format(move.comment) if move.comment else '')
    # If game has variations at this point they will be printed including comments.
    # examples: 'c5 (1... e5 2. Nf3)', '2. Nf3 (2. d4 a more direct approach)'
    if len(move.parent.variations) > 1:
        for i in range(1, len(move.parent.variations)):
            text += ' (<i>'
            # This will only add the first move of the variation
            text += '<strong>{}{}</strong>{}'.format('{}. '.format(move_number) if white_to_move else '{}... '.format(move_number),
                                           move.parent.variations[i].san(),
                                           ' {}'.format(move.parent.variations[i].comment) if move.parent.variations[i].comment else '')
            # For the following moves recursivly explore the variation tree
            # This will also include subvariations
            for j, var_move in enumerate(move.parent.variations[i].mainline()):
                text += ' {}'.format(print_move_and_variations(var_move, halfmove + 1 + j))
            text += '</i>)'
    return text


def create_document(game):
    styles = getSampleStyleSheet()
    doc = BaseDocTemplate('{} - {}.pdf'.format(game.headers.get('White'), game.headers.get('Black')),
                          pagesize=PAGE_FORMAT,
                          leftMargin=PAGE_MARGIN * cm,
                          rightMargin=PAGE_MARGIN * cm,
                          topMargin=PAGE_MARGIN * cm,
                          bottomMargin=PAGE_MARGIN * cm,
                          showBoundary=0,
                          allowSplitting=1)

    # define styles for paragraphs
    styles.add(ParagraphStyle(
        'Header',
        fontSize=FONT_SIZE,
        fontName=FONT_NAME,
        spaceBefore=SPACE_BEFORE,
        spaceAfter=SPACE_AFTER,
        leading=LINE_SPACING,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        'Move_Text',
        fontSize=FONT_SIZE,
        fontName=FONT_NAME,
        spaceBefore=SPACE_BEFORE,
        spaceAfter=SPACE_AFTER,
        leading=LINE_SPACING
    ))

    # Two Columns
    frame_width = doc.width / 2 - COL_GAP / 2 * cm
    frame1 = Frame(doc.leftMargin, doc.bottomMargin, frame_width, doc.height, id='col1')
    frame2 = Frame(doc.leftMargin + frame_width + COL_GAP * cm, doc.bottomMargin, frame_width, doc.height, id='col2')
    doc.addPageTemplates([PageTemplate(id='twoCol', frames=[frame1, frame2])])

    # Set board dimensions relative to the two column layout
    global BOARD_LENGTH, TILE_LENGTH
    BOARD_LENGTH = 0.8 * frame_width / cm  # in cm
    TILE_LENGTH = BOARD_LENGTH / 8  # in cm

    # elements will contain flowables for the build function
    elements = []
    # Paragraph for Heading and meta information
    paragraph = '<font size={}><strong>{}<i>{}</i><br/> vs.<br/>{}<i>{}</i></strong></font><br/>'.format(
        FONT_SIZE + 2,
        game.headers.get('White'),
        ' [{}]'.format(game.headers.get('WhiteElo')) if game.headers.get('WhiteElo') else '',
        game.headers.get('Black'),
        ' [{}]'.format(game.headers.get('BlackElo')) if game.headers.get('BlackElo') else '')
    for key in game.headers.keys():
        if key != 'White' and key != 'Black' and key != 'WhiteElo' and key != 'BlackElo' and game.headers.get(key) != '?':
            paragraph += '<br/>{}: {}'.format(key, game.headers.get(key))
    elements.append(Paragraph(paragraph, styles['Header']))
    # Generate paragraphs with move text and board diagramms
    paragraph = str()
    for i, move in enumerate(game.mainline()):
        # After print of a board diagramm if it's black's move print move number
        if any([i - 1 == halfmove for halfmove in HALFMOVES_TO_BE_PRINTED]) and i % 2 == 1:
            paragraph += '<strong>{}...</strong> {} '.format(int((i + 2) / 2), print_move_and_variations(move, i).replace('<*>', '').strip())
        else:
            paragraph += print_move_and_variations(move, i).replace('<*>', '').strip() + ' '
        if move.comment and '<*>' in move.comment or any([i == halfmove for halfmove in HALFMOVES_TO_BE_PRINTED]):
            elements.append(Paragraph(paragraph, styles['Move_Text']))
            elements.append(KeepTogether(board_from_FEN(move.board().fen())))
            paragraph = str()
    elements.append(Paragraph(paragraph, styles['Move_Text']))

    doc.build(elements)


# TODO: Error handling
def run(args):
    # Open pgn with parsed path
    with open(args.pgn_path) as pgn:
        game = chess.pgn.read_game(pgn)

    # Parse moves to be printed with board
    global HALFMOVES_TO_BE_PRINTED
    for token in args.printBoard.split(' '):
        # example: '3w' translates to halfmove number 4
        halfmove = int(token[:-1]) * 2
        halfmove -= 2 if token[-1] == 'w' else 1
        HALFMOVES_TO_BE_PRINTED.append(halfmove)

    # Set style variables
    global FONT_SIZE, FONT_NAME, SPACE_BEFORE, SPACE_AFTER, LINE_SPACING, PAGE_MARGIN, \
        ALLOW_SPLITTING, COL_GAP
    FONT_SIZE = args.fontSize
    FONT_NAME = args.fontName
    SPACE_BEFORE = args.spaceBefore
    SPACE_AFTER = args.spaceAfter
    LINE_SPACING = args.lineSpacing
    PAGE_MARGIN = args.pageMargin
    COL_GAP = args.columnGap

    create_document(game)


def main():
    parser = argparse.ArgumentParser(description="Pretty print for pgn")
    parser.add_argument('pgn_path',
                        help='specify the path to the pgn')
    parser.add_argument('-p',
                        '--printBoard',
                        help='Give a string of moves to be printed (e.g. "2w 3b 10w")',
                        default='1w')
    parser.add_argument('-fs',
                        '--fontSize',
                        type=int,
                        help='Set the font size',
                        default='10')
    parser.add_argument('-fn',
                        '--fontName',
                        help='Set the font name',
                        default='Helvetica')
    parser.add_argument('-sb',
                        '--spaceBefore',
                        type=int,
                        help='Set amount of space before every paragraph',
                        default=6)
    parser.add_argument('-sa',
                        '--spaceAfter',
                        type=int,
                        help='Set amount of space after every paragraph',
                        default=6)
    parser.add_argument('-ls',
                        '--lineSpacing',
                        type=int,
                        help='Set amount of space a single line takes',
                        default=12)
    parser.add_argument('-pm',
                        '--pageMargin',
                        type=float,
                        help='Set margin (left, right, bottom, up) of page',
                        default=1.27)
    parser.add_argument('-cg',
                        '--columnGap',
                        type=float,
                        help='Set the width (in cm) between columns in two-column-layout',
                        default=1)
    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
