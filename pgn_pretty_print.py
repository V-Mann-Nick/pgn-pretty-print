#!/usr/bin/python


import argparse
import os
from io import StringIO, BytesIO
import chess
import chess.pgn
from reportlab.platypus import Table, Image, Frame, BaseDocTemplate, Paragraph, PageTemplate, SimpleDocTemplate
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus.flowables import KeepTogether

# TODO
# - immprove pdf-return/pdf-file-save
# - think about error handling
# - more comments


class GamePrinter:
    tile_padding = 0.1  # meaning 10% of width/height of tile is padded
    piece_images_path = 'app/static/images/piece_images/merida/72/'

    def __init__(self,
                 pgn,
                 output_path='',
                 filename='',
                 halfmoves_to_be_printed=list(),
                 dark_tile_color='#7C7671',
                 light_tile_color='#DCD7BC',
                 page_format=A4,
                 page_margin=1.27,  # in cm
                 font_name='Helvetica',
                 font_size=12,
                 space_before=6,
                 space_after=6,
                 col_gap=1,
                 # not yet implemented
                 page_layout='two_col',
                 page_numbering=None):
        self.change_game(pgn)
        self.output_path = output_path
        self.filename = filename if filename else '{} - {}.pdf'.format(self.game.headers.get('White'),
                                                                       self.game.headers.get('Black'))
        self.halfmoves_to_be_printed = halfmoves_to_be_printed
        self.dark_tile_color = dark_tile_color
        self.light_tile_color = light_tile_color
        self.page_margin = page_margin
        self.font_name = font_name
        self.font_size = font_size
        self.space_before = space_before
        self.space_after = space_after
        self.col_gap = col_gap
        self.page_layout = page_layout
        self.page_numbering = page_numbering
        if page_format == 'letter':
            self.page_format = letter
        else:
            self.page_format = A4

    def init_reportlab(self, save_to_file=True):
        self.styles = getSampleStyleSheet()
        self.buff = BytesIO()
        self.doc = BaseDocTemplate(os.path.join(self.output_path, self.filename) if save_to_file else self.buff,
                                   pagesize=self.page_format,
                                   leftMargin=self.page_margin * cm,
                                   rightMargin=self.page_margin * cm,
                                   topMargin=self.page_margin * cm,
                                   bottomMargin=self.page_margin * cm,
                                   showBoundary=0,
                                   allowSplitting=1)
        # define styles for paragraphs
        self.styles.add(ParagraphStyle(
            'Header',
            fontSize=self.font_size,
            fontName=self.font_name,
            spaceBefore=self.space_before,
            spaceAfter=self.space_after,
            leading=self.font_size,
            alignment=TA_CENTER
        ))
        self.styles.add(ParagraphStyle(
            'Move_Text',
            fontSize=self.font_size,
            fontName=self.font_name,
            spaceBefore=self.space_before,
            spaceAfter=self.space_after,
            leading=self.font_size,
        ))
        # TODO: Add more Layouts
        if False:
            pass
        elif self.page_layout == 'two_col':
            frame_width = self.doc.width / 2 - self.col_gap / 2 * cm
            frame1 = Frame(self.doc.leftMargin, self.doc.bottomMargin, frame_width, self.doc.height, id='col1')
            frame2 = Frame(self.doc.leftMargin + frame_width + self.col_gap * cm, self.doc.bottomMargin, frame_width, self.doc.height, id='col2')
            self.doc.addPageTemplates([PageTemplate(id='twoCol', frames=[frame1, frame2])])
            # Set board dimensions relative to the two column layout
            self.board_length = 0.8 * frame_width / cm  # in cm
            self.tile_length = self.board_length / 8  # in cm

    def change_game(self, pgn):
        if type(pgn) is str and os.path.exists(pgn):
            with open(pgn) as f:
                self.game = chess.pgn.read_game(f)
        else:
            self.game = chess.pgn.read_game(StringIO(pgn))

    def get_file_path(self):
        return os.path.join(self.output_path, self.doc_name)

    def board_from_FEN(self, fen):
        # Generate Data for Table from FEN-Code
        board_setup_fen = fen.split(' ')[0]
        rank_setup_fen = board_setup_fen.split('/')
        board_setup = []
        for rank in rank_setup_fen:
            rank_setup = []
            for tile in rank:
                if tile.isalpha():
                    piece = 'w{}'.format(tile.lower()) if tile.isupper() else 'b{}'.format(tile)
                    img_size = self.tile_length * (1 - self.tile_padding) * cm
                    img = Image('{}{}.png'.format(self.piece_images_path, piece), width=img_size, height=img_size)
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
        table_style += [('BACKGROUND', coord, coord, self.dark_tile_color) for coord in dark_tile_coords]
        table_style += [('BACKGROUND', coord, coord, self.light_tile_color) for coord in light_tile_coords]
        return Table(board_setup, colWidths=[self.tile_length * cm] * 8, rowHeights=[self.tile_length * cm] * 8, style=table_style)

    def print_move_and_variations(self, move, halfmove):
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
                    text += ' {}'.format(self.print_move_and_variations(var_move, halfmove + 1 + j))
                text += '</i>)'
        return text

    def create_and_return_document(self):
        self.init_reportlab(save_to_file=False)
        self.create_document()
        return self.buff


    def create_document(self):
        # elements will contain flowables for the build function
        elements = []
        # Paragraph for Heading and meta information
        paragraph = '<font size={}><strong>{}<i>{}</i><br/> vs.<br/>{}<i>{}</i></strong></font><br/>'.format(
            self.font_size + 2,
            self.game.headers.get('White'),
            ' [{}]'.format(self.game.headers.get('WhiteElo')) if self.game.headers.get('WhiteElo') else '',
            self.game.headers.get('Black'),
            ' [{}]'.format(self.game.headers.get('BlackElo')) if self.game.headers.get('BlackElo') else '')
        for key in self.game.headers.keys():
            if key != 'White' and key != 'Black' and key != 'WhiteElo' and key != 'BlackElo' and self.game.headers.get(key) != '?':
                paragraph += '<br/>{}: {}'.format(key, self.game.headers.get(key))
        elements.append(Paragraph(paragraph, self.styles['Header']))
        # Generate paragraphs with move text and board diagramms
        paragraph = str()
        for i, move in enumerate(self.game.mainline()):
            if move.comment and '<*>' in move.comment or any([i == halfmove for halfmove in self.halfmoves_to_be_printed]):
                elements.append(Paragraph(paragraph, self.styles['Move_Text']))
                elements.append(KeepTogether(self.board_from_FEN(move.board().fen())))
                paragraph = str()
            # After print of a board diagramm if it's black's move print move number
            if any([i == halfmove for halfmove in self.halfmoves_to_be_printed]) and i % 2 == 1:
                paragraph += '<strong>{}...</strong> {} '.format(int((i + 2) / 2), self.print_move_and_variations(move, i).replace('<*>', '').strip())
            else:
                paragraph += self.print_move_and_variations(move, i).replace('<*>', '').strip() + ' '
        elements.append(Paragraph(paragraph, self.styles['Move_Text']))
        self.doc.build(elements)


