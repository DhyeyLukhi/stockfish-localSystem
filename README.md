# ♟️ Chess Game Review (Stockfish Powered)

Analyze your chess games locally using **Stockfish** and
**python-chess** to receive a detailed review of every move.

> 🎯 The goal of this project is to help you understand **why** your
> moves were good or bad, completely offline.

------------------------------------------------------------------------

# ✨ Features

-   🧠 Stockfish-powered analysis
-   📖 Opening book (Polyglot) support
-   📊 Evaluation bar after every move
-   🎯 Move labels
    -   BOOK
    -   BRILLIANT
    -   GREAT
    -   BEST
    -   EXCELLENT
    -   GOOD
    -   INACCURACY
    -   MISTAKE
    -   MISS
    -   BLUNDER
-   📈 Accuracy calculation for both players
-   📋 Final move breakdown
-   ⚙️ Configurable engine search (Depth / Nodes)

------------------------------------------------------------------------

# 📦 Requirements

-   Python 3
-   python-chess
-   Stockfish
-   Polyglot opening book (optional)

Install dependencies:

``` bash
pip install python-chess
```

------------------------------------------------------------------------

# 🚀 How to Use

Place your PGN file in the same folder (or provide its path), then run:

``` bash
python3 stock.py game.pgn
```

Example:

``` bash
python3 stock.py my_game.pgn
```

------------------------------------------------------------------------

# ⚠️ Important Notice

## This is **NOT** an official Chess.com Game Review clone.

This project is inspired by Chess.com's Game Review, but **it does not
and cannot perfectly reproduce its results**.

That is completely normal.

### 🤔 Why can the results differ?

-   ♟️ Chess.com and this project use different review pipelines.
-   🧠 Chess.com's Game Review is proprietary and not publicly
    documented.
-   🔄 Chess.com has changed its Game Review methodology over the years.
-   🚀 Different Stockfish versions can evaluate the same position
    differently.
-   🔍 Search depth, node limits, MultiPV, pruning and other engine
    settings affect evaluations.
-   📈 Even tiny evaluation differences can change move labels.

Because of this, you may sometimes see different:

-   ✅ Best moves
-   ✅ Move labels
-   ✅ Evaluation scores
-   ✅ Accuracy percentages

**Neither review is necessarily "wrong". They simply use different
analysis pipelines.**

------------------------------------------------------------------------

# 💡 What this project is for

Even if the results are not identical to Chess.com's review, this tool
gives a very strong understanding of your game by helping you:

-   🔎 Find mistakes and blunders
-   💡 Discover stronger moves
-   ⚠️ Identify critical turning points
-   📊 Understand evaluation swings
-   📚 Learn from your games and improve

If your goal is to become a stronger chess player, this project provides
an excellent local analysis without requiring an internet connection.

------------------------------------------------------------------------

# ⚖️ Disclaimer

Chess.com is a proprietary platform, and its complete Game Review
algorithm is **not public**.

This project is an independent implementation built using Stockfish and
publicly observable behaviour. It is intended for learning,
experimentation and personal improvement.

So if your review differs from Chess.com's review, **that is expected**.
