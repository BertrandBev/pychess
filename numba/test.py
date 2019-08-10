import numba as nb
from numba import njit, jitclass
import time
import numpy as np
import math


def timeit(fun, args, repeat=100):
    start = time.time()
    for k in range(repeat):
        fun(*args)
    end = time.time()
    delta = (end - start) / repeat
    delta_unit = "s"
    for unit in ["ms", "μs", "ns"]:
        if delta > 1:
            break
        delta *= 1000
        delta_unit = unit
    print("Elapsed time {:.3f}{}".format(delta, delta_unit))


spec = [("array", nb.int32[:]), ("matrix", nb.int16[:, :])]


@jitclass(spec)
class State:
    def __init__(self):
        self.array = np.zeros((10), dtype=np.int32)
        self.matrix = np.zeros((2, 20), dtype=np.int16)

    def long_loop(self):
        for i in range(10):
            for j in range(10):
                for k in range(10):
                    self.array[(i + k) % 10] = self.array[j] - self.array[k] + k + 2 * i + 3 * j
                    self.matrix[i % 2, j] = self.array[k]


class Board:
    def __init__(self, state):
        self.state = state

    def test(self):
        self.state.long_loop()


# state = State()
# state.long_loop()
# board = Board(state)
# timeit(board.test, (), repeat=1000)
# timeit(state.long_loop.py_func, (), repeat=1000)


class Const:
    TEST = 0


PIECE_TYPE = np.int8([4, 3, 2, 1, 0, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5])
PIECE_TYPE = [4, 3, 2, 1, 0, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 5]

color = {"WHITE": 1, "BLACK": 2}
VAL = 1


@njit
def unpack(idx):
    """idx -> (color, piece, type)"""
    return (math.floor(idx / 16), idx % 16, PIECE_TYPE[idx % 16]) if PIECE_TYPE[idx % 16] > 0 else (-1, -1, -1)


unpack(12)
timeit(unpack, (12,), repeat=10000)


# @njit(nb.i1(nb.i1, nb.i1))
# def f(x, y):
#     # A somewhat trivial example
#     for k in range(0, 100):
#         for i in range(0, 80):
#             for j in range(0, 100):
#                 x += y
#     return x + y


# print(f(127, 1))
# timeit(f, (1, 2), repeat=1000)
# timeit(f.py_func, (1, 2), repeat=1000)
