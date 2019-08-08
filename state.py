#!/usr/bin/python3

import math
from itertools import product

# -----------------------------------------
# c = [0 | 1] (white | black)
# [King, Queen, Bishop, Knight, Rook, Pawn]
# [0   , 1    , 2     , 3     , 4   , 5   ]
# -----------------------------------------


class State:
    # Pieces
    KING = 0
    QUEEN = 1
    BISHOP = 2
    KNIGNT = 3
    ROOK = 4
    PAWN = 5
    # Index to type map
    PIECE_TYPE = [4, 3, 2, 1, 0, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5]
    # Moves
    DIAGONALS = [(1, 1), (-1, -1), (1, -1), (-1, 1)]
    LINEAR = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    JUMPS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (2, -1), (2, 1), (1, -2), (1, 2)]

    def __init__(self):
        self.mat = [[-1 for j in range(8)] for i in range(8)]  # idx[][]
        self.pieces = [(-1, -1) for p in range(32)]  # [(i, j)]
        self.actions = []  # [(idx, di, dj, idx')]
        self.init_board()

    def init_board(self):
        indices = [(c, j) for c, j in product(range(2), range(8))]
        for c, j in indices:
            self.add_piece(c, j, 7 if c == 0 else 0, j)
            self.add_piece(c, j + 8, 6 if c == 0 else 1, j)

    def add_piece(self, c, p, i, j):
        idx = State.pack(c, p)
        self.mat[i][j] = idx
        self.pieces[idx] = (i, j)

    def push_action(self, idx, action):
        i, j = self.pieces[idx]
        ip, jp = action
        idxp = self.mat[ip][jp]
        self.mat[i][j] = -1
        self.mat[ip][jp] = idx
        self.pieces[idx] = (ip, jp)
        if idxp > -1:
            self.pieces[idxp] = (-1, -1)
        self.actions.append((idx, ip - i, jp - j, idxp))

    def pop_action(self):
        idx, di, dj, idxp = self.actions.pop()
        i, j = self.pieces[idx]
        self.mat[i][j] = idxp
        if idxp > -1:
            self.pieces[idxp] = (i, j)
        i, j = (i - di, j - dj)
        self.mat[i][j] = idx
        self.pieces[idx] = (i, j)

    def print(self):
        line = (8 * 3 + 1) * "-"
        print(line)
        for row in self.mat:
            print("[" + ",".join("%2d" % p if p > -1 else "  " for p in row) + "]")
        print(line)

    def check_consistency(self):
        for idx, p in enumerate(self.pieces):
            if p != (-1, -1) and self.mat[p[0]][p[1]] != idx:
                print("Pieces %d -> %s; Mat -> %d" % (idx, str(p), self.mat[p[0]][p[1]]))
        indices = [(i, j) for i, j in product(range(8), range(8))]
        for i, j in indices:
            mat_idx = self.mat[i][j]
            if mat_idx > -1 and self.pieces[mat_idx] != (i, j):
                print(
                    "Mat (%d, %d) -> %d; Pieces -> %s" % (i, j, mat_idx, str(self.pieces[mat_idx]))
                )

    def get_idx(self, i, j):
        return self.mat[i][j] if (i >= 0 and i < 8 and j >= 0 and j < 8) else -1

    def get_piece(self, i, j):
        idx = self.get_idx(i, j)
        return State.unpack(idx)

    @staticmethod
    def piece_type(p):
        return State.PIECE_TYPE[p]

    @staticmethod
    def pack(c, p):
        """(color, piece) -> idx"""
        return c * 16 + p

    @staticmethod
    def unpack(idx):
        """idx -> (color, piece, type)"""
        return (
            (math.floor(idx / 16), idx % 16, State.PIECE_TYPE[idx % 16])
            if idx >= 0 and idx < 32
            else (-1, -1, -1)
        )

    # Actions
    def in_bounds(self, i, j):
        return i >= 0 and i < 8 and j >= 0 and j < 8

    def get_color(self, i, j):
        c, _, _ = self.get_piece(i, j)
        return c

    def is_king_checked(self, idx, action):
        """Control if the king is checked"""
        c, _, _ = State.unpack(idx)
        self.push_action(idx, action)
        king_idx = State.pack(c, 4)
        i, j = self.pieces[king_idx]
        for di, dj in State.DIAGONALS + State.LINEAR:
            for k in range(1, 8):
                ip, jp = i + di * k, j + dj * k
                cp, _, tp = self.get_piece(ip, jp)
                if not self.in_bounds(ip, jp) or cp == c:
                    break
                checked = False
                # King neighbor
                checked |= tp == State.KING and k == 1
                # Diagonal pawn
                checked |= tp == State.PAWN and abs(dj * k) == 1 and di == (c * 2 - 1)
                # Diagonal checks
                checked |= (tp == State.BISHOP or tp == State.QUEEN) and (di, dj) in State.DIAGONALS
                # Linear checked
                checked |= (tp == State.ROOK or tp == State.QUEEN) and (di, dj) in State.LINEAR
                if checked:
                    self.pop_action()
                    return True
                # Line of sight hit a piece, exit
                if cp != -1:
                    break
        # # Knight moves
        for di, dj in State.JUMPS:
            ip, jp = i + di, j + dj
            cp, _, tp = self.get_piece(ip, jp)
            if not self.in_bounds(ip, jp) or cp == c:
                continue
            if tp == State.KNIGNT:
                self.pop_action()
                return True
        self.pop_action()
        return False

    def get_actions(self, idx):
        # list [(i, j)]
        c, p, t = State.unpack(idx)
        i, j = self.pieces[idx]
        pos = []

        # Routine to append action if checked
        def append_if_not_checked(action):
            if not self.is_king_checked(idx, action):
                pos.append(action)

        # King
        if t == 0:
            for di, dj in State.DIAGONALS + State.LINEAR:
                ip, jp = i + di, j + dj
                cp = self.get_color(ip, jp)
                if not self.in_bounds(ip, jp) or cp == c:
                    continue
                append_if_not_checked((ip, jp))
        # Queen
        if t == 1:
            for di, dj in State.DIAGONALS + State.LINEAR:
                for k in range(1, 8):
                    ip, jp = i + di * k, j + dj * k
                    cp = self.get_color(ip, jp)
                    if not self.in_bounds(ip, jp) or cp == c:
                        break
                    append_if_not_checked((ip, jp))
                    if cp != -1:
                        break
        # Bishop
        if t == 2:
            for di, dj in State.DIAGONALS:
                for k in range(1, 8):
                    ip, jp = i + di * k, j + dj * k
                    cp = self.get_color(ip, jp)
                    if not self.in_bounds(ip, jp) or cp == c:
                        break
                    append_if_not_checked((ip, jp))
                    if cp != -1:
                        break
        # Knight
        if t == 3:
            for di, dj in State.JUMPS:
                ip, jp = i + di, j + dj
                cp = self.get_color(ip, jp)
                if not self.in_bounds(ip, jp) or cp == c:
                    continue
                append_if_not_checked((ip, jp))
        # Rook
        if t == 4:
            for di, dj in State.LINEAR:
                for k in range(1, 8):
                    ip, jp = i + di * k, j + dj * k
                    cp = self.get_color(ip, jp)
                    if not self.in_bounds(ip, jp) or cp == c:
                        break
                    append_if_not_checked((ip, jp))
                    if cp != -1:
                        break
        # Pawn
        if t == 5:
            limit = 3 if (c == 0 and i == 6) or (c == 1 and i == 1) else 2
            direction = c * 2 - 1
            for di in range(1, limit):
                ip = i + di * direction
                cp = self.get_color(ip, j)
                if not self.in_bounds(ip, j) or cp != -1:
                    break
                append_if_not_checked((ip, j))
                if cp != -1:
                    break
            for di, dj in [(1, -1), (1, 1)]:
                ip = i + di * direction
                jp = j + dj
                cp = self.get_color(ip, jp)
                if cp == (c + 1) % 2:
                    append_if_not_checked((ip, jp))
        return pos


if __name__ == "__main__":
    """Unit test"""
    state = State()
    state.print()
    state.check_consistency()
    state.push_action((10, -1, 0, -1))
    state.print()
    state.check_consistency()
    state.pop_action()
    state.print()
    state.check_consistency()
