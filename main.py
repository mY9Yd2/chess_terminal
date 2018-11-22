#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#     This file is part of the chess_terminal application.
#     Copyright (C) 2018  Kovács József Miklós <kovacsjozsef7u@gmail.com>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import chess
import chess.uci
import chess.pgn
import time
import argparse
import colorama
import configparser
import pathlib
import uuid
import os


class MyBoard(chess.Board):
    def no_color(self, conf):
        builder = []
        counter = 8

        builder.append("  ")
        builder.append("  a b c d e f g h")
        builder.append("    \n\n")

        for i, square in enumerate(chess.SQUARES_180):
            piece = self.piece_at(square)

            if i % 8 == 0:
                builder.append(" ")
                builder.append(str(counter))
                builder.append(" ")

            builder.append(" ")
            if piece:
                builder.append(piece.symbol())
            else:
                builder.append(conf["empty_square_char"])

            if chess.BB_SQUARES[square] & chess.BB_FILE_H:
                builder.append("  ")
                builder.append(str(counter))
                builder.append(" ")
                counter -= 1

                if square != chess.H1:
                    builder.append("\n")
        builder.append("\n\n")
        builder.append("  ")
        builder.append("  a b c d e f g h   ")

        return "".join(builder)

    def colored(self, conf, small):
        builder = []
        counter = 8

        column_chars = "  a  b  c  d  e  f  g  h"
        square_color_bool = True

        builder.append(conf["bolder_color"])
        builder.append("  ")
        for x in column_chars:
            if x == " ":
                builder.append(x)
            else:
                builder.append(conf["bolder_char_color"])
                builder.append(x)
                builder.append(colorama.Style.RESET_ALL)
                builder.append(conf["bolder_color"])
        builder.append("    \n")
        builder.append(colorama.Style.RESET_ALL)

        for i, square in enumerate(chess.SQUARES_180):
            piece = self.piece_at(square)

            if i % 8 == 0:
                builder.append(conf["bolder_color"])
                builder.append(" ")
                builder.append(conf["bolder_char_color"])
                builder.append(str(counter))
                builder.append(colorama.Style.RESET_ALL)
                builder.append(conf["bolder_color"])
                builder.append(" ")
                builder.append(colorama.Style.RESET_ALL)

            if square_color_bool:
                builder.append(conf["square_color_true"])
            else:
                builder.append(conf["square_color_false"])

            builder.append(" ")
            if piece:
                p_symbol = piece.symbol()

                if p_symbol.islower():
                    builder.append(conf["black_piece_color"])
                else:
                    builder.append(conf["white_piece_color"])

                if small:
                    builder.append(p_symbol)
                else:
                    builder.append(p_symbol.upper())
            else:
                builder.append(conf["empty_square_char"])

            builder.append(colorama.Style.RESET_ALL)

            if chess.BB_SQUARES[square] & chess.BB_FILE_H:
                if square_color_bool:
                    builder.append(conf["square_color_true"])
                else:
                    builder.append(conf["square_color_false"])
                builder.append(" ")
                builder.append(colorama.Style.RESET_ALL)

                builder.append(conf["bolder_color"])
                builder.append(" ")
                builder.append(conf["bolder_char_color"])
                builder.append(str(counter))
                builder.append(colorama.Style.RESET_ALL)
                builder.append(conf["bolder_color"])
                builder.append(" ")
                builder.append(colorama.Style.RESET_ALL)
                counter -= 1

                if square != chess.H1:
                    builder.append("\n")
            else:
                if square_color_bool:
                    builder.append(conf["square_color_true"])
                    square_color_bool = False
                else:
                    builder.append(conf["square_color_false"])
                    square_color_bool = True
                builder.append(" ")
                builder.append(colorama.Style.RESET_ALL)
        builder.append("\n")
        builder.append(conf["bolder_color"])
        builder.append("  ")
        for x in column_chars:
            if x == " ":
                builder.append(x)
            else:
                builder.append(conf["bolder_char_color"])
                builder.append(x)
                builder.append(colorama.Style.RESET_ALL)
                builder.append(conf["bolder_color"])
        builder.append("    ")
        builder.append(colorama.Style.RESET_ALL)

        return "".join(builder)


