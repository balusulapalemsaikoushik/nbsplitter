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

import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from importlib.resources import files

from jaconv import hira2kata
from sudachipy import Dictionary

from . import chars


KANJIDIC2_PATH = files("nbsplitter").joinpath("data/kanjidic2.xml")


@lru_cache(maxsize=1)
def _get_kanjidic2():
    return ET.parse(KANJIDIC2_PATH).getroot()


@lru_cache(maxsize=1)
def _get_sudachi_dict():
    return Dictionary(dict="full")


def _is_kana(japanese: str):
    kana_pattern = r"^[\u3040-\u309f\u30a0-\u30ff]+$"
    return bool(re.fullmatch(kana_pattern, japanese))


def _normalize_on(on: str):
    # Remove suffix markers associated with some instances of renjo (see
    # https://en.wikipedia.org/wiki/Japanese_phonology#Renj%C5%8D)

    return on.replace("-", "")


def _get_clipped_readings(readings: set[str]):
    clipped_readings = set()
    for reading in readings:
        if reading[-1] in chars.CLIPPABLE_MORAE:
            clipped_readings.add(reading[:-1] + chars.SOKUON)
    return clipped_readings


def _normalize_kun(kun: str):
    # Remove okurigana (see https://en.wikipedia.org/wiki/Okurigana) suffixes
    # (separated from core reading by ".") and affix markers ("-")

    return hira2kata(kun.split(".")[0].replace("-", ""))


def _get_voiced_readings(readings: set[str]):
    voiced_readings = set()
    for reading in readings:
        if (first_mora := reading[0]) in chars.RENDAKU_TABLE:
            voiced_reading = chars.RENDAKU_TABLE[first_mora] + reading[1:]
            if voiced_reading not in readings:
                voiced_readings.add(voiced_reading)
    return voiced_readings


def _get_rendaku_readings(readings: set[str]):
    # Soon-to-be deprecated, although a more robust approach to classifying
    # rendaku may be implemented in a future update

    voiced_readings = set()
    for reading in readings:
        has_voiced_mora = any(mora in reading[1:] for mora in chars.VOICED_MORAE)
        # See Lyman's Law (https://en.wikipedia.org/wiki/Rendaku#Lyman's_law).
        if (first_mora := reading[0]) in chars.RENDAKU_TABLE and (not has_voiced_mora):
            voiced_reading = chars.RENDAKU_TABLE[first_mora] + reading[1:]
            if voiced_reading not in readings:
                voiced_readings.add(voiced_reading)
    return voiced_readings


def _get_readings(
        japanese: str,
        include_voiced: bool = True,
        include_clipped: bool | None = None,
        include_rendaku: bool | None = None):
    if japanese in chars.MISC_READINGS:
        return chars.MISC_READINGS[japanese]
    if _is_kana(japanese):
        return [hira2kata(japanese)]  # Leaves katakana untouched
    readings = set()
    if len(japanese) == 1:
        kanjidic2 = _get_kanjidic2()
        kanji = kanjidic2.find(f".//character[literal='{japanese}']")
        if kanji is not None:
            on_readings = {
                _normalize_on(on_reading.text)
                for on_reading in kanji.findall(".//reading[@r_type='ja_on']")
            }
            if include_clipped:
                on_readings |= _get_clipped_readings(on_readings)
            kun_readings = {
                _normalize_kun(kun_reading.text)
                for kun_reading in kanji.findall(".//reading[@r_type='ja_kun']")
            }
            readings |= on_readings | kun_readings
        # Generally speaking, if the character isn't found in the dictionary,
        # it probably doesn't have an independent reading
    else:
        readings |= {
            morpheme.reading_form()
            for morpheme in _get_sudachi_dict().lookup(japanese)
        }
    if not _is_kana(japanese[0]):  # Kana inherently account for voicing
        if include_rendaku:
            readings |= _get_rendaku_readings(readings)
        if include_voiced:
            readings |= _get_voiced_readings(readings)
    # We want to prioritize longer readings
    return sorted(list(readings), key=len, reverse=True)
