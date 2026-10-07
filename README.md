# nbsplitter

A tool for splitting Japanese text into graphemes (i.e. the smallest unit of written text that preserves pronunciation).

## Usage

```pycon
>>> from nbsplitter import split_graphemes
>>> graphemes = split_graphemes("東大和市")
>>> print(graphemes.surface())
['東', '大和', '市']
>>> print(graphemes.reading_form())
['ヒガシ', 'ヤマト', 'シ']
```

## Context

Though a "grapheme" can broadly be defined as a phonetically indivisble unit of written text, note the use of the phrase "_preserves_ pronunciation" in the description above; it is difficult to define "grapheme" as used in this package without first explaining the very act of _splitting_ text into graphemes to begin with. In summary,

> Splitting graphemes is the act of dividing written text into the smallest units possible while ensuring each unit bears a valid pronunciation (in the case of kanji, a valid reading) that reflects its actual pronunciation in the broader string of text, disregarding personal and dialectal variations in phonology. That is to say, by examining an individual unit, it should be evident how exactly that unit is pronounced within the original text.

Technically speaking, this falls outside many definitions of a grapheme as it excludes a number of characters that affect pronunciation to some degree, but the term most closely coincides with what the intention of this package is.

However, splitting Japanese graphemes as described above isn't exactly a straightforward task. For instance, each individual kanji has several possible readings, certain kanji groupings must be considered unique graphemes because their pronunciations aren't obtainable by merely combining individual readings, and there exist numerous whole-character kana modifiers and dependent characters that don't bear individual pronunciations at all. This package elegantly handles the vast majority of such exceptions under the hood and exposes a single interface for splitting graphemes as desired.

## Known Limitations

### Inability to differentiate between unvoiced-to-voiced consonant changes and some inherently voiced readings

Although the splitter algorithm is able to correctly identify most instances of deliberate unvoiced-to-voiced consonant changes within a word, it cannot definitively distinguish such examples from words in which the voiced counterpart of an unvoiced kanji reading was chosen solely for its phonetic value or (although rare) in which an unvoiced kanji reading of foreign origin was simply borrowed into Japanese as its voiced counterpart, constituting a completely valid, standalone reading that wasn't affected by an intentional change in voicing but wasn't in the algorithm's kanji dictionary either. As a result, disabling the option to split voiced readings may treat these inherently voiced readings as dependent on the graphemes around it, when this shouldn't happen in practice. For example, consider the output below:

```python
graphemes = split_graphemes("富士", split_voiced=False)
print(graphemes.reading_form())
# Output: ['フジ']  <-- WRONG: should be ['フ', 'ジ']
```

This occurs because the intended reading ジ chosen for the kanji 士 isn't present in the algorithm's kanji dictionary, so the kanji is treated as dependent on the character immediately prior and the entire string is interpreted as a single grapheme.

Along with the ability to exert granular control over splitting by type of voicing, this may be fixed in a future update.

### Certain strings bearing non-kana readings

Because the splitter algorithm relies on a multi-step process that begins with the tokenization of the input string, it can only be as accurate as the tokenizer itself, and, in some cases (although quite rare), the tokenizer yields a token reading that isn't written in katakana like expected. For instance,

```python
graphemes = split_graphemes("送品")
print(graphemes.reading_form())
# Output: ['送品']  <-- WRONG: should be ['ソウ', 'ヒン']
```

This may be fixed in a future update.

## API Reference

