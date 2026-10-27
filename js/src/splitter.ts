/**
 * Copyright 2026 Sai Koushik Balusulapalem
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { TokenizeMode } from "sudachi-wasm333";
import { isKana, isKanji } from "wanakana";
import { Chars } from "./chars.js";
import type { Grapheme, GraphemeData, GraphemeList } from "./types.js";
import { getReadings, getSudachi, toFurigana } from "./util.js";

/** @internal */
function cleanTokenGraphemes(
    graphemes: Grapheme[],
    splitSokuon: boolean = false,
    splitHatsuon: boolean = true,
    splitModifiers: boolean = false,
    splitLong: boolean = true,
    splitOffglides: boolean = false,
) {
    const cleaned: GraphemeData[] = [];
    let prev = undefined;
    for (const grapheme of graphemes) {
        const [surface, reading] = [grapheme.surface, grapheme.readingForm];
        if (
            prev !== undefined && (
                (!splitSokuon && prev.at(-1) === Chars.SOKUON)
                || (!splitHatsuon && prev.at(-1) === Chars.HATSUON)
                || (
                    isKana(surface)
                    && (
                        (!splitModifiers) && reading in Chars.KANA_MODIFIERS
                        || (
                            (!splitOffglides)
                            && (
                                (prev.at(-1)! in Chars.O_ROW && reading === Chars.O_OFFGLIDE)
                                || (prev.at(-1)! in Chars.E_ROW && reading === Chars.E_OFFGLIDE)
                            )
                        ) || (
                            (!splitLong)
                            && (
                                (prev.at(-1)! in Chars.A_ROW && reading === Chars.A_LONG)
                                || (prev.at(-1)! in Chars.I_ROW && reading === Chars.I_LONG)
                                || (prev.at(-1)! in Chars.U_ROW && reading === Chars.U_LONG)
                                || (prev.at(-1)! in Chars.E_ROW && reading === Chars.E_LONG)
                                || (prev.at(-1)! in Chars.O_ROW && reading === Chars.O_LONG)
                            )
                        )
                    )
                )
            )
        ) {
            const [new_surface, new_reading] = [
                cleaned.at(-1)!.surface + surface,
                cleaned.at(-1)!.readingForm + reading,
            ]
            cleaned[cleaned.length - 1] = { surface: new_surface, readingForm: new_reading };
        } else {
            cleaned.push(grapheme)
        }
        prev = reading
    }
    return cleaned as Grapheme[];
}

