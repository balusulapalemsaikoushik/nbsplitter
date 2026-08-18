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
import re
import xml.etree.ElementTree as ET

from jaconv import hira2kata
from sudachipy import Dictionary


KANJIDIC2_PATH = files("nbsplitter").joinpath("data/kanjidic2.xml")

SOKUON = {"ッ", "っ"}
YOON = {
    "ャ", "ュ", "ョ",
    "ゃ", "ゅ", "ょ",
}
CHOON = {"ー"}
SMALL_VOWELS = {
    "ァ", "ィ", "ゥ", "ェ", "ォ",
    "ぁ", "ぃ", "ぅ", "ぇ", "ぉ",
}
KANA_MODIFIERS = SOKUON | YOON | CHOON | SMALL_VOWELS

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


class Grapheme(ABC):
    """A single grapheme.

    Represents the smallest unit of written text that maintains its intended
    pronunciation. Can either be a single character or a multi-character
    compound with a distinct pronunciation.
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


@lru_cache(maxsize=1)
def _get_sudachi_dict():
    return Dictionary(dict="full")


def _is_kana(japanese: str):
    kana_pattern = r"^[\u3040-\u309f\u30a0-\u30ff]+$"
    return bool(re.fullmatch(kana_pattern, japanese))


def _normalize_kun(kun: str):
    # Remove okurigana (see https://en.wikipedia.org/wiki/Okurigana) suffixes
    # (separated from core reading by ".") and affix markers ("-")

    return hira2kata(kun.split(".")[0].replace("-", ""))


def _get_voiced_readings(readings: set[str]):
    voiced_readings = set()
    for reading in readings:
        has_voiced_mora = any(mora in reading[1:] for mora in VOICED_MORA)
        # See Lyman's Law (https://en.wikipedia.org/wiki/Rendaku#Lyman's_law).
        if (first_mora := reading[0]) in RENDAKU_TABLE and (not has_voiced_mora):
            voiced_readings.add(RENDAKU_TABLE[first_mora] + reading[1:])
    return voiced_readings


def _get_readings(japanese: str, include_voiced: bool = False):
    if japanese in KANA_MODIFIERS or japanese[-1] in SOKUON:
        # Forces kana modifiers to be parsed in the parent frame, sokuon by the
        # next parent frame specifically (see _split_token_graphemes).

        return []
    if japanese in MISC_READINGS:
        return MISC_READINGS[japanese]
    if _is_kana(japanese):
        return [hira2kata(japanese)]  # Leaves katakana untouched
    readings = set()
    if len(japanese) == 1:
        kanjidic2 = _get_kanjidic2()
        kanji = kanjidic2.find(f".//character[literal='{japanese}']")
        if kanji is not None:
            on_readings = kanji.findall(".//reading[@r_type='ja_on']")
            kun_readings = kanji.findall(".//reading[@r_type='ja_kun']")
            readings |= (
                {on_reading.text for on_reading in on_readings}
                | {_normalize_kun(kun_reading.text) for kun_reading in kun_readings}
            )
    else:
        readings |= {
            morpheme.reading_form()
            for morpheme in _get_sudachi_dict().lookup(japanese)
        }
    return sorted(list(
        readings | _get_voiced_readings(readings)
        # Kana inherently account for voiced readings
        if (not _is_kana(japanese[0])) and include_voiced
        else readings
    ), key=len, reverse=True)  # We want to prioritize longer readings


def _split_token_graphemes(
        surface: str,
        reading: str,
        split_rendaku: bool = False) -> list[Grapheme]:
    # The following algorithm splits a morpheme into graphemes. Sudachi makes
    # this very convenient since it provides us with the surface (original
    # Japanese form) and appropriate reading (katakana form) of a given
    # morpheme.
    # 
    # Im sorry in advance if this explanation doesnt make sense
    # 
    # For now, understand that we declare left, split, and right pointers that
    # are used to define substrings (referred to here as "frames") of the
    # surface string and reading string (prefixed by surface_ and reading_
    # accordingly). reading_right, however, must be defined dynamically because
    # kanji readings can be of various lengths (this will make sense later).
    # For all intents and purposes, left < split < right. reading_valid is a
    # flag we use to add desirable readings to valid_readings.
    # 
    # While surface_right is not out of bound:
    # 
    # Firstly, we iterate over all the readings of what I call the surface's
    # "leading" frame (split to right). The length of each reading allows us to
    # define a right pointer for the reading string, and, by extension, a
    # corresponding leading frame for it too. At every iteration, we check to
    # see if the surface leading frame reading equals the reading leading
    # frame; if it does, we (set reading_valid to True, empty valid_readings if
    # some still exist from a previous grapheme, and) add the reading to
    # valid_readings accordingly. After the loop terminates, if reading_valid
    # is True, we pop the first (longest) reading from valid_readings, greedily
    # add it to graphemes, shift the left pointer to the start of the leading
    # frame, and shift the split pointer to the next unread character.
    # 
    # If the leading check fails (and surface_left is defined i.e. the length
    # of graphemes >= 1) we check each valid_reading of the previous grapheme's
    # valid_readings (shorter ones that were still a match) alongside each of
    # the current leading frame's readings to see if we accidentally added a
    # longer reading than we should have. Generally, this is quite rare because
    # the longest match rule applies rather nicely to kanji readings, but it
    # sometimes fails, such as in certain cases of ateji (see
    # https://en.wikipedia.org/wiki/Ateji). Combining each valid_reading and
    # surface_leading_reading yields what I call the surface's "lagging" frame
    # (left to right) reading, whose length allows us to define a right pointer
    # for the reading string, and, by extension, a corresponding lagging frame
    # for it too. If at any point the surface lagging frame reading equals the
    # reading lagging frame, we update the most recent grapheme with its
    # shorter reading, add the leading frame to graphemes, shift the surface
    # left pointer to the start of the leading frame (doing the same for the
    # reading left pointer, adjusting for the fact that the current reading
    # split pointer is ahead due to the incorrect previous reading), shift
    # the split pointer to the next unread character, empty valid_readings,
    # and immediately exit the nested loop.
    # 
    # If the lagging check fails (or, more likely, doesn't execute at all), we
    # perform the exact same check that we did on the leading frame using what
    # I call the surface's "parent" frame (also left to right) in case we
    # prematurely considered the previous leading frame an independent grapheme
    # when it wasn't. This is particularly helpful in identifying jukugo (see
    # https://en.wikipedia.org/wiki/Kanji#Special_readings). After the loop
    # terminates, if reading_valid is True, we pop the longest reading from
    # valid_readings as we did with the leading frame but replace the
    # previously added grapheme with the lagging frame instead of adding an
    # entirely new one, still shifting the split pointer to the next unread
    # character.
    # 
    # Regardless of whether these checks pass or fail, surface_right moves
    # forward so that we can test for new graphemes on the next iteration.

    graphemes = []
    surface_left, surface_split, surface_right = None, 0, 1
    reading_left, reading_split = None, 0
    reading_valid, valid_readings = False, []
    while surface_right <= len(surface):
        surface_leading = surface[surface_split:surface_right]
        surface_leading_readings = (
            _get_readings(surface_leading, include_voiced=split_rendaku)
        )
        for surface_leading_reading in surface_leading_readings:
            reading_right = reading_split + len(surface_leading_reading)
            reading_leading = reading[reading_split:reading_right]
            if surface_leading_reading == reading_leading:
                if not reading_valid:
                    reading_valid, valid_readings = True, []
                valid_readings.append(reading_leading)
        if reading_valid:
            reading_leading = valid_readings.pop(0)
            reading_right = reading_split + len(reading_leading)
            graphemes.append(_Grapheme(surface_leading, reading_leading))
            surface_left, surface_split = surface_split, surface_right
            reading_left, reading_split = reading_split, reading_right
            reading_valid = False
        else:
            if surface_left is not None:
                for valid_reading in valid_readings:
                    for surface_leading_reading in surface_leading_readings:
                        surface_lagging_reading = valid_reading + surface_leading_reading
                        reading_right = reading_left + len(surface_lagging_reading)
                        reading_lagging = reading[reading_left:reading_right]
                        if surface_lagging_reading == reading_lagging:
                            graphemes[-1] = _Grapheme(graphemes[-1].surface(), valid_reading)
                            graphemes.append(_Grapheme(surface_leading, surface_leading_reading))
                            surface_left, surface_split = surface_split, surface_right
                            reading_left, reading_split = (
                                reading_split - len(surface_leading_reading), reading_right
                            )
                            valid_readings = []
                            break
                    else:
                        continue
                    break
                else:
                    surface_parent = surface[surface_left:surface_right]
                    for surface_parent_reading in (
                        _get_readings(surface_parent, include_voiced=split_rendaku)
                    ):
                        reading_right = reading_left + len(surface_parent_reading)
                        reading_parent = reading[reading_left:reading_right]
                        if surface_parent_reading == reading_parent:
                            if not reading_valid:
                                reading_valid, valid_readings = True, []
                            valid_readings.append(reading_parent)
                    if reading_valid:
                        reading_parent = valid_readings.pop(0)
                        reading_right = reading_left + len(reading_parent)
                        graphemes[-1] = _Grapheme(surface_parent, reading_parent)
                        surface_split = surface_right
                        reading_split = reading_right
                        reading_valid = False
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
    sokuon_end = None
    tokenizer = _get_sudachi_dict().create(mode="A")
    for token in tokenizer.tokenize(japanese):
        if (reading := token.reading_form()):  # Exclude punctuation
            surface = token.surface()

            # Pushes a sokuon at the end of one token to the start of the next
            if sokuon_end is not None:
                surface, reading = sokuon_end + surface, "ッ" + reading
                sokuon_end = None
            if surface[-1] in SOKUON:
                sokuon_end = surface[-1]
                surface, reading = surface[:-1], reading[:-1]

            graphemes += _split_token_graphemes(
                surface, reading, split_rendaku
            )
    return _GraphemeList(graphemes)