def engine_turn(engine, board, color, m_time):
    try:
        print(f"{color} ({board.fullmove_number}): thinking...")
        engine.position(board)
        move = engine.go(movetime=m_time)
        s_move = board.san(move.bestmove)
        board.push(move.bestmove)
        return s_move
    except KeyboardInterrupt:
        print("\nExited\n")
        raise SystemExit


def player_turn(board, color):
    while True:
        try:
            move = input(f"{color} ({board.fullmove_number}): ")
            if move == "resign":
                return move
            elif move == "?":
                legal_moves = str(board.legal_moves)
                print("\nLegal moves: " + legal_moves[legal_moves.find("(") + 1:legal_moves.find(")")], end="\n\n")
            else:
                board.push(board.parse_san(move))
                return move
        except ValueError:
            print("Invalid move!")
        except KeyboardInterrupt:
            print("\nExited\n")
            raise SystemExit


def args_init():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--side", default="white", help="Choose black or white.",
                        choices=["black", "white", "b", "w"])
    parser.add_argument("-c", "--config", help="Use another config file. Set path to the file.")
    parser.add_argument("-n", "--noColor", action="store_true", help="No color.")
    parser.add_argument("-p", "--pgn", action="store_true", help="Save PGN.")
    parser.add_argument("-t", "--time", default=2000, type=int, help="Set chess engine thinking time (ms).")
    parser.add_argument("-S", "--small", action="store_true", help="Small character for black side.")
    parser.add_argument("-o", "--opponent", action="count", help="player vs player or P vs engine, E vs E.")
    args = parser.parse_args()
    return args


def read_config(file_name, engine_on):
    result_dict = {}
    config = configparser.ConfigParser()
    config.read(file_name)

    if engine_on:
        if config.get("BASIC", "chess_engine") == "":
            raise ValueError
        else:
            result_dict["chess_engine"] = config.get("BASIC", "chess_engine")

    if config.get("BASIC", "empty_square_char") == "":
        result_dict["empty_square_char"] = " "
    else:
        result_dict["empty_square_char"] = config.get("BASIC", "empty_square_char")

    result_dict["square_color_true"] = \
        get_color(config.get("COLORS", "square_color_true", fallback="colorama.Back.LIGHTMAGENTA_EX"))
    result_dict["square_color_false"] = \
        get_color(config.get("COLORS", "square_color_false", fallback="colorama.Back.YELLOW"))
    result_dict["bolder_color"] = \
        get_color(config.get("COLORS", "bolder_color", fallback="colorama.Back.LIGHTBLUE_EX"))
    result_dict["black_piece_color"] = \
        get_color(config.get("COLORS", "black_piece_color", fallback="colorama.Fore.BLACK"))
    result_dict["white_piece_color"] = \
        get_color(config.get("COLORS", "white_piece_color", fallback="colorama.Fore.WHITE"))
    result_dict["bolder_char_color"] = \
        get_color(config.get("COLORS", "bolder_char_color", fallback="colorama.Style.BRIGHT"))

    return result_dict


