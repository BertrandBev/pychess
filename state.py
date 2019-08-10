#!/usr/bin/python3

import math
from utils import timeit
import numba as nb
from numba import njit, jitclass, deferred_type
import numpy as np


# Colors
WHITE = 0
BLACK = 1
# Pieces
KING = 0
QUEEN = 1
BISHOP = 2
KNIGNT = 3
ROOK = 4
PAWN = 5
# Index to type map
PIECE_TYPE = np.int8([4, 3, 2, 1, 0, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5])
KING_IDX = 4
# Moves
DIAGONALS = np.int8([(1, 1), (-1, -1), (1, -1), (-1, 1)])
LINEAR = np.int8([(0, 1), (0, -1), (1, 0), (-1, 0)])
OMNIDIRECTIONAL = np.concatenate((DIAGONALS, LINEAR), axis=0)
JUMPS = np.int8([(-2, -1), (-2, 1), (-1, -2), (-1, 2), (2, -1), (2, 1), (1, -2), (1, 2)])


@njit("int8(int8, int8)")
def pack(c, p):
    """(color, piece) -> idx"""
    return c * 16 + p


@njit("UniTuple(int8, 3)(int8)")
def unpack(idx):
    """idx -> (color, piece, type)"""
    return (
        (math.floor(idx / 16), idx % 16, PIECE_TYPE[idx % 16])
        if idx >= 0 and idx < 32
        else (-1, -1, -1)
    )


# Not a njit to allow formatting
def print_state(state):
    line = (8 * 3 + 1) * "-"
    print(line)
    for i in range(8):
        print("[" + ",".join("%2d" % p if p > -1 else "  " for p in state.mat[i, :]) + "]")
    print(line)


spec = [
    ("mat", nb.int8[:, :]),
    ("pieces", nb.int8[:, :]),
    ("actions", nb.int8[:, :]),
    ("action_idx", nb.int16),
]