/** @internal */
async function splitTokenGraphemes(
    surface: string,
    reading: string,
    splitVoiced: boolean = true,
    splitClipped: boolean | undefined = undefined,
) {
    /*
     * The following algorithm splits a morpheme into graphemes. Sudachi makes
     * this very convenient since it provides us with the surface (original
     * Japanese form) and appropriate reading (katakana form) of a given
     * morpheme.
     * 
     * Im sorry in advance if this explanation doesnt make sense
     * 
     * For now, understand that we declare left, split, and right pointers that
     * are used to define substrings (referred to here as "frames") of the
     * surface string and reading string (prefixed by surface and reading
     * accordingly). readingRight, however, must be defined dynamically because
     * kanji readings can be of various lengths (this will make sense later).
     * For all intents and purposes, left < split < right. readingValid is a
     * flag we use to add desirable readings to validReadings.
     * 
     * While surfaceRight is not out of bound:
     * 
     * Firstly, we iterate over all the readings of what I call the surface's
     * "leading" frame (split to right). The length of each reading allows us to
     * define a right pointer for the reading string, and, by extension, a
     * corresponding leading frame for it too. At every iteration, we check to
     * see if the surface leading frame reading equals the reading leading
     * frame; if it does, we (set readingValid to true, empty validReadings if
     * some still exist from a previous grapheme, and) add the reading to
     * validReadings accordingly. After the loop terminates, if readingValid
     * is true, we pop the first (longest) reading from validReadings, greedily
     * add it to graphemes, shift the left pointer to the start of the leading
     * frame, and shift the split pointer to the next unread character.
     * 
     * If the leading check fails (and surfaceLeft is defined i.e. the length
     * of graphemes >= 1) we check each validReading of the previous grapheme's
     * validReadings (shorter ones that were still a match) alongside each of
     * the current leading frame's readings to see if we accidentally added a
     * longer reading than we should have. Generally, this is quite rare because
     * the longest match rule applies rather nicely to kanji readings, but it
     * sometimes fails, such as in certain cases of ateji (see
     * https://en.wikipedia.org/wiki/Ateji). Combining each validReading and
     * surfaceLeadingReading yields what I call the surface's "lagging" frame
     * (left to right) reading, whose length allows us to define a right pointer
     * for the reading string, and, by extension, a corresponding lagging frame
     * for it too. If at any point the surface lagging frame reading equals the
     * reading lagging frame, we update the most recent grapheme with its
     * shorter reading, add the leading frame to graphemes, shift the surface
     * left pointer to the start of the leading frame (doing the same for the
     * reading left pointer, adjusting for the fact that the current reading
     * split pointer is ahead due to the incorrect previous reading), shift
     * the split pointer to the next unread character, empty validReadings,
     * and immediately exit the nested loop.
     * 
     * If the lagging check fails (or, more likely, doesn't execute at all), we
     * perform the exact same check that we did on the leading frame using what
     * I call the surface's "parent" frame (also left to right) in case we
     * prematurely considered the previous leading frame an independent grapheme
     * when it wasn't. This is particularly helpful in identifying jukugo (see
     * https://en.wikipedia.org/wiki/Kanji#Special_readings). After the loop
     * terminates, if readingValid is true, we pop the longest reading from
     * validReadings as we did with the leading frame but replace the
     * previously added grapheme with the lagging frame instead of adding an
     * entirely new one, still shifting the split pointer to the next unread
     * character.
     * 
     * Regardless of whether these checks pass or fail, surfaceRight moves
     * forward so that we can test for new graphemes on the next iteration.
     */

    const graphemes: GraphemeData[] = [];
    let [surfaceLeft, surfaceSplit, surfaceRight]: [number | undefined, number, number] = [
        undefined, 0, 1
    ];
    let [readingLeft, readingSplit]: [number | undefined, number] = [undefined, 0];
    let [readingValid, validReadings]: [boolean, string[]] = [false, []];
    while (surfaceRight <= surface.length) {
        const surfaceLeading = surface.slice(surfaceSplit, surfaceRight);
        const surfaceLeadingReadings = await getReadings(
            surfaceLeading, splitVoiced, splitClipped,
        );
        for (const surfaceLeadingReading of surfaceLeadingReadings) {
            const readingRight = readingSplit + surfaceLeadingReading.length;
            const readingLeading = reading.slice(readingSplit, readingRight);
            if (surfaceLeadingReading === readingLeading) {
                if (!readingValid) {
                    [readingValid, validReadings] = [true, []];
                }
                validReadings.push(readingLeading);
            }
        }
        if (readingValid) {
            const readingLeading = validReadings.shift()!;
            const readingRight = readingSplit + readingLeading.length;
            graphemes.push({ surface: surfaceLeading, readingForm: readingLeading });
            [surfaceLeft, surfaceSplit] = [surfaceSplit, surfaceRight];
            [readingLeft, readingSplit] = [readingSplit, readingRight];
            readingValid = false;
        } else {
            if (surfaceLeft !== undefined) {
                let shorterReadingFound = false;
                for (const validReading of validReadings) {
                    let isCorrectReading = false;
                    for (const surfaceLeadingReading of surfaceLeadingReadings) {
                        const surfaceLaggingReading = validReading + surfaceLeadingReading;
                        const readingRight: number = readingLeft! + surfaceLaggingReading.length;
                        const readingLagging = reading.slice(readingLeft, readingRight);
                        if (surfaceLaggingReading === readingLagging) {
                            graphemes[graphemes.length - 1] = {
                                surface: graphemes[graphemes.length - 1]!.surface,
                                readingForm: validReading
                            };
                            graphemes.push({
                                surface: surfaceLeading, readingForm: surfaceLeadingReading
                            });
                            [surfaceLeft, surfaceSplit] = [surfaceSplit, surfaceRight];
                            [readingLeft, readingSplit] = [
                                readingSplit - surfaceLeadingReading.length, readingRight
                            ];
                            validReadings = [];
                            isCorrectReading = true;
                            break;
                        }
                    }
                    if (!isCorrectReading) {
                        continue;
                    }
                    shorterReadingFound = true;
                    break;
                }
                if (!shorterReadingFound) {
                    const surfaceParent = surface.slice(surfaceLeft, surfaceRight);
                    for (const surfaceParentReading of (
                        await getReadings(
                            surfaceParent,
                            splitVoiced,
                            splitClipped,
                        )
                    )) {
                        const readingRight = readingLeft! + surfaceParentReading.length;
                        const readingParent = reading.slice(readingLeft, readingRight);
                        if (surfaceParentReading === readingParent) {
                            if (readingValid) {
                                [readingValid, validReadings] = [true, []];
                            }
                            validReadings.push(readingParent);
                        }
                    }
                    if (readingValid) {
                        const readingParent = validReadings.shift()!;
                        const readingRight = readingLeft! + readingParent.length;
                        graphemes[graphemes.length - 1] = {
                            surface: surfaceParent,
                            readingForm: readingParent
                        };
                        surfaceSplit = surfaceRight;
                        readingSplit = readingRight;
                        readingValid = false;
                    }
                }
            }
        }
        surfaceRight++;
    }
    return (
        (
            graphemes.map((grapheme) => grapheme.surface).join("") === surface
            && graphemes.map((grapheme) => grapheme.readingForm).join("") === reading
        )
        ? graphemes
        : [{ surface: surface, readingForm: reading }]
    ) as Grapheme[];
}

