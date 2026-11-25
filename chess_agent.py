"""Depth-limited minimax with alpha-beta pruning and a small evaluation function."""

from math import inf
from time import monotonic

import chess


PIECE_VALUES = (0, 100, 320, 330, 500, 900)
CENTER = chess.BB_D4 | chess.BB_E4 | chess.BB_D5 | chess.BB_E5
HOME_RANK = {chess.WHITE: chess.BB_RANK_1, chess.BLACK: chess.BB_RANK_8}
CLOCK_RESERVE = 1.8
MATE = 100_000


class SearchTimeout(Exception):
    """The current depth did not finish within the move budget."""


def terminal_score(board):
    """Return a White-perspective score for an ending, or None if play continues."""
    if not any(board.generate_legal_moves()):
        if board.is_check():
            return -MATE if board.turn == chess.WHITE else MATE
        return 0
    if board.is_insufficient_material() or board.halfmove_clock >= 100 or board.is_repetition(3):
        return 0
    return None


def position_score(board):
    """Weight material, center occupancy, and minor-piece development."""
    score = 0
    for piece_type in range(chess.PAWN, chess.KING):
        white = board.pieces_mask(piece_type, chess.WHITE)
        black = board.pieces_mask(piece_type, chess.BLACK)
        score += PIECE_VALUES[piece_type] * (white.bit_count() - black.bit_count())
        if piece_type <= chess.BISHOP:
            score += 18 * ((white & CENTER).bit_count() - (black & CENTER).bit_count())
        if piece_type in (chess.KNIGHT, chess.BISHOP):
            developed_white = (white & ~HOME_RANK[chess.WHITE]).bit_count()
            developed_black = (black & ~HOME_RANK[chess.BLACK]).bit_count()
            score += 12 * (developed_white - developed_black)
    return score


def evaluate(fen):
    board = chess.Board(fen)
    outcome = terminal_score(board)
    return position_score(board) if outcome is None else outcome


def ordered_moves(board):
    """Try promotions and valuable captures early to tighten the bounds."""
    def priority(move):
        victim = board.piece_type_at(move.to_square)
        if board.is_en_passant(move):
            victim = chess.PAWN
        attacker = board.piece_type_at(move.from_square)
        capture = 0
        if victim:
            capture = 10 * PIECE_VALUES[victim] - PIECE_VALUES[min(attacker, chess.QUEEN)]
        promotion = PIECE_VALUES[move.promotion] if move.promotion else 0
        return promotion + capture

    return sorted(board.legal_moves, key=priority, reverse=True)


def search(board, depth, alpha, beta, pruning, deadline=None, preferred=None):
    """Return (White's value, visited positions, best move) for a subtree."""
    if deadline is not None and monotonic() >= deadline:
        raise SearchTimeout
    outcome = terminal_score(board)
    if outcome is not None:
        return outcome, 1, None
    if depth == 0:
        return position_score(board), 1, None

    maximizing = board.turn == chess.WHITE
    best_value = -inf if maximizing else inf
    best_move = None
    nodes = 1
    moves = ordered_moves(board) if pruning else list(board.legal_moves)
    if preferred in moves:
        moves.remove(preferred)
        moves.insert(0, preferred)
    for move in moves:
        board.push(move)
        try:
            value, child_nodes, _ = search(board, depth - 1, alpha, beta, pruning, deadline)
        finally:
            board.pop()
        nodes += child_nodes
        if (maximizing and value > best_value) or (not maximizing and value < best_value):
            best_value, best_move = value, move
        if pruning:
            if maximizing:
                alpha = max(alpha, best_value)
            else:
                beta = min(beta, best_value)
            if alpha >= beta:
                break
    return best_value, nodes, best_move


def minimax(fen, depth):
    value, nodes, _ = search(chess.Board(fen), depth, -inf, inf, False)
    return {"value": value, "nodes": nodes}


def alphabeta(fen, depth):
    value, nodes, _ = search(chess.Board(fen), depth, -inf, inf, True)
    return {"value": value, "nodes": nodes}


def act(observation):
    started = monotonic()
    legal = observation["legal_moves"]
    if not legal:
        return {"move": "resign"}
    fallback = legal[0]
    remaining = observation["time_remaining_s"]
    if len(legal) == 1 or remaining <= CLOCK_RESERVE:
        return {"move": fallback}
    turn_cap = 0.021 if observation["ply"] < 40 else 0.011
    deadline = started + min(turn_cap, (remaining - CLOCK_RESERVE) / 40)

    board = chess.Board()
    for move in observation["history"]:
        board.push_uci(move)
    if board.fen() != observation["fen"]:
        board = chess.Board(observation["fen"])

    completed_depth = 0
    completed_nodes = 0
    preferred = None
    for depth in range(1, 5):
        try:
            value, nodes, move = search(board, depth, -inf, inf, True, deadline, preferred)
        except SearchTimeout:
            break
        if move is not None and move.uci() in legal:
            fallback = move.uci()
            completed_depth = depth
            completed_nodes += nodes
            preferred = move
        if abs(value) == MATE:
            break
    print("search", completed_depth, completed_nodes)
    return {"move": fallback}
