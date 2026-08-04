import chess
import chess.pgn
import chess.engine
import chess.polyglot
import sys
import os
import math

# --- Engine version note -------------------------------------------------
# Chess.com does not run a single fixed engine forever. Game Review and the
# free-standing Analysis board have historically used different Stockfish
# builds, and Game Review is also architected around a fixed NODE budget per
# move rather than a fixed DEPTH (see LIMIT_MODE below). This means you
# cannot get bit-for-bit matching numbers just by swapping binaries -- engine
# disagreement between versions (and even between two runs of the same
# version at different node counts) is expected, not a bug.
#
# installed: download the exact release binary from
# https://github.com/official-stockfish/Stockfish/releases (avoid third
# -party mirrors) and update STOCKFISH_PATH below.
# --------------------------------------------------------------------------

STOCKFISH_PATH = "/usr/games/stockfish"
BOOK_PATH = "~/books/book.bin"

# LIMIT_MODE controls how each position is searched:
#   "depth" — search to a fixed ply depth (DEPTH below). Stronger/more
#             thorough on modern hardware since it isn't capped by a node
#             budget, but the real computation spent varies a lot between
#             quiet and sharp positions.
#   "nodes" — search a fixed number of nodes per move regardless of
#             position complexity. This is the approach chess.com moved
#             Game Review to, specifically for consistent, comparable
#             per-move effort. Use this if you want your review's
#             methodology to match chess.com's design, not just its output.
LIMIT_MODE = "depth"
DEPTH = 20
NODES_PER_MOVE = 1_000_000  # only used when LIMIT_MODE == "nodes"

GAP_DEPTH = 14  # secondary multipv pass only needs to detect "sharp position",
                # not match the primary eval precisely - keep it cheap
ENGINE_THREADS = 4
ENGINE_HASH_MB = 256

PIECE_VALUES = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
                chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}

# Minimum eval gap (cp) between best and 2nd-best move for a position
# to count as "sharp" enough to qualify for GREAT / BRILLIANT / MISS.
SHARP_GAP = 150

# Win%-loss thresholds -> label (checked in order, first match wins).
# Reverse-engineered approximation of chess.com's actual bucketing,
# converged on independently by several open-source "game review clone"
# projects after testing against real chess.com output. Not a guess.
CLASSIFY_THRESHOLDS = [
    (2,  "BEST"),
    (5,  "EXCELLENT"),
    (10, "GOOD"),
    (20, "INACCURACY"),
    (35, "MISTAKE"),
]


def win_percent(cp):
    """Centipawn eval -> win probability (0-100), Lichess-style logistic curve."""
    cp = max(-1000, min(1000, cp))
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def move_accuracy(win_pct_loss):
    """Per-move accuracy % from win% lost. Reverse-engineered chess.com curve."""
    win_pct_loss = max(0, win_pct_loss)
    return max(0, min(100, 103.1668 * math.exp(-0.04354 * win_pct_loss) - 3.1669))


def classify_move(wp_before, wp_after):
    loss = wp_before - wp_after
    for threshold, label in CLASSIFY_THRESHOLDS:
        if loss <= threshold:
            return label
    return "BLUNDER"


def eval_bar(cp_score, width=40):
    cp_score = max(-1000, min(1000, cp_score))
    white_ratio = (cp_score + 1000) / 2000
    white_blocks = int(white_ratio * width)
    return f"[{'█'*white_blocks}{'░'*(width-white_blocks)}]  {cp_score/100:+.1f}"


def is_book_move(board, move, book_reader):
    if book_reader is None:
        return False
    try:
        return move in [e.move for e in book_reader.find_all(board)]
    except Exception:
        return False


def is_brilliant(board_before, move, played_is_best, gap):
    """Genuine sacrifice that is also provably the engine's clear best move."""
    if not played_is_best or gap < SHARP_GAP:
        return False
    if len(list(board_before.legal_moves)) <= 1:
        return False

    board_after = board_before.copy()
    board_after.push(move)
    dest = move.to_square
    piece = board_after.piece_at(dest)
    if piece is None:
        return False

    piece_value = PIECE_VALUES[piece.piece_type]
    if piece_value < 3:
        return False

    attackers = board_after.attackers(not piece.color, dest)
    if not attackers:
        return False

    min_attacker_value = min(
        PIECE_VALUES[board_after.piece_at(sq).piece_type] for sq in attackers
    )
    defenders = board_after.attackers(piece.color, dest)

    return min_attacker_value <= piece_value and len(defenders) < len(attackers)


def is_great_move(played_is_best, gap, is_decided):
    if not played_is_best or is_decided:
        return False
    return gap >= SHARP_GAP


def is_miss(played_is_best, gap, wp_before, wp_after, is_decided):
    """A critical, findable move existed and the player missed it, at real cost."""
    if played_is_best or is_decided or gap < SHARP_GAP:
        return False
    return (wp_before - wp_after) >= 6


