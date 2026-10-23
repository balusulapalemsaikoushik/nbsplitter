# nbsplitter

A tool for splitting Japanese text into graphemes (i.e. the smallest unit of written text that preserves pronunciation).

## Context

Though a "grapheme" can broadly be defined as a phonetically indivisble unit of written text, note the use of the phrase "_preserves_ pronunciation" in the description above; it is difficult to define "grapheme" as used in this package without first explaining the very act of _splitting_ text into graphemes to begin with. In summary,

> Splitting graphemes is the act of dividing written text into the smallest units possible while ensuring each unit bears a valid pronunciation (in the case of kanji, a valid reading) that reflects its actual pronunciation in the broader string of text, disregarding personal and dialectal variations in phonology. That is to say, by examining an individual unit, it should be evident how exactly that unit is pronounced within the original text.

Technically speaking, this falls outside many definitions of a grapheme as it excludes a number of characters that affect pronunciation to some degree, but the term most closely coincides with what the intention of this package is.

However, splitting Japanese graphemes as described above isn't exactly a straightforward task. For instance, each individual kanji has several possible readings, certain kanji groupings must be considered unique graphemes because their pronunciations aren't obtainable by merely combining individual readings, and there exist numerous whole-character kana modifiers and dependent characters that don't bear individual pronunciations at all. This package elegantly handles the vast majority of such exceptions under the hood and exposes a single interface for splitting graphemes as desired.

## Known Limitations

### Inability to differentiate between unvoiced-to-voiced consonant changes and some inherently voiced readings

Although the splitter algorithm is able to correctly identify most instances of deliberate unvoiced-to-voiced consonant changes within a word, it cannot definitively distinguish such examples from words in which the voiced counterpart of an unvoiced kanji reading was chosen solely for its phonetic value or (although rare) in which an unvoiced kanji reading of foreign origin was simply borrowed into Japanese as its voiced counterpart, constituting a completely valid, standalone reading that wasn't affected by an intentional change in voicing but wasn't in the algorithm's kanji dictionary either. As a result, disabling the option to split voiced readings may treat these inherently voiced readings as dependent on the graphemes around it, when this shouldn't happen in practice. For example, consider the output below:

#### Python

```python
graphemes = split_graphemes("富士", split_voiced=False)
print(graphemes.reading_form())
# Output: ['フジ']  <-- WRONG: should be ['フ', 'ジ']
```

#### TypeScript

```typescript
const graphemes = splitGraphemes("富士", { splitVoiced: false });
console.log(graphemes.readingForm);
// Output: ["フジ"]  <-- WRONG: should be "'フ", "ジ"]
```

This occurs because the intended reading ジ chosen for the kanji 士 isn't present in the algorithm's kanji dictionary, so the kanji is treated as dependent on the character immediately prior and the entire string is interpreted as a single grapheme.

Along with the ability to exert granular control over splitting by type of voicing, this may be fixed in a future update.

### Certain strings bearing non-kana readings

Because the splitter algorithm relies on a multi-step process that begins with the tokenization of the input string, it can only be as accurate as the tokenizer itself, and, in some cases (although quite rare), the tokenizer yields a token reading that isn't written in katakana like expected. For instance,

#### Python

```python
graphemes = split_graphemes("送品")
print(graphemes.reading_form())
# Output: ['送品']  <-- WRONG: should be ['ソウ', 'ヒン']
```

#### Typescript

```typescript
const graphemes = splitGraphemes("送品");
console.log(graphemes.readingForm);
// Output: ["送品"]  <-- WRONG: should be ["ソウ", "ヒン"]
```

This may be fixed in a future update.

## Acknowledgements

This package relies on [KANJIDIC](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) dictionary files. These files are property of the [Electronic Dictionary Research and Development Group (EDRDG)](https://www.edrdg.org/) and are used in accordance with the Group's [license](https://www.edrdg.org/edrdg/licence.html).
