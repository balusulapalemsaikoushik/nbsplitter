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

Note the use of the phrase "_preserves_ pronunciation" in the description above; it is impossible to define a "grapheme" without first explaining the very act of _splitting_ text into graphemes to begin with. In summary,

> Splitting graphemes is the act of dividing written text into the smallest units possible while ensuring each unit bears a valid pronunciation (in the case of kanji, a valid reading) that reflects its actual pronunciation in the broader string of text. That is to say, by examining an individual unit, it should be evident how exactly that unit is pronounced within the original text.

Technically speaking, this falls outside most definitions of a "grapheme" as it excludes a number of characters that affect pronunciation, but the term most closely coincides with what the intention of this package is.

However, splitting Japanese graphemes as described above isn't exactly a straightforward task. For instance, each individual kanji has several possible readings, certain kanji groupings must be considered unique graphemes because their pronunciations aren't obtainable by merely combining individual readings, and there exist numerous whole-character kana modifiers and dependent characters that don't bear individual pronunciations at all. This package elegantly handles the vast majority of such exceptions under the hood and exposes a single interface for splitting graphemes as desired.

## Known Limitations

### Inability to differentiate between rendaku and arbitrary unvoiced-to-voiced consonant changes

As noted in the documentation below, the splitter algorithm cannot definitively distinguish between examples of true rendaku and multi-kanji graphemes whose second component appears to be read as the voiced equivalent of one of its standalone readings. For example, consider the output below:

```python
graphemes = split_graphemes("富士", split_rendaku=True)
print(graphemes.reading_form())
# Output: ['フ', 'ジ']  <-- WRONG: should be ['フジ']
```

This occurs because the kanji 士 can be read as シ, so the algorithm interprets the ジ found in the grapheme's actual reading as an intentional change in voicing (i.e. rendaku) when in practice the grapheme 富士 cannot be split (although this may reveal a thing or two about historical changes in pronunciation, I wouldn't say it's particularly useful for parsing modern Japanese).

If this behavior is undesirable, simply disable the option to split graphemes affected by rendaku, at the cost of compound words such as 船橋 being treated as a single grapheme. May be fixed in a future update.

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
* **split_rendaku**: NOT RECOMMENDED: Use only if intending on verifying
graphemes later on. This option may interpret compounds whose
latter parts happen to be the voiced equivalents of unvoiced
counterparts as examples of rendaku when they should not be
considered as such. If True latter parts of a multi-kanji compound
affected by rendaku (see https://en.wikipedia.org/wiki/Rendaku) are
treated as separate graphemes.

Returns:
* A GraphemeList representing the split text.

<!--[[[end]]]-->

## Acknowledgements

This package relies on [KANJIDIC](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) dictionary files. These files are property of the [Electronic Dictionary Research and Development Group (EDRDG)](https://www.edrdg.org/) and are used in accordance with the Group's [license](https://www.edrdg.org/edrdg/licence.html).
