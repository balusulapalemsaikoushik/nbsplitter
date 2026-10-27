# nbsplitter

The TypeScript implementation of [nbsplitter](https://github.com/balusulapalemsaikoushik/nbsplitter), a tool for manipulating Japanese graphemes (i.e. the smallest unit of written text that preserves pronunciation).

## Usage

#### Splitting graphemes

```typescript
import { splitGraphemes } from "nbsplitter";

(async () => {
    const graphemes = await splitGraphemes("東大和市");
    console.log(graphemes.surface);
    // Output: [ '東', '大和', '市' ]
    console.log(graphemes.readingForm);
    // Output: [ 'ヒガシ', 'ヤマト', 'シ' ]
})();
```

#### Generating furigana

```typescript
import { generateFurigana, splitGraphemes } from "nbsplitter";

(async () => {
    const japanese = "私は学生です。";
    const graphemes = await splitGraphemes(japanese);
    const furigana = generateFurigana(japanese, graphemes);
    console.log(furigana);
    // Output: '<ruby>私<rp>(</rp><rt>わたくし</rt><rp>)</rp></ruby>は<ruby>学<rp>(</rp><rt>がく</rt><rp>)</rp></ruby><ruby>生<rp>(</rp><rt>せい</rt><rp>)</rp></ruby>です。'
})();
```

Rendered: <ruby>私<rp>(</rp><rt>わたくし</rt><rp>)</rp></ruby>は<ruby>学<rp>(</rp><rt>がく</rt><rp>)</rp></ruby><ruby>生<rp>(</rp><rt>せい</rt><rp>)</rp></ruby>です。

## Known Limitations

### Inability to test alternate readings for certain multi-kanji strings

Note: this is a JavaScript ecosystem-specific issue.

The WebAssembly distribution of Sudachi that the splitter algorithm relies on does not support direct dictionary lookups, so the algorithm is only able to test the single reading Sudachi infers when tokenizing multi-kanji strings that may have several readings (although rare). See the implementation details for lookup() in [util.ts](src/util.ts) and splitGraphemes() in [splitter.ts](src/splitter.ts) for context.

### Inability to differentiate between unvoiced-to-voiced consonant changes and some inherently voiced readings

Consider the output below:

```typescript
const graphemes = await splitGraphemes("富士", { splitVoiced: false });
console.log(graphemes.readingForm);
// Output: [ 'フジ' ]  <-- WRONG: should be [ 'フ', 'ジ' ]
```

This occurs because the intended reading ジ chosen for the kanji 士 isn't present in the algorithm's kanji dictionary, so the kanji is treated as dependent on the character immediately prior and the entire string is interpreted as a single grapheme.

Along with the ability to exert granular control over splitting by type of voicing, this may be fixed in a future update.

### Certain strings bearing non-kana readings

Sometimes, the tokenizer underlying the splitter algorithm yields a token reading that isn't written in katakana like expected. For instance,

```typescript
const graphemes = await splitGraphemes("送品");
console.log(graphemes.readingForm);
// Output: [ '送品' ]  <-- WRONG: should be [ 'ソウ', 'ヒン' ]
```

This may be fixed in a future update.

## API Reference

### Grapheme

A single grapheme.

Represents the smallest unit of written text that maintains its intended pronunciation. Can
either be a single character or a multi-character compound with a distinct pronunciation.

#### Grapheme.readingForm

The reading form of this grapheme (in katakana).

#### Grapheme.surface

The original Japanese form of this grapheme.

### GraphemeList

A list of graphemes.

#### GraphemeList.readingForm

A list containing every grapheme's reading form (in katakana).

#### GraphemeList.surface

A list containing every grapheme's original Japanese form.

### generateFurigana()

Generates HTML-flavored furigana for kanji in some text.

Params:
* **japanese** The text to generate furigana for.
* **graphemes** The list of graphemes that corresponds with japanese.
* **format** The format the output furigana should be in.

Returns:
* A string containing japanese with HTML furigana ruby insertions when appropriate.


### splitGraphemes()

Splits Japanese text into graphemes.

Params:
* **japanese** The text to be split.
* **options** Options for how different characters should be treated during splitting.
* **options.splitVoiced** If true the voiced counterparts of voiceless kanji readings will be
treated as standalone readings, most notably in instances of rendaku (see
https://en.wikipedia.org/wiki/Rendaku).
* **options.splitSokuon** If true the sokuon (see https://en.wikipedia.org/wiki/Sokuon) and
phonetically indivisble units of text ending with a sokuon will be treated as independent
graphemes.
* **options.splitHatsuon** If true the hatsuon (see
https://en.wikipedia.org/wiki/Japanese_phonology#Moraic_nasal) and phonetically indivisble
units of text ending with a hatsuon will be treated as independent graphemes.
* **options.splitModifiers** If true kana modifier characters, namely yoon (see 
https://en.wikipedia.org/wiki/Y%C5%8Don), choon (see
https://en.wikipedia.org/wiki/Ch%C5%8Donpu), and small vowels will be treated as independent
graphemes.
* **options.splitLong** If true kana used to lengthen vowel sounds that are normally pronounced
as that same vowel sound will be treated as independent graphemes.
* **options.splitOffglides** If true offglide kana solely used to lengthen vowel sounds (the
"i" in "ei" or the "u" in "ou") will be treated as independent graphemes.
* **options.splitClipped** If true the clipped versions of on'yomi readings whose last mora can
be clipped to a sokuon will be treated as standalone readings (see
https://en.wikipedia.org/wiki/Japanese_phonology#Sino-Japanese_gemination). Note that
splitSokuon must be true for this behavior to be active.

Returns:
* A promise that resolves to a GraphemeList representing the split text.

## Acknowledgements

This package relies on [KANJIDIC](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project) dictionary files. These files are property of the [Electronic Dictionary Research and Development Group (EDRDG)](https://www.edrdg.org/) and are used in accordance with the Group's [license](https://www.edrdg.org/edrdg/licence.html).
