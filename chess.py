import tkinter as tk
from board import Board
from state import State
from ai import baseline_evaluator, min_max


class Chess:
    def __init__(self):
        self.root = tk.Tk()
        # Create frame
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH)
        # Create board
        self.board = Board(frame, on_update=self.on_update)
        self.state = State()
        self.board.state = self.state
        # Show frame
        self.board.pack(side=tk.LEFT, fill=tk.BOTH, padx=2, pady=2)
        self.create_menu(frame)
        # Force root to show
        self.root.lift()
        self.root.attributes("-topmost", True)
        self.root.after_idle(self.root.attributes, "-topmost", False)
        self.root.mainloop()

    def create_menu(self, frame):
        # Create menu
        menu_frame = tk.Frame(frame)
        menu_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        # Eval label
        self.eval_lbl = tk.Label(menu_frame, fg="dark green")
        self.eval_lbl.pack(side=tk.TOP)
        self.on_update()
        # Min max btn
        minmax_btn = tk.Button(menu_frame, width=16, text="MinMax", command=self.minmax)
        minmax_btn.pack(side=tk.TOP)
        # Take back btn
        take_back_btn = tk.Button(menu_frame, width=16, text="Take back", command=self.take_back)
        take_back_btn.pack(side=tk.TOP)
        # Exit btn
        exit_btn = tk.Button(menu_frame, width=16, text="Exit", command=self.root.destroy)
        exit_btn.pack(side=tk.BOTTOM)

    def minmax(self):
        (idx, action), value = min_max(self.state)
        print((idx, action), value)
        self.state.push_action(idx, action)
        self.board.redraw()

    def take_back(self):
        self.state.pop_action()
        self.board.redraw()

    def on_update(self):
        # Redraw label
        value = baseline_evaluator(self.state, State.WHITE)
        self.eval_lbl.config(text="eval: " + str(value))


if __name__ == "__main__":
    chess = Chess()
