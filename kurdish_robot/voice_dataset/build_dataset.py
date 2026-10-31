"""Build the Badini recording list from src/*.txt.

Writes:
  sentences.tsv  id <tab> Latin <tab> Arabic script  (master list)
  metadata.csv   id|Latin                             (LJSpeech format for Piper training)
  READ_ME_ALOUD.md                                     (numbered list to read, Arabic script)
  studio.html                                          (reading page, from studio_template.html)

Sentences are written in Latin (Kurmancî) letters; the Arabic script is
generated with transliterate().
"""

import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
LIMIT = 1000

LETTERS = {
    "a": "ا", "b": "ب", "c": "ج", "ç": "چ", "d": "د", "e": "ە", "ê": "ێ",
    "f": "ف", "g": "گ", "h": "ه", "î": "ی", "j": "ژ", "k": "ک", "l": "ل",
    "m": "م", "n": "ن", "o": "ۆ", "p": "پ", "q": "ق", "r": "ر", "s": "س",
    "ş": "ش", "t": "ت", "u": "و", "û": "وو", "v": "ڤ", "w": "و", "x": "خ",
    "y": "ی", "z": "ز",
}
VOWELS = set("aeêiîouû")
PUNCT = {"?": "؟", ",": "،"}
# Whole words that the letter rules get wrong.
SPECIAL = {"û": "و", "saet": "سەعەت", "saeta": "سەعەتا", "saetan": "سەعەتان"}
# Copulas ("is", "am", "are") are written joined to the word before them.
COPULAS = {"e": "ە", "im": "م", "in": "ن"}


def transliterate_word(word):
    out = []
    prev_vowel = True  # start of word behaves like "after a vowel"
    for ch in word.lower():
        if ch in VOWELS and prev_vowel:
            out.append("ئ")  # a vowel cannot start a syllable without hamza
        if ch == "i":
            pass  # short i is not written in Kurdish Arabic script
        elif ch in LETTERS:
            out.append(LETTERS[ch])
        else:
            out.append(ch)
        prev_vowel = ch in VOWELS
    return "".join(out)


def transliterate(sentence):
    words = re.split(r"(\W+)", sentence)
    result = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in COPULAS and i >= 2 and words[i - 1] == " ":
            result[-1] = ""  # drop the space, join to the previous word
            result.append(COPULAS[lw])
        elif lw in SPECIAL:
            result.append(SPECIAL[lw])
        elif re.fullmatch(r"\w+", w):
            result.append(transliterate_word(w))
        else:
            result.append("".join(PUNCT.get(c, c) for c in w))
    return "".join(result)


def load_sentences():
    seen, sentences = set(), []
    for path in sorted(glob.glob(os.path.join(HERE, "src", "*.txt"))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line in seen:
                    continue
                seen.add(line)
                sentences.append(line)
    return sentences[:LIMIT]


def main():
    sentences = load_sentences()
    rows = [(f"badini_{i:04d}", s, transliterate(s)) for i, s in enumerate(sentences, 1)]

    with open(os.path.join(HERE, "sentences.tsv"), "w", encoding="utf-8") as f:
        f.write("id\tlatin\tarabic\n")
        for r in rows:
            f.write("\t".join(r) + "\n")

    with open(os.path.join(HERE, "metadata.csv"), "w", encoding="utf-8") as f:
        for id_, latin, _ in rows:
            f.write(f"{id_}|{latin}\n")

    with open(os.path.join(HERE, "READ_ME_ALOUD.md"), "w", encoding="utf-8") as f:
        f.write("# ١٠٠٠ رستێن بادینی بۆ دەنگێ رۆبۆتی\n\n")
        f.write("هەر رستەکێ ب دەنگێ خۆ تۆمار بکە، و ناڤێ فایلی بکە هەژمارا رستێ "
                "(بۆ نموونە `badini_0001.wav`).\n\n")
        for i, (id_, latin, arabic) in enumerate(rows, 1):
            if (i - 1) % 50 == 0:
                f.write(f"\n## {i} – {min(i + 49, len(rows))}\n\n")
            f.write(f"{i}. {arabic}  \n   `{latin}`\n")

    with open(os.path.join(HERE, "studio_template.html"), encoding="utf-8") as f:
        page = f.read()
    data = json.dumps([[arabic, latin] for _, latin, arabic in rows], ensure_ascii=False)
    with open(os.path.join(HERE, "studio.html"), "w", encoding="utf-8") as f:
        f.write(page.replace("__SENTENCES__", data))

    print(f"{len(rows)} sentences written")


if __name__ == "__main__":
    main()
