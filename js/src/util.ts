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

import { transform } from "camaro";
import { promises as fs } from "fs";
import { LRUCache } from "lru-cache";
import pMemoize from "p-memoize";
import path from "path";
import { SudachiStateless, TokenizeMode } from "sudachi-wasm333";
import wanakana, { toHiragana, toRomaji } from "wanakana";
import { Chars } from "./chars.js";

const KANJIDIC2_PATH = path.join(import.meta.dirname, "data/kanjidic2.xml");
const SUDACHI_DICT_PATH = path.join(import.meta.dirname, "data/system_full.dic");

/** @internal */
const getKanjidic2 = pMemoize(async () => {
    return await fs.readFile(KANJIDIC2_PATH, "utf8");
}, { cache: new LRUCache({ max: 1 }) });

/** @internal */
export const getSudachi = pMemoize(async () => {
    const sudachi = new SudachiStateless();
    await sudachi.initialize_node(fs.readFile, SUDACHI_DICT_PATH);
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
    
    return wanakana.toKatakana(kun.split(".")[0]!.replace("-", ""));
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
async function lookup(word: string) {
    const sudachi = await getSudachi();
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
) {
    if (Chars.MISC_READINGS.has(japanese)) {
        return Chars.MISC_READINGS.get(japanese)!;
    }
    if (isKana(japanese)) {
        return [wanakana.toKatakana(japanese)]  // Leaves katakana untouched
    }
    let readings = new Set<string>();
    if (japanese.length == 1) {
        const kanjidic2 = await getKanjidic2();
        const { kanji } = await transform(
            kanjidic2, { kanji: `raw(.//character[literal='${japanese}'])` }
        );
        if (kanji.length > 0) {
            let onReadings = new Set<string>(
                (await transform(kanji, [".//reading[@r_type='ja_on']", "."])).map(
                    (onReading) => normalizeOn(onReading)
                )
            );
            if (includeClipped) {
                onReadings = onReadings.union(getClippedReadings(onReadings));
            }
            const kunReadings = new Set<string>(
                (await transform(kanji, [".//reading[@r_type='ja_kun']", "."])).map(
                    (kunReading) => normalizeKun(kunReading)
                )
            );
            readings = new Set([...readings, ...onReadings, ...kunReadings]);
        }
        // Generally speaking, if the character isn't found in the dictionary,
        // it probably doesn't have an independent reading
    } else {
        const reading = await lookup(japanese);
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
