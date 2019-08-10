from state import State, KING, QUEEN, ROOK, BISHOP, KNIGNT, PAWN, unpack

MAX_DEPTH = 3
INF = 10 ** 5


def baseline_evaluator(state, color):
    assert color != -1
    PIECE_VALUE = {KING: 4, QUEEN: 9, ROOK: 5, BISHOP: 3, KNIGNT: 3, PAWN: 1}
    value = 0
    for idx, (i, j) in enumerate(state.pieces):
        if i < 0 or j < 0:
            continue
        c, _, t = unpack(idx)
        sign = 1 if c == color else -1
        value += PIECE_VALUE[t] * sign
    return value


def min_max(state, depth=MAX_DEPTH, max_color=None):
    # Find maximizing color
    if max_color is None:
        max_color = state.get_player_color()
    curr_color = state.get_player_color()
    # Terminate if needed
    if state.is_terminal(curr_color):
        return None, INF if curr_color != max_color else -INF
    if depth == 0:
        return None, baseline_evaluator(state, max_color)
    player_actions = state.get_player_actions(curr_color)
    seek_max = curr_color == max_color
    opt_value = -INF if seek_max else INF
    opt_action = None
    for idx, actions in player_actions:
        for action in actions:
            # Simulate action
            state.push_action(idx, action)
            _, value = min_max(state, depth - 1, max_color)
            value = max(opt_value, value) if seek_max else min(opt_value, value)
            if value != opt_value:
                opt_value = value
                opt_action = (idx, action)
            # Pop action
            state.pop_action()
    # print(
    #     "D",
    #     depth,
    #     "color",
    #     curr_color,
    #     "max col",
    #     max_color,
    #     "opt action",
    #     opt_action,
    #     "value",
    #     opt_value,
    # )
    return opt_action, opt_value


if __name__ == "__main__":
    state = State()
    result = min_max(state, depth=4)