type SplitSokuonDisabledOptions = {
    splitSokuon: false;
    splitClipped?: undefined;
}

type SplitSokuonEnabledOptions = {
    splitSokuon: true;
    splitClipped?: boolean;
}

type SplitGraphemesOptions = {
    splitVoiced: boolean;
    splitHatsuon: boolean;
    splitModifiers: boolean;
    splitLong: boolean;
    splitOffglides: boolean;
} & (SplitSokuonDisabledOptions | SplitSokuonEnabledOptions);

export async function splitGraphemes(japanese: string): Promise<GraphemeList>;
export async function splitGraphemes(
    japanese: string, options: Partial<SplitGraphemesOptions>
): Promise<GraphemeList>;

/**
 * Splits Japanese text into graphemes.
 * @param japanese The text to be split.
 * @param options Options for how different characters should be treated during splitting.
 * @param options.splitVoiced If true the voiced counterparts of voiceless kanji readings will be
 *     treated as standalone readings, most notably in instances of rendaku (see
 *     https://en.wikipedia.org/wiki/Rendaku).
 * @param options.splitSokuon If true the sokuon (see https://en.wikipedia.org/wiki/Sokuon) and
 *     phonetically indivisble units of text ending with a sokuon will be treated as independent
 *     graphemes.
 * @param options.splitHatsuon If true the hatsuon (see
 *     https://en.wikipedia.org/wiki/Japanese_phonology#Moraic_nasal) and phonetically indivisble
 *     units of text ending with a hatsuon will be treated as independent graphemes.
 * @param options.splitModifiers If true kana modifier characters, namely yoon (see 
 *     https://en.wikipedia.org/wiki/Y%C5%8Don), choon (see
 *     https://en.wikipedia.org/wiki/Ch%C5%8Donpu), and small vowels will be treated as independent
 *     graphemes.
 * @param options.splitLong If true kana used to lengthen vowel sounds that are normally pronounced
 *     as that same vowel sound will be treated as independent graphemes.
 * @param options.splitOffglides If true offglide kana solely used to lengthen vowel sounds (the
 *     "i" in "ei" or the "u" in "ou") will be treated as independent graphemes.
 * @param options.splitClipped If true the clipped versions of on'yomi readings whose last mora can
 *     be clipped to a sokuon will be treated as standalone readings (see
 *     https://en.wikipedia.org/wiki/Japanese_phonology#Sino-Japanese_gemination). Note that
 *     splitSokuon must be true for this behavior to be active.
 * @returns A promise that resolves to a GraphemeList representing the split text.
 */
