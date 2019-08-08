#!/usr/bin/python3

import pygame as pyg
from board import Board


class Cons:
    WIDTH = 320
    HEIGHT = 320
    FPS = 60


def quit(event):
    return event.type == pyg.QUIT or (event.type == pyg.KEYDOWN and event.key == pyg.K_ESCAPE)


def main():
    pyg.init()
    screen = pyg.display.set_mode((Cons.WIDTH, Cons.HEIGHT))  # pyg.RESIZABLE
    clock = pyg.time.Clock()

    # Initialize objects
    board = Board()

    objects = [board]

    # Main loop
    while True:
        for event in pyg.event.get():
            if quit(event):
                return
        for ob in objects:
            ob.event(event)
            ob.draw(screen)

        pyg.display.flip()
        clock.tick(Cons.FPS)


main()