def get_color(color):
    color_dict = {
        "colorama.Fore.LIGHTRED_EX": colorama.Fore.LIGHTRED_EX,
        "colorama.Fore.LIGHTBLUE_EX": colorama.Fore.LIGHTBLUE_EX,
        "colorama.Fore.LIGHTYELLOW_EX": colorama.Fore.LIGHTYELLOW_EX,
        "colorama.Fore.LIGHTWHITE_EX": colorama.Fore.LIGHTWHITE_EX,
        "colorama.Fore.LIGHTGREEN_EX": colorama.Fore.LIGHTGREEN_EX,
        "colorama.Fore.LIGHTCYAN_EX": colorama.Fore.LIGHTCYAN_EX,
        "colorama.Fore.LIGHTBLACK_EX": colorama.Fore.LIGHTBLACK_EX,
        "colorama.Fore.LIGHTMAGENTA_EX": colorama.Fore.LIGHTMAGENTA_EX,
        "colorama.Fore.RED": colorama.Fore.RED,
        "colorama.Fore.BLUE": colorama.Fore.BLUE,
        "colorama.Fore.YELLOW": colorama.Fore.YELLOW,
        "colorama.Fore.WHITE": colorama.Fore.WHITE,
        "colorama.Fore.GREEN": colorama.Fore.GREEN,
        "colorama.Fore.CYAN": colorama.Fore.CYAN,
        "colorama.Fore.BLACK": colorama.Fore.BLACK,
        "colorama.Fore.MAGENTA": colorama.Fore.MAGENTA,
        "colorama.Back.LIGHTRED_EX": colorama.Back.LIGHTRED_EX,
        "colorama.Back.LIGHTBLUE_EX": colorama.Back.LIGHTBLUE_EX,
        "colorama.Back.LIGHTYELLOW_EX": colorama.Back.LIGHTYELLOW_EX,
        "colorama.Back.LIGHTWHITE_EX": colorama.Back.LIGHTWHITE_EX,
        "colorama.Back.LIGHTGREEN_EX": colorama.Back.LIGHTGREEN_EX,
        "colorama.Back.LIGHTCYAN_EX": colorama.Back.LIGHTCYAN_EX,
        "colorama.Back.LIGHTBLACK_EX": colorama.Back.LIGHTBLACK_EX,
        "colorama.Back.LIGHTMAGENTA_EX": colorama.Back.LIGHTMAGENTA_EX,
        "colorama.Back.RED": colorama.Back.RED,
        "colorama.Back.BLUE": colorama.Back.BLUE,
        "colorama.Back.YELLOW": colorama.Back.YELLOW,
        "colorama.Back.WHITE": colorama.Back.WHITE,
        "colorama.Back.GREEN": colorama.Back.GREEN,
        "colorama.Back.CYAN": colorama.Back.CYAN,
        "colorama.Back.BLACK": colorama.Back.BLACK,
        "colorama.Back.MAGENTA": colorama.Back.MAGENTA,
        "colorama.Style.BRIGHT": colorama.Style.BRIGHT,
        "colorama.Style.DIM": colorama.Style.DIM,
        "colorama.Style.RESET_ALL": colorama.Style.RESET_ALL
    }

    return color_dict[color]


def write_config():
    config = configparser.ConfigParser(allow_no_value=True)

    config.add_section("BASIC")
    config.set("BASIC", "; INFO: https://gitlab.com/Tz2/chess_terminal/wikis/home")
    config.set("BASIC", "chess_engine", "")
    config.set("BASIC", "empty_square_char", "")

    config.add_section("COLORS")
    config.set("COLORS", "square_color_true", "colorama.Back.LIGHTMAGENTA_EX")
    config.set("COLORS", "square_color_false", "colorama.Back.YELLOW")
    config.set("COLORS", "bolder_color", "colorama.Back.LIGHTBLUE_EX")
    config.set("COLORS", "black_piece_color", "colorama.Fore.BLACK")
    config.set("COLORS", "white_piece_color", "colorama.Fore.WHITE")
    config.set("COLORS", "bolder_char_color", "colorama.Style.BRIGHT")

    with open("chessTerminal.ini", "w") as configfile:
        config.write(configfile)


