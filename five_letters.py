# -*- coding: utf-8 -*-
"""Игра «5 букв»: загаданное существительное, 6 попыток, зелёный / медовый / серый."""
from __future__ import annotations

import hashlib
import random
from datetime import date
from pathlib import Path

ROWS = 6
COLS = 5

KEYBOARD = [
    list("йцукенгшщзхъ"),
    list("фывапролджэ"),
    list("ячсмитьбю"),
]

LATIN_TO_RU = {
    "q": "й", "w": "ц", "e": "у", "r": "к", "t": "е", "y": "н", "u": "г",
    "i": "ш", "o": "щ", "p": "з", "[": "х", "]": "ъ",
    "a": "ф", "s": "ы", "d": "в", "f": "а", "g": "п", "h": "р", "j": "о",
    "k": "л", "l": "д", ";": "ж", "'": "э",
    "z": "я", "x": "ч", "c": "с", "v": "м", "b": "и", "n": "т", "m": "ь",
    ",": "б", ".": "ю",
}


def normalize(word: str) -> str:
    return (word or "").strip().lower().replace("ё", "е")


def is_cyr5(word: str) -> bool:
    w = normalize(word)
    return len(w) == COLS and all("а" <= ch <= "я" or ch == "ё" for ch in w)


# Явный мат и грубые формы; не трогаем обычные слова вроде «сукно», «хутор», «эпоха».
RUDE_EXACT = {
    "бляди", "блядь", "блять",
    "хуйло", "хуйня", "хуйне", "хуйню", "хуями", "хуета", "хуево", "хуясе",
    "пизда", "пизде", "пизду", "пизды", "пиздя",
    "ебать", "ебала", "ебало", "ебана", "ебану", "еблан", "ебись",
    "ебите", "ебусь", "выебу", "выеби", "заеби", "заеба", "заебу", "наебу",
    "поеби", "въеби", "отъеб", "уебан", "уебок", "уебки",
    "нахуй", "похуй", "нихуя", "охуел", "охуею",
    "мудак", "мудил",
    "пидор", "пидар", "педик",
    "говно", "говна", "говне", "говну",
    "срать", "срака", "ссать", "ссука",
    "жопам", "жопах", "жопой", "жопе", "жопу", "жопою",
    "сукам", "суках", "сукой", "сукин", "сучий",
    "сучка", "сучке", "сучки", "сучку", "сучок",
    "манда", "манде", "манду", "манды",
    "дрочи", "дрочу", "дроча", "дрочь",
    "шлюха", "шлюхе", "шлюхи", "шлюху",
    "мразь", "мрази", "гнида", "гниде", "гниду", "гниды",
    "курва", "курве", "курвы", "курву",
    "конча", "конче", "кончи", "кончу",
    "траха", "трахн", "сперм", "залуп",
    "секса", "сексе", "сексу",
    "члена", "члене", "члено", "члену", "члены",
    "хрена", "хрене", "хрену",
    "херик", "херил", "херим", "херит", "хером", "херят",
    "фигня", "фигне", "фигни", "фигню",
    "какай", "какал", "какаю",
    "всоси",
    "блуда", "блуде", "блуди", "блудн", "блуду", "блудя",
}

RUDE_STEMS = (
    "бляд", "блят", "хуй", "хуе", "хуё", "хуя",
    "пизд", "ебал", "ебат", "ебан", "ебло", "еблан",
    "заеб", "выеб", "наеб", "поеб", "въеб", "отъеб", "уеб",
    "мудак", "мудил", "пидор", "пидар", "педик",
    "говн", "жоп", "сучк", "дроч", "срак", "ссат",
    "шлюх", "охуе", "залуп", "траха", "сперм",
)


def is_rude(word: str) -> bool:
    w = normalize(word)
    if w in RUDE_EXACT:
        return True
    return any(stem in w for stem in RUDE_STEMS)


def load_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    out, seen = [], set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        w = normalize(raw)
        if is_cyr5(w) and w not in seen and not is_rude(w):
            seen.add(w)
            out.append(w)
    return out