export async function splitGraphemes(
    japanese: string, options: Partial<SplitGraphemesOptions> = {}
): Promise<GraphemeList> {
    const {
        splitVoiced = true,
        splitSokuon = false,
        splitHatsuon = true,
        splitModifiers = false,
        splitLong = true,
        splitOffglides = false,
        splitClipped = undefined
    } = options;

    const graphemes: Grapheme[] = [];
    let surfaceSokuon, readingSokuon, surfaceHatsuon, readingHatsuon;
    surfaceSokuon = readingSokuon = undefined;
    surfaceHatsuon = readingHatsuon = undefined;
    const sudachi = await getSudachi();
    const tokens = sudachi.tokenize_raw(japanese, TokenizeMode.A);

    let surface, reading: string;
    for (const [idx, token] of tokens.entries()) {
        if (token.poses[0] !== "補助記号") {  // Exclude punctuation/symbols
            [surface, reading] = [token.surface, token.reading_form];
            if (surfaceSokuon !== undefined) {
                // Appends a token with a final sokuon to the start of the next
                [surface, reading] = [
                    surfaceSokuon + surface, readingSokuon + reading
                ]
                surfaceSokuon = readingSokuon = undefined;
            } else if (surfaceHatsuon !== undefined) {
                // Appends a token with a final hatsuon to the start of the next
                [surface, reading] = [
                    surfaceHatsuon + surface, readingHatsuon + reading
                ];
                surfaceHatsuon = readingHatsuon = undefined;
            }
            if (idx !== tokens.length - 1) {  // Allow sokuon/hatsuon at end of string
                if (!splitSokuon && reading.at(-1) === Chars.SOKUON) {
                    [surfaceSokuon, readingSokuon] = [surface, reading];
                    continue;
                } else if (!splitHatsuon && reading.at(-1) === Chars.HATSUON) {
                    [surfaceHatsuon, readingHatsuon] = [surface, reading];
                    continue;
                }
            }
        } else {
            // Allow sokuon/hatsuon before punctuation
            if (surfaceSokuon !== undefined) {
                [surface, reading] = [surfaceSokuon, readingSokuon!];
            } else if (surfaceHatsuon !== undefined) {
                [surface, reading] = [surfaceHatsuon, readingHatsuon!];
            } else {
                surfaceSokuon = readingSokuon = undefined
                surfaceHatsuon = readingHatsuon = undefined
                continue;
            }
        }
        graphemes.push(...cleanTokenGraphemes(await
            splitTokenGraphemes(
                surface,
                reading,
                splitVoiced,
                splitClipped,
            ),
            splitSokuon,
            splitHatsuon,
            splitModifiers,
            splitLong,
            splitOffglides,
        ));
    }

    return Object.defineProperties(graphemes, {
        surface: {
            get() { return this.map((grapheme: Grapheme) => grapheme.surface); }
        },
        readingForm: {
            get() { return this.map((grapheme: Grapheme) => grapheme.readingForm); }
        },
    }) as unknown as GraphemeList;
}

/**
 * Generates HTML-flavored furigana for kanji in some text.
 * @param japanese The text to generate furigana for.
 * @param graphemes The list of graphemes that corresponds with japanese.
 * @param format The format the output furigana should be in.
 * @returns A string containing japanese with HTML furigana ruby insertions when appropriate.
 */
export function generateFurigana(
    japanese: string,
    graphemes: GraphemeList,
    format: "hiragana" | "katakana" | "romaji" = "hiragana",
): string {
    let furigana = "";
    let c, g;
    c = g = 0;
    while (c < japanese.length) {
        if (g < graphemes.length) {
            const grapheme = graphemes[g]!;
            const surface = grapheme.surface;
            if (surface === japanese.slice(c, c + surface.length)) {
                if (isKanji(surface)) {
                    const reading = toFurigana(grapheme.readingForm, format);
                    furigana += `<ruby>${surface}<rp>(</rp><rt>${reading}</rt><rp>)</rp></ruby>`;
                } else {
                    furigana += surface;
                }
                c += surface.length;
                g++;
                continue;
            }
        }
        furigana += japanese[c];
        c++;
    }
    return furigana
}