def run(args):
    # Parse moves to be printed with board
    halfmoves_to_be_printed = list()
    for token in args.printBoard.split(' '):
        # example: '3w' translates to halfmove number 4
        halfmove = int(token[:-1]) * 2
        halfmove -= 2 if token[-1] == 'w' else 1
        halfmoves_to_be_printed.append(halfmove)
    # Create a GamePrinter Object
    printer = GamePrinter(args.pgnPath,
                          output_path=args.outputPath,
                          filename=args.filename,
                          halfmoves_to_be_printed=halfmoves_to_be_printed,
                          page_margin=args.pageMargin,
                          font_name=args.fontName,
                          font_size=args.fontSize,
                          space_before=args.spaceBefore,
                          space_after=args.spaceAfter,
                          col_gap=args.columnGap)
    printer.create_document()


def main():
    parser = argparse.ArgumentParser(description="Pretty print for pgn")
    parser.add_argument('pgnPath',
                        help='specify the path to the pgn')
    parser.add_argument('-o',
                        '--outputPath',
                        type=str,
                        help='defines the output path',
                        default='')
    parser.add_argument('-n',
                        '--filename',
                        type=str,
                        help='Specify a filename. Default: "[White] - [Black].pdf"',
                        default='')
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
                        help='set the font. Available: Helvetica, Times-Roman, Courier',
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
