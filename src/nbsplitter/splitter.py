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

import warnings

from . import chars
from .types import Grapheme, GraphemeList, _Grapheme, _GraphemeList
from .util import _get_readings, _get_sudachi_dict, _is_kana


def _clean_token_graphemes(
        graphemes: list[Grapheme],
        split_sokuon: bool = False,
        split_hatsuon: bool = True,
        split_modifiers: bool = False,
        split_long: bool = True,
        split_offglides: bool = False):
    cleaned = []
    prev = None
    for grapheme in graphemes:
        surface, reading = grapheme.surface(), grapheme.reading_form()
        if (
            prev is not None and (
                ((not split_sokuon) and prev[-1] == chars.SOKUON)
                or ((not split_hatsuon) and prev[-1] == chars.HATSUON)
                or (
                    _is_kana(surface)
                    and (
                        (not split_modifiers) and reading in chars.KANA_MODIFIERS
                        or (
                            (not split_offglides)
                            and (
                                (prev[-1] in chars.O_ROW and reading == chars.O_OFFGLIDE)
                                or (prev[-1] in chars.E_ROW and reading == chars.E_OFFGLIDE)
                            )
                        ) or (
                            (not split_long)
                            and (
                                (prev[-1] in chars.A_ROW and reading == chars.A_LONG)
                                or (prev[-1] in chars.I_ROW and reading == chars.I_LONG)
                                or (prev[-1] in chars.U_ROW and reading == chars.U_LONG)
                                or (prev[-1] in chars.E_ROW and reading == chars.E_LONG)
                                or (prev[-1] in chars.O_ROW and reading == chars.O_LONG)
                            )
                        )
                    )
                )
            )
        ):
            new_surface, new_reading = (
                cleaned[-1].surface() + surface,
                cleaned[-1].reading_form() + reading,
            )
            cleaned[-1] = _Grapheme(new_surface, new_reading)
        else:
            cleaned.append(grapheme)
        prev = reading
    return cleaned


def _split_token_graphemes(
        surface: str,
        reading: str,
        split_voiced: bool = True,
        split_clipped: bool | None = None,
        split_rendaku: bool | None = None):
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
            _get_readings(
                surface_leading,
                include_voiced=split_voiced,
                include_clipped=split_clipped,
                include_rendaku=split_rendaku,
            )
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
                        _get_readings(
                            surface_parent,
                            include_voiced=split_voiced,
                            include_clipped=split_clipped,
                            include_rendaku=split_rendaku,
                        )
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
        if (
            "".join(grapheme.surface() for grapheme in graphemes) == surface
            and "".join(grapheme.reading_form() for grapheme in graphemes) == reading
        )
        else [_Grapheme(surface, reading)]
    )


def split_graphemes(
        japanese: str,
        split_voiced: bool = True,
        split_sokuon: bool = False,
        split_hatsuon: bool = True,
        split_modifiers: bool = False,
        split_long: bool = True,
        split_offglides: bool = False,
        split_clipped: bool | None = None,
        *,
        split_rendaku: bool | None = None) -> GraphemeList:
    """Splits Japanese text into graphemes.

    Args:
        japanese: The text to be split.
        split_voiced: If True the voiced counterparts of voiceless kanji
            readings will be treated as standalone readings, most notably in
            instances of rendaku (see https://en.wikipedia.org/wiki/Rendaku).
        split_sokuon: If True the sokuon (see
            https://en.wikipedia.org/wiki/Sokuon) and phonetically indivisble
            units of text ending with a sokuon will be treated as independent
            graphemes.
        split_hatsuon: If True the hatsuon (see
            https://en.wikipedia.org/wiki/Japanese_phonology#Moraic_nasal) and
            phonetically indivisble units of text ending with a hatsuon will
            be treated as independent graphemes.
        split_modifiers: If True kana modifier characters, namely yoon (see
            https://en.wikipedia.org/wiki/Y%C5%8Don), choon (see
            https://en.wikipedia.org/wiki/Ch%C5%8Donpu), and small vowels will
            be treated as independent graphemes.
        split_long: If True kana used to lengthen vowel sounds that are
            normally pronounced as that same vowel sound will be treated as
            independent graphemes.
        split_offglides: If True offglide kana solely used to lengthen vowel
            sounds (the "i" in "ei" or the "u" in "ou") will be treated as
            independent graphemes.
        split_clipped: If True the clipped versions of on'yomi readings
            whose last mora can be clipped to a sokuon will be treated as
            standalone readings (see
            https://en.wikipedia.org/wiki/Japanese_phonology#Sino-Japanese_gemination).
            Note that split_sokuon must be True for this behavior to be active.
        split_rendaku: DEPRECATED: This parameter is no longer used and will be
            removed in version 2.0.0; use split_voiced instead for similar
            functionality. NOT RECOMMENDED: Use only if intending on verifying
            graphemes later on. This option may interpret compounds whose
            latter parts happen to be the voiced equivalents of unvoiced
            counterparts as examples of rendaku when they should not be
            considered as such. If True latter parts of a multi-kanji compound
            affected by rendaku (see https://en.wikipedia.org/wiki/Rendaku) are
            treated as separate graphemes.

    Returns:
        A GraphemeList representing the split text.
    
    Raises:
        ValueError: If split_sokuon is False and split_clipped is not None.
    """

    if (not split_sokuon) and (split_clipped is not None):
        raise ValueError("Cannot set split_clipped when split_sokuon is False")

    if split_rendaku is not None:
        warnings.warn(
            "`split_rendaku` is no longer used and will be removed in version 2.0.0; "
            "use `split_voiced` instead for similar functionality.",
            category=DeprecationWarning,
            stacklevel=2,
        )

    graphemes = []
    surface_sokuon = reading_sokuon = None
    surface_hatsuon = reading_hatsuon = None
    tokenizer = _get_sudachi_dict().create(mode="A")
    tokens = tokenizer.tokenize(japanese)
    for (idx, token) in enumerate(tokens):
        if token.part_of_speech()[0] != "補助記号":  # Exclude punctuation/symbols
            surface, reading = token.surface(), token.reading_form()
            if surface_sokuon is not None:
                # Appends a token with a final sokuon to the start of the next
                surface, reading = (
                    surface_sokuon + surface, reading_sokuon + reading
                )
                surface_sokuon = reading_sokuon = None
            elif surface_hatsuon is not None:
                # Appends a token with a final hatsuon to the start of the next
                surface, reading = (
                    surface_hatsuon + surface, reading_hatsuon + reading
                )
                surface_hatsuon = reading_hatsuon = None
            if idx != len(tokens) - 1:  # Allow sokuon/hatsuon at end of string
                if (not split_sokuon) and reading[-1] == chars.SOKUON:
                    surface_sokuon, reading_sokuon = surface, reading
                    continue
                elif (not split_hatsuon) and reading[-1] == chars.HATSUON:
                    surface_hatsuon, reading_hatsuon = surface, reading
                    continue
        else:
            # Allow sokuon/hatsuon before punctuation
            if surface_sokuon is not None:
                surface, reading = surface_sokuon, reading_sokuon
            elif surface_hatsuon is not None:
                surface, reading = surface_hatsuon, reading_hatsuon
            else:
                surface_sokuon = reading_sokuon = None
                surface_hatsuon = reading_hatsuon = None
                continue
        graphemes += _clean_token_graphemes(
            _split_token_graphemes(
                surface,
                reading,
                split_voiced,
                split_clipped,
                split_rendaku,
            ),
            split_sokuon,
            split_hatsuon,
            split_modifiers,
            split_long,
            split_offglides,
        )
    return _GraphemeList(graphemes)
