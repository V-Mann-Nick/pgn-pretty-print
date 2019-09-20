#!/usr/bin/python

from reportlab.platypus import Table, Image, Frame, BaseDocTemplate, Paragraph, PageTemplate
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
# import re
import chess
import chess.pgn
import argparse


# ------------- CONSTANTS -------------
BOARD_LENGTH = 15  # in cm
TILE_LENGTH = BOARD_LENGTH / 8  # in cm
TILE_PADDING = 0.1  # relative to TILE_LENGTH
DARK_TILE_COLOR = colors.brown
LIGHT_TILE_COLOR = colors.white
PIECE_IMAGES_PATH = 'piece_images/merida/72/'
PAGE_MARGIN = 1.27  # in cm
HALFMOVES_TO_BE_PRINTED = list()


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
    text = '<b>{}{}</b><i>{}</i>'.format('{}. '.format(move_number) if white_to_move else '',
                                         move.san(),
                                         ' {}'.format(move.comment) if move.comment else '')
    # If game has variations at this point they will be printed including comments.
    # examples: 'c5 (1... e5 2. Nf3)', '2. Nf3 (2. d4 a more direct approach)'
    if len(move.parent.variations) > 1:
        for i in range(1, len(move.parent.variations)):
            text += ' '
            # This will only add the first move of the variation
            text += '({}{}<i>{}</i>'.format('{}. '.format(move_number) if white_to_move else '{}... '.format(move_number),
                                            move.parent.variations[i].san(),
                                            ' {}'.format(move.parent.variations[i].comment) if move.parent.variations[i].comment else '')
            # For the following moves recursivly explore the variation tree
            # This will also include subvariations
            for j, var_move in enumerate(move.parent.variations[i].mainline()):
                text += ' {}'.format(print_move_and_variations(var_move, halfmove + 1 + j))
            text += ')'
    return text


def create_document(game):
    styles = getSampleStyleSheet()
    doc = BaseDocTemplate('{} - {}.pdf'.format(game.headers['White'], game.headers['Black']),
                          pagesize=A4,
                          leftMargin=PAGE_MARGIN * cm,
                          rightMargin=PAGE_MARGIN * cm,
                          topMargin=PAGE_MARGIN * cm,
                          bottomMargin=PAGE_MARGIN * cm,
                          showBoundary=0,
                          allowSplitting=0)

    # Two Columns
    frame_gap = 0.15  # in cm
    frame_width = doc.width / 2 - frame_gap / 2 * cm
    frame1 = Frame(doc.leftMargin, doc.bottomMargin, frame_width, doc.height, id='col1')
    frame2 = Frame(doc.leftMargin + frame_width + frame_gap, doc.bottomMargin, frame_width, doc.height, id='col21')
    doc.addPageTemplates([PageTemplate(id='twoCol', frames=[frame1, frame2])])

    # Set board dimensions relative to the two column layout
    global BOARD_LENGTH, TILE_LENGTH
    BOARD_LENGTH = frame1.width / cm  # in cm
    TILE_LENGTH = BOARD_LENGTH / 8  # in cm

    # elements will contain flowables for the build function
    elements = []
    # Generate paragraphs and board diagramms
    paragraph = str()
    for i, move in enumerate(game.mainline()):
        paragraph += print_move_and_variations(move, i) + ' '
        if move.comment and '<*>' in move.comment or any([i == halfmove for halfmove in HALFMOVES_TO_BE_PRINTED]):
            elements.append(Paragraph(paragraph, styles['Normal']))
            elements.append(board_from_FEN(move.board().fen()))
            paragraph = str()
    elements.append(Paragraph(paragraph, styles['Normal']))

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
    create_document(game)


def main():
    parser = argparse.ArgumentParser(description="Pretty print for pgn")
    parser.add_argument('pgn_path', help='specify the path to the pgn')
    parser.add_argument('-p', '--printBoard', help='Give a string of moves to be printed (e.g. "2w 3b 10w")', default='1w')
    parser.set_defaults(func=run)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()


# def parse_PGN(pgn):
#     meta_info, move_text = pgn.split('\n\n')
#     meta_info = re.compile('\[.*\]').findall(meta_info)
#     tags = {}
#     for tag in meta_info:
#         tags[re.compile('(?<=\[)\w*(?= )').search(tag)[0]] = re.compile('(?<= ").*(?="\])').search(tag)[0]
#     moves_raw = re.compile('\d{1,3}\.').split(move_text.replace('\n', ' '))[1:]
#     # every item in moves is a half move: 0 being white's first move and 1 being black's first move and so on
#     moves = []
#     # keys for the comments dictionary are integers of half-move
#     comments = {}
#     for i, move in enumerate(moves_raw):
#         if '{' in move:
#             # This regex pattern checks if comment is at end of string (with black's move)
#             comment = re.compile('(?<=\{).*(?=\}$)').search(move.strip())
#             if comment:
#                 comments[i * 2 + 1] = comment.group()
#             # if it's not at the end then the comment concerns white's move
#             else:
#                 comments[i * 2] = re.compile('(?<=\{).*(?=\})').search(move.strip()).group()
#             # No remove the comment
#             move = re.compile(' \{.*\}').sub('', move).strip()
#         moves += move.strip().split(' ')
#     return tags, moves, comments


# Deprecated !!
# def open_pgn(link):
#     with open(link) as pgn:
#         GAME = chess.pgn.read_game(pgn)