def save_PGN(board, args, result):
    pgn = chess.pgn.Game().from_board(board)
    pgn.headers["Date"] = time.strftime("%Y.%m.%d")
    pgn.headers["Result"] = board.result(claim_draw=True) if result is None else result
    pgn.headers["Event"] = "chess_terminal"
    pgn.headers["Site"] = "https://gitlab.com/Tz2/chess_terminal"

    if args.opponent is None:
        pgn.headers["White"] = "Player"
        pgn.headers["Black"] = "Player"
    elif args.opponent == 1:
        if args.side.lower() == "white" or args.side.lower() == "w":
            pgn.headers["White"] = "Player"
            pgn.headers["Black"] = "Engine"
        elif args.side.lower() == "black" or args.side.lower() == "b":
            pgn.headers["Black"] = "Player"
            pgn.headers["White"] = "Engine"
    elif args.opponent == 2:
        pgn.headers["White"] = "Engine"
        pgn.headers["Black"] = "Engine"

    if not os.path.exists("PGNs"):
        os.mkdir("PGNs")
    with open("PGNs/" + str(uuid.uuid4()) + ".pgn", "w") as pgn_file:
        pgn_file.write(str(pgn) + "\n\n")


def main():
    args = args_init()
    conf_file_name = "chessTerminal.ini"

    if not pathlib.Path(conf_file_name).is_file():
        write_config()
    try:
        if args.config:
            conf_file_name = args.config

        if args.opponent is not None:
            conf = read_config(conf_file_name, engine_on=True)
        else:
            conf = read_config(conf_file_name, engine_on=False)
    except ValueError:
        print("Need to set the path to the chess engine in chessTerminal.ini!")
        return

    colorama.init()
    board = MyBoard()

    if args.opponent is not None:
        print("ENGINE")
        try:
            engine = chess.uci.popen_engine(conf["chess_engine"])
        except FileNotFoundError:
            print("Chess engine not found!")
            raise SystemExit
        engine.uci()
        engine.isready()

        print("\nEngine:")
        print(engine.name)
        print(engine.author)

        if not engine.is_alive():
            print("Engine not alive!")
            return

    print("\nType(?) to show valid moves and (resign), to resign.\n")
    print("Board")

    if args.noColor:
        print(board.no_color(conf), end="\n\n")
    else:
        print(board.colored(conf, args.small), end="\n\n")

    result = None

    while not board.is_game_over(claim_draw=True):
        turn = board.turn
        move_count = board.fullmove_number

        if args.opponent is None:
            if board.turn:
                move = player_turn(board, "White")
            else:
                move = player_turn(board, "Black")
        elif args.opponent == 1:
            if (args.side.lower() == "white" or args.side.lower() == "w") and board.turn:
                move = player_turn(board, "White")
            elif (args.side.lower() == "black" or args.side.lower() == "b") and not board.turn:
                move = player_turn(board, "Black")
            elif board.turn:
                move = engine_turn(engine, board, "White", args.time)
            else:
                move = engine_turn(engine, board, "Black", args.time)
        elif args.opponent == 2:
            if board.turn:
                move = engine_turn(engine, board, "White", args.time)
            else:
                move = engine_turn(engine, board, "Black", args.time)

        if turn:
            if move == "resign":
                print("White resigned.")
                result = "0-1"
                break
            print(f"White ({move_count}): {move}")
        else:
            if move == "resign":
                print("Black resigned.")
                result = "1-0"
                break
            print(f"Black ({move_count}): {move}")

        if args.noColor:
            print(board.no_color(conf), end="\n\n")
        else:
            print(board.colored(conf, args.small), end="\n\n")

        if board.is_checkmate():
            print("CHECKMATE")
        elif board.is_stalemate():
            print("STALEMATE")
        elif board.is_check():
            print("CHECK")

    if result is None:
        print(f"Result: {board.result(claim_draw=True)}")
    else:
        print(f"Result: {result}")

    if args.pgn:
        save_PGN(board, args, result)

if __name__ == "__main__":
    print("chess_terminal Copyright (C) 2018  Kovács József Miklós <kovacsjozsef7u@gmail.com>\n"
          "This program comes with ABSOLUTELY NO WARRANTY;\n"
          "This is free software, and you are welcome to redistribute it\n"
          "under certain conditions; See COPYING for details or\nhttps://www.gnu.org/licenses/gpl-3.0.txt\n")
    main()
