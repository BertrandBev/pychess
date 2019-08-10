import tkinter as tk
from PIL import Image, ImageTk
import itertools
from state import State
import math


class Board(tk.Canvas):
    def __init__(self, root, size=64, on_update=None):
        """size is the size of a square, in pixels"""
        super().__init__(root, borderwidth=0, highlightthickness=0, width=8 * size, height=8 * size)
        self.size = size
        self.on_update = on_update
        self.color_white = "white"
        self.color_tile = "#70adc2"
        self.color_selected = "#68ad7c"
        self.color_action = "#68ad7c"
        self.state = None
        # this binding will cause a redraw if the user interactively
        # changes the window size
        self.bind("<Configure>", self.redraw)
        self.bind("<Button-1>", self.on_click)

        # Load pieces
        self.load_pieces()

        # Init game command
        self.selected = -1
        self.actions = []

    def load_pieces(self):
        img = Image.open("pieces.png").convert("RGBA")
        width = 170
        self.piece_img = {}
        for i, j in itertools.product(range(2), range(6)):
            area = (j * width, i * width, (j + 1) * width, (i + 1) * width)
            cropped = img.crop(area)
            cropped = cropped.resize((self.size, self.size), Image.ANTIALIAS)
            self.piece_img[(i, j)] = ImageTk.PhotoImage(cropped)

    def draw_rect(self, i, j, color):
        self.create_rectangle(
            j * self.size,
            i * self.size,
            (j + 1) * self.size,
            (i + 1) * self.size,
            outline="black",
            fill=color,
            tags="square",
        )

    def redraw(self, event=None):
        """Redraw the board, possibly in response to window being resized"""
        if event:
            xsize = int((event.width - 1) / 8)
            ysize = int((event.height - 1) / 8)
            self.size = min(xsize, ysize)
        self.delete("all")
        # Draw the board
        for i, j in itertools.product(range(8), range(8)):
            color = self.color_white if (i + j) % 2 else self.color_tile
            self.draw_rect(i, j, color)

        # Draw selection
        if self.selected >= 0:
            i, j = self.state.pieces[self.selected]
            self.draw_rect(i, j, self.color_selected)
            for i, j in self.actions:
                self.draw_rect(i, j, self.color_action)

        # Draw the pieces
        if self.state:
            for idx, (i, j) in enumerate(self.state.pieces):
                c, p, t = State.unpack(idx)
                image = self.piece_img[(c, t)]
                self.create_image(j * self.size, i * self.size, image=image, anchor="nw")

        # Trigger callback
        if self.on_update:
            self.on_update()

    def on_click(self, event):
        i = math.floor(event.y / self.size)
        j = math.floor(event.x / self.size)
        idx = self.state.get_idx(i, j)
        c, _, _ = self.state.get_piece(i, j)
        if self.selected >= 0 and (i, j) in self.actions:
            # Commit move
            self.state.push_action(self.selected, (i, j))
            self.selected = -1
            # self.state.print()
        elif c >= 0:
            # Select piece
            self.selected = idx
            self.actions = self.state.get_actions(idx)
        else:
            self.selected = -1
        self.redraw()
