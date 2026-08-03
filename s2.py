import chess
import chess.pgn
import chess.engine
import math

STOCKFISH_PATH = "/usr/games/stockfish"
CALIBRATION_DEPTH = 12  # lower depth = much faster for calibration; trend holds fine at 12

def win_percent(cp):
    cp = max(-1000, min(1000, cp))
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def get_game_acpl(game, engine):
    board = game.board()
    white_cpl, black_cpl = [], []

    for move in game.mainline_moves():
        is_white = board.turn == chess.WHITE
        info_before = engine.analyse(board, chess.engine.Limit(depth=CALIBRATION_DEPTH))
        best_eval = info_before["score"].relative.score(mate_score=10000)

        board.push(move)
        info_after = engine.analyse(board, chess.engine.Limit(depth=CALIBRATION_DEPTH))
        played_eval = -info_after["score"].relative.score(mate_score=10000)

        is_decided = abs(best_eval) >= 600
        if not is_decided:
            cpl = max(0, best_eval - played_eval)
            (white_cpl if is_white else black_cpl).append(cpl)

    w = sum(white_cpl) / len(white_cpl) if white_cpl else None
    b = sum(black_cpl) / len(black_cpl) if black_cpl else None
    return w, b


def build_dataset(pgn_path, max_games=50):
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    data_points = []  # list of (acpl, rating)

    with open(pgn_path) as f:
        count = 0
        while count < max_games:
            game = chess.pgn.read_game(f)
            if game is None:
                break

            white_rating = game.headers.get("WhiteElo")
            black_rating = game.headers.get("BlackElo")
            if not white_rating or not black_rating:
                continue

            try:
                white_rating = int(white_rating)
                black_rating = int(black_rating)
            except ValueError:
                continue

            w_acpl, b_acpl = get_game_acpl(game, engine)
            if w_acpl is not None:
                data_points.append((w_acpl, white_rating))
            if b_acpl is not None:
                data_points.append((b_acpl, black_rating))

            count += 1
            print(f"Processed game {count}/{max_games}")

    engine.quit()
    return data_points


if __name__ == "__main__":
    import pickle
    dataset = build_dataset("calibration_games.pgn", max_games=50)
    with open("acpl_rating_dataset.pkl", "wb") as f:
        pickle.dump(dataset, f)
    print(f"Collected {len(dataset)} data points")