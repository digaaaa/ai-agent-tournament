"""One-ply minimax with a material evaluation, for the Chess comparison."""

import chess

VALUES = (0, 100, 320, 330, 500, 900)


def score(board):
    if board.is_checkmate():
        return -100000 if board.turn == chess.WHITE else 100000
    if board.is_stalemate() or board.is_insufficient_material() or board.halfmove_clock >= 100:
        return 0
    return sum(
        VALUES[piece] * (
            board.pieces_mask(piece, chess.WHITE).bit_count()
            - board.pieces_mask(piece, chess.BLACK).bit_count()
        )
        for piece in range(chess.PAWN, chess.KING)
    )


def act(observation):
    legal = observation["legal_moves"]
    if not legal:
        return {"move": "resign"}
    if len(legal) == 1 or observation["time_remaining_s"] <= 0.35:
        return {"move": legal[0]}
    board = chess.Board(observation["fen"])
    white = board.turn == chess.WHITE
    best_move = legal[0]
    best = -float("inf")
    for uci in legal:
        board.push_uci(uci)
        value = score(board)
        board.pop()
        if not white:
            value = -value
        if value > best:
            best, best_move = value, uci
    print("search", 1, 1 + len(legal))
    return {"move": best_move}