# State.class_type.instance_type
@jitclass(spec)
class State:
    def __init__(self):
        self.mat = np.int8([[-1 for j in range(8)] for i in range(8)])
        self.pieces = np.int8([(-1, -1) for p in range(32)])
        self.actions = np.zeros((10 ** 3, 4), dtype=np.int8)
        self.action_idx = 0
        self.init_board()

    def get_idx(self, i, j):
        return self.mat[i, j] if (i >= 0 and i < 8 and j >= 0 and j < 8) else -1

    def get_piece(self, i, j):
        idx = self.get_idx(i, j)
        return unpack(idx)

    def in_bounds(self, i, j):
        return i >= 0 and i < 8 and j >= 0 and j < 8

    def get_color(self, i, j):
        c, _, _ = self.get_piece(i, j)
        return c

    def init_board(self):
        for c in range(2):
            for j in range(8):
                self.set_piece(c, j, 7 if c == 0 else 0, j)
                self.set_piece(c, j + 8, 6 if c == 0 else 1, j)

    def set_piece(self, c, p, i, j):
        idx = pack(c, p)
        self.mat[i, j] = idx
        self.pieces[idx, :] = (i, j)

    def push_action(self, idx, action):
        i, j = self.pieces[idx, :]
        ip, jp = action
        idxp = self.mat[ip, jp]
        self.mat[i, j] = -1
        self.mat[ip, jp] = idx
        self.pieces[idx, :] = (ip, jp)
        if idxp > -1:
            self.pieces[idxp] = (-1, -1)
        self.actions[self.action_idx, :] = np.int8((idx, ip - i, jp - j, idxp))
        self.action_idx += 1

    def pop_action(self):
        if self.action_idx == 0:
            print("Empty action stack")
            return
        self.action_idx -= 1
        idx, di, dj, idxp = self.actions[self.action_idx, :]
        i, j = self.pieces[idx, :]
        self.mat[i, j] = idxp
        if idxp > -1:
            self.pieces[idxp, :] = (i, j)
        i, j = (i - di, j - dj)
        self.mat[i, j] = idx
        self.pieces[idx, :] = (i, j)

    def get_player_color(self):
        """Return next player up"""
        if self.action_idx == 0:
            return 0
        else:
            idx = self.actions[self.action_idx, 0]
            c, _, _ = unpack(idx)
            return (c + 1) % 2

    def is_pieced_checked(self, idx):
        c, _, _ = unpack(idx)
        i, j = self.pieces[idx, :]
        for l in range(OMNIDIRECTIONAL.shape[0]):
            di, dj = OMNIDIRECTIONAL[l, :]
            for k in range(1, 8):
                ip, jp = i + di * k, j + dj * k
                cp, _, tp = self.get_piece(ip, jp)
                if not self.in_bounds(ip, jp) or cp == c:
                    break
                checked = False
                # King neighbor
                checked |= tp == KING and k == 1
                # Diagonal pawn
                checked |= tp == PAWN and abs(dj * k) == 1 and di == (c * 2 - 1)
                # Diagonal checks
                checked |= (tp == BISHOP or tp == QUEEN) and abs(di) == abs(dj)
                # Linear checked
                checked |= (tp == ROOK or tp == QUEEN) and di * dj == 0
                if checked:
                    return True
                # Line of sight hit a piece, exit
                if cp != -1:
                    break
        # # Knight moves
        for l in range(JUMPS.shape[0]):
            di, dj = JUMPS[l, :]
            ip, jp = i + di, j + dj
            cp, _, tp = self.get_piece(ip, jp)
            if not self.in_bounds(ip, jp) or cp == c:
                continue
            if tp == KNIGNT:
                return True
        return False

    def get_actions(self, idx):
        # list [(i, j)]
        c, p, t = unpack(idx)
        i, j = self.pieces[idx, :]
        pos = []  # [(np.int8(0), np.int8(0)) for _ in range(0)]

        # Routine to append action if the king is safe
        def append_if_not_checked(action):
            action = np.int8(action)
            c, _, _ = unpack(idx)
            king_idx = pack(c, KING_IDX)
            self.push_action(idx, action)
            checked = self.is_pieced_checked(king_idx)
            self.pop_action()
            if not checked:
                pos.append(action)

        # King
        if t == 0:
            for l in range(OMNIDIRECTIONAL.shape[0]):
                di, dj = OMNIDIRECTIONAL[l, :]
                ip, jp = i + di, j + dj
                cp = self.get_color(ip, jp)
                if not self.in_bounds(ip, jp) or cp == c:
                    continue
                append_if_not_checked((ip, jp))
        # Queen
        if t == 1:
            for l in range(OMNIDIRECTIONAL.shape[0]):
                di, dj = OMNIDIRECTIONAL[l, :]
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
            for l in range(DIAGONALS.shape[0]):
                di, dj = DIAGONALS[l, :]
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
            for l in range(JUMPS.shape[0]):
                di, dj = JUMPS[l, :]
                ip, jp = i + di, j + dj
                cp = self.get_color(ip, jp)
                if not self.in_bounds(ip, jp) or cp == c:
                    continue
                append_if_not_checked((ip, jp))
        # Rook
        if t == 4:
            for l in range(LINEAR.shape[0]):
                di, dj = LINEAR[l, :]
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

    def is_terminal(self, color):
        king_idx = pack(color, KING_IDX)
        if not self.is_pieced_checked(king_idx):
            return False
        actions = self.get_actions(king_idx)
        return len(actions) > 0

    def get_player_actions(self, color):
        player_actions = []
        for p in range(16):
            idx = pack(color, p)
            actions = self.get_actions(idx)
            if actions:
                player_actions.append((idx, actions))
        return player_actions

    # def check_consistency(self):
    #     for idx, p in enumerate(self.pieces):
    #         if p != (-1, -1) and self.mat[p[0]][p[1]] != idx:
    #             print("Pieces %d -> %s; Mat -> %d" % (idx, str(p), self.mat[p[0]][p[1]]))
    #     indices = [(i, j) for i, j in product(range(8), range(8))]
    #     for i, j in indices:
    #         mat_idx = self.mat[i, j]
    #         if mat_idx > -1 and self.pieces[mat_idx] != (i, j):
    #             print(
    #                 "Mat (%d, %d) -> %d; Pieces -> %s" % (i, j, mat_idx, str(self.pieces[mat_idx]))
    #             )


if __name__ == "__main__":
    """Unit test"""
    state = State()

    # print_state(state)
    # state.push_action(0, (3, 3))
    # print_state(state)
    # state.pop_action()
    # print_state(state)

    # print("color", state.get_player_color())
    # # Is checked
    # for k in range(32):
    #     print(k, "is checked:", state.is_pieced_checked(k))
    # timeit(state.is_pieced_checked, (0,), 1000)
    # Action
    for k in range(32):
        print(k, "actions:", state.get_actions(k))
    timeit(state.get_actions, (1,), 1000)

    # Player actions
    print("player actions", state.get_player_actions(0))
    timeit(state.get_player_actions, (1,), 1000)
