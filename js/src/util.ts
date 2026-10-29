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

import { XMLParser } from "fast-xml-parser";
import { LRUCache } from "lru-cache";
import pMemoize from "p-memoize";
import { SudachiStateless, TokenizeMode } from "sudachi-wasm333";
import { toHiragana, toKatakana, toRomaji } from "wanakana";
import { Chars } from "./chars.js";

/** @internal */
const getKanjidic2 = pMemoize(async (url: string | undefined = undefined) => {
    let xml = "";
    if (url !== undefined) {
        const response = await fetch(url);
        xml = await response.text();
    } else {
        const { readKanjidic2File } = await import("./server.js");
        xml = await readKanjidic2File();
    }
    return new XMLParser({ ignoreAttributes: false }).parse(xml).kanjidic2;
}, { cache: new LRUCache({ max: 1 }) });

/** @internal */
export const getSudachi = pMemoize(async (url: string | undefined = undefined) => {
    const sudachi = new SudachiStateless();
    if (url !== undefined) {
        const response = await fetch(url);
        const buffer = await response.arrayBuffer();
        sudachi.initialize_from_bytes(new Uint8Array(buffer));
    } else {
        const { initializeSudachi } = await import("./server.js");
        await initializeSudachi(sudachi);
    }
    return sudachi;
}, { cache: new LRUCache({ max: 1 }) });

/** @internal */
function isKana(japanese: string) {
    const regex = new RegExp("^[\u3040-\u309f\u30a0-\u30ff]+$", "u");
    return regex.test(japanese);
}

/** @internal */
export function toFurigana(reading: string, format: string) {
    if (format === "hiragana") {
        return toHiragana(reading);
    } else if (format == "romaji") {
        return toRomaji(reading);
    }
    return reading;
}

/** @internal */
function normalizeOn(on: string) {
    // Remove suffix markers associated with some instances of renjo (see
    // https://en.wikipedia.org/wiki/Japanese_phonology#Renj%C5%8D)
    
    return on.replace("-", "");
}

/** @internal */
function getClippedReadings(readings: Set<string>) {
    const clippedReadings = new Set<string>();
    for (const reading of readings) {
        if (Chars.CLIPPABLE_MORAE.has(reading.at(-1)!)) {
            clippedReadings.add(reading.slice(0, -1)! + Chars.SOKUON);
        }
    }
    return clippedReadings;
}

/** @internal */
function normalizeKun(kun: string) {
    // Remove okurigana (see https://en.wikipedia.org/wiki/Okurigana) suffixes
    // (separated from core reading by ".") and affix markers ("-")
    
    return toKatakana(kun.split(".")[0]!.replace("-", ""));
}

/** @internal */
function getVoicedReadings(readings: Set<string>) {
    const voicedReadings = new Set<string>();
    for (const reading of readings) {
        const firstMora = reading[0]!
        if (Chars.RENDAKU_TABLE.has(firstMora)) {
            const voicedReading = Chars.RENDAKU_TABLE.get(firstMora)! + reading.slice(1);
            if (!readings.has(voicedReading)) {
                voicedReadings.add(voicedReading);
            }
        }
    }
    return voicedReadings;
}

/** @internal */
async function lookup(word: string, url: string | undefined = undefined) {
    const sudachi = await getSudachi(url);
    const tokens = sudachi.tokenize_raw(word, TokenizeMode.C);
    if (tokens.length == 1) {
        const token = tokens[0]!
        if (!token.oov) {
            return token.reading_form;
        }
    }
}

/** @internal */
export async function getReadings(
    japanese: string,
    includeVoiced: boolean = true,
    includeClipped: boolean | undefined = undefined,
    kanjidicUrl: string | undefined = undefined,
    sudachiUrl: string | undefined = undefined,
) {
    if (Chars.MISC_READINGS.has(japanese)) {
        return Chars.MISC_READINGS.get(japanese)!;
    }
    if (isKana(japanese)) {
        return [toKatakana(japanese)]  // Leaves katakana untouched
    }
    let readings = new Set<string>();
    if (japanese.length == 1) {
        const kanjidic2 = await getKanjidic2(kanjidicUrl);
        const kanji = kanjidic2.character.find(
            (character: any) => character["literal"] === japanese
        );
        if (kanji !== undefined) {
            const charReadings = kanji.reading_meaning.rmgroup.reading;
            let onReadings = new Set<string>(charReadings
                .filter((reading: any) => reading["@_r_type"] === "ja_on")
                .map((on: any) => normalizeOn(on["#text"]))
            );
            if (includeClipped) {
                onReadings = onReadings.union(getClippedReadings(onReadings));
            }
            const kunReadings = new Set<string>(charReadings
                .filter((reading: any) => reading["@_r_type"] === "ja_kun")
                .map((kun: any) => normalizeKun(kun["#text"]))
            );
            readings = new Set([...readings, ...onReadings, ...kunReadings]);
        }
        // Generally speaking, if the character isn't found in the dictionary,
        // it probably doesn't have an independent reading
    } else {
        const reading = await lookup(japanese, sudachiUrl);
        if (reading !== undefined) {
            readings.add(reading);
        }
    }
    if (!isKana(japanese[0]!)) {  // Kana inherently account for voicing
        if (includeVoiced) {
            readings = readings.union(getVoicedReadings(readings));
        }
    }
    // We want to prioritize longer readings
    return [...readings].toSorted((a, b) => b.length - a.length);
}
