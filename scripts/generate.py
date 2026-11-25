#!/usr/bin/env python3
"""Generate daily puzzles for Daily Countdown.

Each day gets 3 letters rounds, 2 numbers rounds and 1 conundrum.
Puzzles are deterministic: the same date always produces the same puzzle,
so you can regenerate safely at any time.

Usage (from the repo root):
    python3 scripts/generate.py                 # today until end of 2028
    python3 scripts/generate.py 2027-01-01 2027-12-31
"""
import base64, datetime as dt, json, os, random, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS = [w.strip() for w in open(os.path.join(ROOT, "data", "words.txt")) if w.strip()]
WORDSET = set(WORDS)
COMMON9 = [w.strip() for w in open(os.path.join(ROOT, "data", "common9.txt")) if w.strip()]
OUT = os.path.join(ROOT, "puzzles")

# Letter frequencies modelled on the TV show's piles
VOWELS = {"A": 15, "E": 21, "I": 13, "O": 13, "U": 5}
CONSONANTS = {"B": 2, "C": 3, "D": 6, "F": 2, "G": 3, "H": 2, "J": 1, "K": 1, "L": 5,
              "M": 4, "N": 8, "P": 4, "Q": 1, "R": 9, "S": 9, "T": 9, "V": 1, "W": 1,
              "X": 1, "Y": 1, "Z": 1}
LARGE = [25, 50, 75, 100]
SMALL = [n for n in range(1, 11) for _ in range(2)]

# Pre-index words by letter counts for quick letters-round solving
WORD_COUNTS = [(w, Counter(w)) for w in WORDS if len(w) >= 3]


def pile(d):
    return [k for k, v in d.items() for _ in range(v)]


def words_from(letters):
    pool = Counter(letters.lower())
    found = [w for w, c in WORD_COUNTS if len(w) <= 9 and all(pool[k] >= n for k, n in c.items())]
    found.sort(key=lambda w: (-len(w), w))
    return found


def letters_round(rng):
    for _ in range(200):
        nv = rng.choices([3, 4, 5], weights=[40, 45, 15])[0]
        v = rng.sample(pile(VOWELS), nv)
        c = rng.sample(pile(CONSONANTS), 9 - nv)
        if "Q" in c and "U" not in v:
            continue
        if max(Counter(v + c).values()) > 2:
            continue  # no letter more than twice keeps rounds playable
        letters = v + c
        rng.shuffle(letters)
        letters = "".join(letters)
        found = words_from(letters)
        if found and len(found[0]) >= 6:
            return {"letters": letters, "words": found}
    raise RuntimeError("could not make letters round")


def solve_numbers(nums):
    """Return {value: expr} reachable using subsets; expr = int or (op, a, b)."""
    n = len(nums)
    reach = [dict() for _ in range(1 << n)]
    size = [bin(m).count("1") for m in range(1 << n)]
    for i, x in enumerate(nums):
        reach[1 << i][x] = x
    for mask in sorted(range(1, 1 << n), key=lambda m: size[m]):
        if size[mask] < 2:
            continue
        r = reach[mask]
        sub = (mask - 1) & mask
        while sub:
            other = mask ^ sub
            if sub < other:
                for a, ea in reach[sub].items():
                    for b, eb in reach[other].items():
                        cands = [(a + b, ("+", ea, eb)), (a * b, ("×", ea, eb))]
                        if a > b: cands.append((a - b, ("−", ea, eb)))
                        if b > a: cands.append((b - a, ("−", eb, ea)))
                        if b > 1 and a % b == 0: cands.append((a // b, ("÷", ea, eb)))
                        if a > 1 and b % a == 0: cands.append((b // a, ("÷", eb, ea)))
                        for v, e in cands:
                            if v not in r:
                                r[v] = e
            sub = (sub - 1) & mask
    best = {}
    for mask in sorted(range(1, 1 << n), key=lambda m: size[m]):
        for v, e in reach[mask].items():
            best.setdefault(v, e)
    return best


def steps(e, out):
    if isinstance(e, int):
        return e
    op, a, b = e
    x, y = steps(a, out), steps(b, out)
    if op in "+×" and y > x:
        x, y = y, x
    v = {"+": x + y, "−": x - y, "×": x * y, "÷": x // y if y else 0}[op]
    out.append(f"{x} {op} {y} = {v}")
    return v


def numbers_round(rng):
    nl = rng.choices([0, 1, 2, 3, 4], weights=[8, 35, 37, 12, 8])[0]
    nums = rng.sample(LARGE, nl) + rng.sample(SMALL, 6 - nl)
    nums.sort(reverse=True)
    best = solve_numbers(nums)
    for _ in range(500):
        t = rng.randint(101, 999)
        if t in best and t not in nums:
            out = []
            steps(best[t], out)
            return {"numbers": nums, "target": t, "solution": out}
    return numbers_round(rng)


def conundrum_candidates():
    sig = Counter("".join(sorted(w)) for w in WORDS if len(w) == 9)
    good = []
    for w in COMMON9:
        if sig["".join(sorted(w))] != 1:
            continue  # must have exactly one answer
        if w.endswith("s") and w[:-1] in WORDSET:
            continue  # skip simple plurals
        good.append(w)
    random.Random("daily-countdown-conundrums").shuffle(good)
    return good


def scramble(word, rng):
    for _ in range(100):
        s = list(word)
        rng.shuffle(s)
        s = "".join(s)
        if s != word and all(s[i] != word[i] for i in range(3)):
            return s.upper()
    return word[::-1].upper()


def encode(obj, key):
    raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode()
    k = key.encode()
    return base64.b64encode(bytes(b ^ k[i % len(k)] for i, b in enumerate(raw))).decode()


EPOCH = dt.date(2026, 11, 1)


def main():
    start = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    end = dt.date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else dt.date(2028, 12, 31)
    os.makedirs(OUT, exist_ok=True)
    cons = conundrum_candidates()
    d = start
    while d <= end:
        rng = random.Random(f"daily-countdown-{d.isoformat()}")
        num = (d - EPOCH).days + 1
        answer = cons[(num - 1) % len(cons)]
        puzzle = {
            "date": d.isoformat(),
            "number": num,
            "rounds": [
                {"type": "letters", **letters_round(rng)},
                {"type": "letters", **letters_round(rng)},
                {"type": "numbers", **numbers_round(rng)},
                {"type": "letters", **letters_round(rng)},
                {"type": "numbers", **numbers_round(rng)},
                {"type": "conundrum", "scramble": scramble(answer, rng), "answer": answer.upper()},
            ],
        }
        with open(os.path.join(OUT, f"{d.isoformat()}.json"), "w") as f:
            json.dump({"date": d.isoformat(), "data": encode(puzzle, d.isoformat())}, f)
        d += dt.timedelta(days=1)
    print(f"Generated {start} to {end}. {len(cons)} conundrum words available.")


if __name__ == "__main__":
    main()