<!--[[[cog
from inspect import getmembers, isclass, isfunction
import cog
from docstring_parser import parse
import nbsplitter

def outl_func(doc):
    cog.outl(doc.short_description)
    if doc.long_description:
        cog.outl()
        cog.outl(doc.long_description)
    if doc.params:
        cog.outl()
        cog.outl("Args:")
        for param in doc.params:
            cog.outl(f"* **{param.arg_name}**: {param.description}")
    if doc.returns:
        cog.outl()
        cog.outl("Returns:")
        cog.outl(f"* {doc.returns.description}")
    if doc.raises:
        cog.outl()
        cog.outl("Raises:")
        for e in doc.raises:
            cog.outl(f"* **{e.type_name}**: {e.description}")

def outl_member(name, member, parent=None):
    if not name.startswith("_") and (doc := member.__doc__):
        heading = f"### {name}" if parent is None else f"#### {parent}.{name}"
        is_function = isfunction(member)
        if is_function:
            heading += "()"
            doc = parse(doc)
        cog.outl(heading)
        cog.outl()
        { True: outl_func, False: cog.outl }[is_function](doc)
        cog.outl()

for name, member in getmembers(nbsplitter):
    outl_member(name, member)
    if isclass(member):
        for child_name, child_member in getmembers(member):
            outl_member(child_name, child_member, parent=name)
]]]-->
### Grapheme

A single grapheme.

Represents the smallest unit of written text that maintains its intended
pronunciation. Can either be a single character or a multi-character
compound with a distinct pronunciation.


#### Grapheme.reading_form()

The reading form of this grapheme (in katakana).

#### Grapheme.surface()

The original Japanese form of this grapheme.

### GraphemeList

A list of graphemes.

#### GraphemeList.reading_form()

A list containing every grapheme's reading form (in katakana).

#### GraphemeList.surface()

A list containing every grapheme's original Japanese form.

### split_graphemes()

Splits Japanese text into graphemes.

Args:
* **japanese**: The text to be split.
* **split_voiced**: If True the voiced counterparts of voiceless kanji
readings will be treated as standalone readings, most notably in
instances of rendaku (see https://en.wikipedia.org/wiki/Rendaku).
* **split_sokuon**: If True the sokuon (see
https://en.wikipedia.org/wiki/Sokuon) and phonetically indivisble
units of text ending with a sokuon will be treated as independent
graphemes.
* **split_hatsuon**: If True the hatsuon (see
https://en.wikipedia.org/wiki/Japanese_phonology#Moraic_nasal) and
phonetically indivisble units of text ending with a hatsuon will
be treated as independent graphemes.
* **split_modifiers**: If True kana modifier characters, namely yoon (see
https://en.wikipedia.org/wiki/Y%C5%8Don), choon (see
https://en.wikipedia.org/wiki/Ch%C5%8Donpu), and small vowels will
be treated as independent graphemes.
* **split_long**: If True kana used to lengthen vowel sounds that are
normally pronounced as that same vowel sound will be treated as
independent graphemes.
* **split_offglides**: If True offglide kana solely used to lengthen vowel
sounds (the "i" in "ei" or the "u" in "ou") will be treated as
independent graphemes.
* **split_clipped**: If True the clipped versions of on'yomi readings
whose last mora can be clipped to a sokuon will be treated as
standalone readings (see
https://en.wikipedia.org/wiki/Japanese_phonology#Sino-Japanese_gemination).
Note that split_sokuon must be True for this behavior to be active.
* **split_rendaku**: DEPRECATED: This parameter is no longer used and will be
removed in version 2.0.0; use split_voiced instead for similar
functionality. NOT RECOMMENDED: Use only if intending on verifying
graphemes later on. This option may interpret compounds whose
latter parts happen to be the voiced equivalents of unvoiced
counterparts as examples of rendaku when they should not be
considered as such. If True latter parts of a multi-kanji compound
affected by rendaku (see https://en.wikipedia.org/wiki/Rendaku) are
treated as separate graphemes.

Returns:
* A GraphemeList representing the split text.

Raises:
* **ValueError**: If split_sokuon is False and split_clipped is not None.

<!--[[[end]]]-->

## Acknowledgements

This package relies on [KANJIDIC](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) dictionary files. These files are property of the [Electronic Dictionary Research and Development Group (EDRDG)](https://www.edrdg.org/) and are used in accordance with the Group's [license](https://www.edrdg.org/edrdg/licence.html).
