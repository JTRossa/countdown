# Daily Countdown

A daily letters and numbers puzzle in the style of the TV show: three letters rounds, two numbers rounds and a conundrum. Everyone gets the same puzzle on the same date, and a new one appears at midnight local time.

## Put it on GitHub Pages

1. Create a new public repository on GitHub (for example `daily-countdown`).
2. Upload everything in this folder to the repository (drag the files into **Add file → Upload files**, or push with git).
3. In the repo go to **Settings → Pages**, set **Source** to *Deploy from a branch*, choose `main` and `/ (root)`, and save.
4. After a minute the game is live at `https://<your-username>.github.io/daily-countdown/`.

## What's in the repo

| Path | What it is |
|---|---|
| `index.html` | The whole game (HTML, CSS and JavaScript in one file) |
| `puzzles/YYYY-MM-DD.json` | One puzzle per day, 1 Nov 2026 to 31 Dec 2028 |
| `scripts/generate.py` | Makes the puzzle files |
| `data/words.txt` | Dictionary used to check words (about 72,000 words, US and UK spellings) |
| `data/common9.txt` | Common nine-letter words used for conundrums |

## Making more puzzles

Puzzles are generated from the date, so running the script again always produces the same puzzle for the same day.

```bash
python3 scripts/generate.py 2029-01-01 2029-12-31
```

Then commit the new files in `puzzles/`. A year takes about 40 seconds.

## How puzzles are built

- **Letters:** 3 to 5 vowels, drawn using the show's letter frequencies, with no letter more than twice. Every round has at least a six-letter word. All valid words are stored with the puzzle so the game can check answers and show the best ones.
- **Numbers:** 0 to 4 large numbers (25, 50, 75, 100) and small numbers 1 to 10. Every target is guaranteed to be reachable exactly; the stored solution uses as few numbers as possible.
- **Conundrum:** a common nine-letter word with only one possible anagram, scrambled.

Puzzle files are lightly scrambled so answers aren't readable at a glance, but they aren't secret.

## Playing a past day

Add `?date=2026-11-25` to the URL. Future dates are blocked.

## Scoring

| Round | Points |
|---|---|
| Letters | 1 per letter, 18 for a nine-letter word |
| Numbers | 10 exact, 7 within 5, 5 within 10 |
| Conundrum | 10 |

Maximum: 84.

## Word list

The dictionary comes from SCOWL (Spell Checker Oriented Word Lists) by Kevin Atkinson, via the `wordlist-english` npm package, sizes 10 to 70. To add or remove a word, edit `data/words.txt` and regenerate.
