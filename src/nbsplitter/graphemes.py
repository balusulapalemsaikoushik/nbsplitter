# Copyright 2026 Sai Koushik Balusulapalem
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from abc import ABC, abstractmethod
from collections.abc import Sequence
from functools import lru_cache
from importlib.resources import files
import xml.etree.ElementTree as ET

from jaconv import hira2kata
from sudachipy import Dictionary


KANJIDIC2_PATH = files("nbsplitter").joinpath("data/kanjidic2.xml")

# Submorphemic particles that can neither be considered kanji nor kana
MISC_READINGS = {
    "ヶ": ["カ", "ガ", "コ"],
    "ヵ": ["カ", "ガ", "コ"],
}

RENDAKU_TABLE = {
    "カ": "ガ",
    "キ": "ギ",
    "ク": "グ",
    "ケ": "ゲ",
    "コ": "ゴ",
    "サ": "ザ",
    "シ": "ジ",
    "ス": "ズ",
    "セ": "ゼ",
    "ソ": "ゾ",
    "タ": "ダ",
    "チ": "ヂ",
    "ツ": "ヅ",
    "テ": "デ",
    "ト": "ド",
    "ハ": "バ",
    "ヒ": "ビ",
    "フ": "ブ",
    "ヘ": "ベ",
    "ホ": "ボ",
}
VOICED_MORA = {mora for mora in RENDAKU_TABLE.values()}

TOKENIZER_A = Dictionary(dict="full").create(mode="A")
TOKENIZER_C = Dictionary(dict="full").create(mode="C")


class Grapheme(ABC):
    """A single grapheme.

    Represents the smallest unit of written text that maintains its intended
    pronunciation. Can either be a single character or a multi-character
    compound with a distinct pronunciation (see
    https://en.wikipedia.org/wiki/Kanji#Special_readings).
    """

    @abstractmethod
    def surface(self) -> str:
        """The original Japanese form of this grapheme."""
        pass

    @abstractmethod
    def reading_form(self) -> str:
        """The reading form of this grapheme (in katakana)."""
        pass


class _Grapheme(Grapheme):
    def __init__(self, surface: str, reading: str):
        self._surface = surface
        self._reading = reading

    def surface(self):
        return self._surface

    def reading_form(self):
        return self._reading


class GraphemeList(ABC):
    """A list of graphemes."""

    @abstractmethod
    def surface(self) -> list[str]:
        """A list containing every grapheme's original Japanese form."""
        pass

    @abstractmethod
    def reading_form(self) -> list[str]:
        """A list containing every grapheme's reading form (in katakana)."""
        pass


class _GraphemeList(Sequence, GraphemeList):
    def __init__(self, graphemes: list[Grapheme]):
        self._graphemes = graphemes

    def __len__(self):
        return len(self._graphemes)

    def __getitem__(self, index):
        return self._graphemes[index]

    def surface(self):
        return [grapheme.surface() for grapheme in self._graphemes]

    def reading_form(self):
        return [grapheme.reading_form() for grapheme in self._graphemes]


@lru_cache(maxsize=1)
def _get_kanjidic2():
    return ET.parse(KANJIDIC2_PATH).getroot()


def _get_voiced_readings(readings: set[str]):
    voiced_readings = set()
    for reading in readings:
        has_voiced_mora = any(mora in reading[1:] for mora in VOICED_MORA)
        # See Lyman's Law (https://en.wikipedia.org/wiki/Rendaku#Lyman's_law).
        if (first_mora := reading[0]) in RENDAKU_TABLE and (not has_voiced_mora):
            voiced_readings.add(RENDAKU_TABLE[first_mora] + reading[1:])
    return voiced_readings


def _normalize_kun(kun: str):
    # Remove okurigana (see https://en.wikipedia.org/wiki/Okurigana) suffixes
    # (separated from core reading by ".") and affix markers ("-")

    return hira2kata(kun.split(".")[0].replace("-", ""))


def _get_readings(japanese: str, include_voiced: bool = False):
    if len(japanese) == 1:
        if japanese in MISC_READINGS:
            return MISC_READINGS[japanese]
        kanjidic2 = _get_kanjidic2()
        kanji = kanjidic2.find(f".//character[literal='{japanese}']")
        if kanji is not None:
            on_readings = kanji.findall(".//reading[@r_type='ja_on']")
            kun_readings = kanji.findall(".//reading[@r_type='ja_kun']")
            readings = (
                {on_reading.text for on_reading in on_readings}
                | {_normalize_kun(kun_reading.text) for kun_reading in kun_readings}
            )
        else:
            # If a single character that bears a reading isn't a kanji or
            # miscellaneous submorphemic particle, it must be a kana; the
            # following leaves katakana untouched while converting hiragana to
            # katakana as needed.

            return [hira2kata(japanese)]
    else:
        readings = {"".join(token.reading_form() for token in TOKENIZER_C.tokenize(japanese))}
    starts_with_kana = (
        ("\u3040" <= japanese[0] <= "\u309f")  # Hiragana
        or ("\u30a0" <= japanese[0] <= "\u30ff")  # Katakana
    )
    return sorted(list(
        readings | _get_voiced_readings(readings)
        # Kana inherently account for voiced readings
        if (not starts_with_kana) and include_voiced
        else readings
    ), key=len, reverse=True)  # We want to check longer readings first


