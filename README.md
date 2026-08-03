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
considered as such. If True latter parts of a compound affected by
rendaku are treated as separate graphemes.

Returns:
* A GraphemeList representing the split text.

<!--[[[end]]]-->