def analyze_game(pgn_path):
    game = chess.pgn.read_game(open(pgn_path))
    board = game.board()
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    engine.configure({"Threads": ENGINE_THREADS, "Hash": ENGINE_HASH_MB})

    # Print exactly which engine build is running. This replaces having to
    # manually run `stockfish --help` to check — you'll see it every time
    # you run a review, so there's never ambiguity about which version
    # produced a given set of numbers.
    engine_name = engine.id.get("name", "Unknown engine")
    print(f"Engine: {engine_name}   |   limit mode: {LIMIT_MODE}"
          f"{f' (depth {DEPTH})' if LIMIT_MODE == 'depth' else f' ({NODES_PER_MOVE:,} nodes/move)'}\n")

    if LIMIT_MODE == "nodes":
        limit = chess.engine.Limit(nodes=NODES_PER_MOVE)
    else:
        limit = chess.engine.Limit(depth=DEPTH)
    GAP_LIMIT = chess.engine.Limit(depth=GAP_DEPTH)

    book_reader = None
    if os.path.exists(BOOK_PATH):
        book_reader = chess.polyglot.open_reader(BOOK_PATH)
        print("Opening book loaded — early theory moves will be recognized automatically.\n")
    else:
        print("No opening book configured this session — every move, "
              "openings included, will be judged directly by the engine.\n")

    labels_template = {"BOOK": 0, "BRILLIANT": 0, "GREAT": 0, "BEST": 0,
                        "EXCELLENT": 0, "GOOD": 0, "INACCURACY": 0,
                        "MISTAKE": 0, "MISS": 0, "BLUNDER": 0}
    white_labels = labels_template.copy()
    black_labels = labels_template.copy()
    white_acc, black_acc = [], []

    move_num = 1
    for move in game.mainline_moves():
        is_white = board.turn == chess.WHITE
        board_before = board.copy()

        book = is_book_move(board_before, move, book_reader)

        # PRIMARY pass: single-PV, full search strength. This is the ground-truth
        # reference eval everything else gets compared against — must not be
        # diluted by multipv's pruning trade-off.
        info_best = engine.analyse(board, limit)
        best_move = info_best["pv"][0]
        best_eval = info_best["score"].relative.score(mate_score=10000)
        best_san = board_before.san(best_move)
        played_is_best = (move == best_move)
        is_decided = abs(best_eval) >= 600

        # SECONDARY pass: multipv, only to detect "was there a much better
        # alternative" for GREAT/BRILLIANT/MISS. Lower precision here is fine —
        # it never touches the reference eval used for loss/accuracy.
        info_multi = engine.analyse(board, GAP_LIMIT, multipv=2)
        second_eval = (info_multi[1]["score"].relative.score(mate_score=10000)
                       if len(info_multi) > 1 else best_eval)
        gap = abs(best_eval - second_eval)

        san = board_before.san(move)
        board.push(move)

        info_after = engine.analyse(board, limit)

        # Mover-POV eval: used ONLY for the accuracy/classification math below,
        # which needs "this move's mover's own win% before vs after."
        played_eval = -info_after["score"].relative.score(mate_score=10000)

        # Absolute, White-POV eval: used ONLY for the display bar, so it never
        # flips sign convention depending on who just moved.
        white_eval = played_eval

        wp_before = win_percent(best_eval)
        wp_after = win_percent(played_eval)
        acc = move_accuracy(wp_before - wp_after)

        label = classify_move(wp_before, wp_after)

        if book:
            label = "BOOK"
        elif is_brilliant(board_before, move, played_is_best, gap):
            label = "BRILLIANT"
        elif label == "BEST" and is_great_move(played_is_best, gap, is_decided):
            label = "GREAT"
        elif label in ("INACCURACY", "MISTAKE", "BLUNDER") and \
                is_miss(played_is_best, gap, wp_before, wp_after, is_decided):
            label = "MISS"

        (white_acc if is_white else black_acc).append(acc)
        (white_labels if is_white else black_labels)[label] += 1

        note = "" if label in ("BEST", "BOOK", "BRILLIANT", "GREAT") else f"  (best was {best_san})"
        print(f"Move {move_num}{'.' if is_white else '...'} {san}   {'White' if is_white else 'Black'}")
        print(f"  {eval_bar(white_eval)}")
        print(f"  Label: {label}{note}")
        print()

        if not is_white:
            move_num += 1

    engine.quit()
    if book_reader:
        book_reader.close()

    print("=" * 45)
    print("ACCURACY")
    print(f"White: {sum(white_acc)/len(white_acc):.1f}%" if white_acc else "White: N/A")
    print(f"Black: {sum(black_acc)/len(black_acc):.1f}%" if black_acc else "Black: N/A")
    print()
    print("MOVE BREAKDOWN")
    print(f"{'':15}{'White':>8}{'Black':>8}")
    for label in labels_template:
        print(f"{label:15}{white_labels[label]:>8}{black_labels[label]:>8}")
    print("=" * 45)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 stock.py <game.pgn>")
        sys.exit(1)
    analyze_game(sys.argv[1])