def _split_token_graphemes(
        surface: str,
        reading: str,
        split_rendaku: bool = False) -> list[Grapheme]:
    # Ok im going to explain this because its a bit convoluted
    # 
    # We begin by declaring left, split, and right pointers that correspond to
    # indices in the surface string. We similarly define left and split
    # pointers for the reading string, but the right pointer must be defined
    # dynamically because kanji readings can be of various lengths (as
    # explained later). For all intents and purposes, left < split < right.
    # 
    # These pointers allow us to define two substrings of the surface string
    # (referred to here as "frames") that I call the "leading" frame (left to
    # split) and "lagging" frame (left to right). Note that the lagging frame
    # is only defined once we have a grapheme added to our list (hence why it
    # "lags"); it exists to ensure that the algorithm can correct itself in
    # case it prematurely considers the leading frame an independent grapheme
    # when it isn't (as explained later). These will also be defined for the
    # reading string, but again, kanji readings can be of various lengths, so
    # we cannot assign them values immediately.
    # 
    # On every iteration, we first check each of the readings of the surface
    # leading frame to see if one equals the reading leading frame (the reading
    # right pointer is defined based on the length of each of the surface
    # leading frame's readings). If we find a match, we greedily add the
    # surface leading frame/reading leading frame combination to our list of
    # graphemes, shift the start of the lagging frame to the start of the
    # previous leading frame, and shift the start of the leading frame to the
    # next unread character.
    # 
    # If the check fails on the leading frame and we have graphemes added to
    # our list, we perform the same check but use the lagging frame instead to
    # see if our algorithm made a mistake when adding the most recent grapheme.
    # If we find a match here, we quickly correct ourselves by replacing the
    # previously added grapheme with the surface lagging frame/reading lagging
    # frame combination but still shift the start of the leading frame to the
    # next unread character.
    # 
    # Regardless of whether these checks pass or fail, the right pointer moves
    # forward so that we can test for new graphemes on each iteration. The loop
    # terminates once the surface right pointer goes out of bound.

    graphemes = []
    surface_left, surface_split, surface_right = None, 0, 1
    reading_left, reading_split = None, 0
    while surface_right <= len(surface):
        surface_leading = surface[surface_split:surface_right]
        for surface_leading_reading in (
            _get_readings(surface_leading, include_voiced=split_rendaku)
        ):
            reading_right = reading_split + len(surface_leading_reading)
            reading_leading = reading[reading_split:reading_right]
            if surface_leading_reading == reading_leading:
                graphemes.append(_Grapheme(surface_leading, reading_leading))
                surface_left, surface_split = surface_split, surface_right
                reading_left, reading_split = reading_split, reading_right
                break
        else:
            if surface_left is not None:
                surface_lagging = surface[surface_left:surface_right]
                for surface_lagging_reading in (
                    _get_readings(surface_lagging, include_voiced=split_rendaku)
                ):
                    reading_right = reading_left + len(surface_lagging_reading)
                    reading_lagging = reading[reading_left:reading_right]
                    if surface_lagging_reading == reading_lagging:
                        graphemes[-1] = _Grapheme(surface_lagging, reading_lagging)
                        surface_split = surface_right
                        reading_split = reading_right
                        break
        surface_right += 1
    return (
        graphemes
        if "".join(grapheme.reading_form() for grapheme in graphemes) == reading
        else [_Grapheme(surface, reading)]
    )


def split_graphemes(japanese: str, split_rendaku: bool = False) -> GraphemeList:
    """Splits Japanese text into graphemes.

    Args:
        japanese: The text to be split.
        split_rendaku: NOT RECOMMENDED: Use only if intending on verifying
            graphemes later on. This option may interpret compounds whose
            latter parts happen to be the voiced equivalents of unvoiced
            counterparts as examples of rendaku when they should not be
            considered as such. If True latter parts of a multi-kanji compound
            affected by rendaku (see https://en.wikipedia.org/wiki/Rendaku) are
            treated as separate graphemes.

    Returns:
        A GraphemeList representing the split text.
    """

    graphemes = []
    for token in TOKENIZER_A.tokenize(japanese):
        if (reading := token.reading_form()):  # Exclude punctuation
            graphemes += _split_token_graphemes(
                token.surface(), reading, split_rendaku
            )
    return _GraphemeList(graphemes)