def score_guess(secret: str, guess: str) -> list[str]:
    secret = list(normalize(secret))
    guess = list(normalize(guess))
    colors = ["miss"] * COLS
    remain: dict[str, int] = {}
    for i in range(COLS):
        if guess[i] == secret[i]:
            colors[i] = "hit"
            secret[i] = None
        else:
            ch = secret[i]
            remain[ch] = remain.get(ch, 0) + 1
    for i in range(COLS):
        if colors[i] == "hit":
            continue
        ch = guess[i]
        if remain.get(ch, 0) > 0:
            colors[i] = "present"
            remain[ch] -= 1
    return colors


def merge_key(prev: str | None, color: str) -> str:
    rank = {"miss": 1, "present": 2, "hit": 3}
    if prev is None:
        return color
    return color if rank[color] > rank[prev] else prev


def daily_index(n: int, day: date | None = None) -> int:
    day = day or date.today()
    digest = hashlib.md5(day.isoformat().encode("utf-8")).hexdigest()
    return int(digest, 16) % max(n, 1)


class FiveLetters:
    def __init__(self, guesses: list[str], answers: list[str]):
        self.guesses = set(guesses) | set(answers)
        self.answers = answers or sorted(self.guesses)
        self.secret = ""
        self.rows: list[dict] = []
        self.current = ""
        self.status = "play"
        self.keys: dict[str, str] = {}
        self.message = "Загадано существительное из пяти букв. 6 попыток."
        self.mode = "daily"

    def start(self, secret: str | None = None, mode: str = "daily"):
        pool = self.answers or sorted(self.guesses)
        if secret:
            word = normalize(secret)
        elif mode == "daily":
            word = pool[daily_index(len(pool))]
        else:
            word = random.choice(pool)
        self.secret = word
        self.rows = []
        self.current = ""
        self.status = "play"
        self.keys = {}
        self.mode = mode
        self.message = "Введите слово из 5 букв."

    def type_letter(self, ch: str):
        if self.status != "play":
            return
        ch = normalize(ch)
        if len(ch) != 1 or not ("а" <= ch <= "я"):
            return
        if len(self.current) < COLS:
            self.current += ch
            self.message = ""

    def backspace(self):
        if self.status != "play":
            return
        self.current = self.current[:-1]
        self.message = ""

    def submit(self) -> str:
        if self.status != "play":
            return self.status
        word = normalize(self.current)
        if len(word) < COLS:
            self.message = "Не хватает букв"
            return "short"
        if word not in self.guesses:
            self.message = "Нет такого слова"
            return "unknown"
        colors = score_guess(self.secret, word)
        self.rows.append({"word": word, "colors": colors})
        for i, ch in enumerate(word):
            self.keys[ch] = merge_key(self.keys.get(ch), colors[i])
        self.current = ""
        if word == self.secret:
            self.status = "win"
            self.message = "Угадали!"
            return "win"
        if len(self.rows) >= ROWS:
            self.status = "lose"
            self.message = f"Слово: {self.secret.upper()}"
            return "lose"
        left = ROWS - len(self.rows)
        self.message = f"Осталось попыток: {left}"
        return "ok"

    def letter_at(self, row: int, col: int) -> tuple[str, str]:
        if row < len(self.rows):
            item = self.rows[row]
            return item["word"][col], item["colors"][col]
        if row == len(self.rows) and col < len(self.current):
            return self.current[col], "typed"
        return "", "empty"

    def dump(self) -> dict:
        return {
            "secret": self.secret,
            "rows": self.rows,
            "current": self.current,
            "status": self.status,
            "keys": self.keys,
            "message": self.message,
            "mode": self.mode,
        }

    def restore(self, data: dict | None):
        if not data or not data.get("secret"):
            self.start(mode="daily")
            return
        self.secret = normalize(data.get("secret") or "")
        self.rows = list(data.get("rows") or [])
        self.current = normalize(data.get("current") or "")[:COLS]
        self.status = data.get("status") or "play"
        self.keys = dict(data.get("keys") or {})
        self.message = data.get("message") or ""
        self.mode = data.get("mode") or "daily"
