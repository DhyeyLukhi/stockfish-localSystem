import requests
import zipfile
import io
import chess.pgn
import re

LICHESS_DB_URL = "https://database.lichess.org/standard/lichess_db_standard_rated_2023-01.pgn.zst"
# NOTE: Lichess monthly dumps are huge (30+ GB compressed) and .zst format.
# Instead, use the Lichess API to pull a bounded number of real rated games directly — much lighter.

import chess.pgn

def fetch_lichess_games(username_pool, games_per_user=20, min_rating=800, max_rating=2400):
    """
    Pull real rated classical/rapid games via the Lichess public API.
    No auth needed for public game export.
    """
    all_pgns = []
    for username in username_pool:
        url = f"https://lichess.org/api/games/user/{username}"
        params = {
            "max": games_per_user,
            "rated": "true",
            "perfType": "blitz,rapid,classical",
            "pgnInJson": "false"
        }
        headers = {"Accept": "application/x-chess-pgn"}
        resp = requests.get(url, params=params, headers=headers)
        if resp.status_code == 200:
            all_pgns.append(resp.text)
        else:
            print(f"Failed for {username}: {resp.status_code}")
    return "\n\n".join(all_pgns)


def save_games(pgn_text, out_path="calibration_games.pgn"):
    with open(out_path, "w") as f:
        f.write(pgn_text)
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    # Use a spread of known active players across rating bands for variety.
    # Replace with any real lichess usernames you like, or pull from leaderboards.
    sample_users = [
        "Arkadiy_Khromaev", "Hooligan64", "nihalsarin2004",
        "RebeccaHarris", "Zhigalko_Sergei", ""
    ]
    pgn_data = fetch_lichess_games(sample_users, games_per_user=15)
    save_games(pgn_data)