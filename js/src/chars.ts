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

export namespace Chars {
    export const SOKUON = "ッ";

    export const YOON = new Set(["ャ", "ュ", "ョ"]);
    export const CHOON = new Set(["ー"]);
    export const SMALL_VOWELS = new Set(["ァ", "ィ", "ゥ", "ェ", "ォ"]);
    export const KANA_MODIFIERS = new Set([...YOON, ...CHOON, ...SMALL_VOWELS]);

    export const A_ROW = new Set([
        "ア", "カ", "サ", "タ", "ナ", "ハ", "マ", "ヤ", "ラ", "ワ", "ガ", "ザ", "ダ", "バ", "パ",
        "ャ",
    ]);
    export const I_ROW = new Set([
        "イ", "キ", "シ", "チ", "ニ", "ヒ", "ミ", "リ", "ギ", "ジ", "ヂ", "ビ", "ピ",
    ]);
    export const U_ROW = new Set([
        "ウ", "ク", "ス", "ツ", "ヌ", "フ", "ム", "ユ", "ル", "グ", "ズ", "ヅ", "ブ", "プ",
        "ュ"
    ]);
    export const E_ROW = new Set(["エ", "ケ", "セ", "テ", "ネ", "ヘ", "メ", "レ", "ゲ", "ゼ", "デ", "ベ", "ペ"]);
    export const O_ROW = new Set([
        "オ", "コ", "ソ", "ト", "ノ", "ホ", "モ", "ヨ", "ロ", "ゴ", "ゾ", "ド", "ボ", "ポ",
        "ョ",
    ]);

    export const A_LONG = "ア";
    export const I_LONG = "イ";
    export const U_LONG = "ウ";
    export const E_LONG = "エ";
    export const O_LONG = "オ";

    export const E_OFFGLIDE = "イ";
    export const O_OFFGLIDE = "ウ";

    export const HATSUON = "ン";

    // Submorphemic particles that can neither be considered kanji nor kana
    export const MISC_READINGS = new Map([
        ["ヶ", ["カ", "ガ", "コ"]],
        ["ヵ", ["カ", "ガ", "コ"]],
    ]);

    export const CLIPPABLE_MORAE = new Set(["ツ", "チ", "ク", "キ"]);

    export const RENDAKU_TABLE = new Map([
        ["カ", "ガ"],
        ["キ", "ギ"],
        ["ク", "グ"],
        ["ケ", "ゲ"],
        ["コ", "ゴ"],
        ["サ", "ザ"],
        ["シ", "ジ"],
        ["ス", "ズ"],
        ["セ", "ゼ"],
        ["ソ", "ゾ"],
        ["タ", "ダ"],
        ["チ", "ヂ"],
        ["ツ", "ヅ"],
        ["テ", "デ"],
        ["ト", "ド"],
        ["ハ", "バ"],
        ["ヒ", "ビ"],
        ["フ", "ブ"],
        ["ヘ", "ベ"],
        ["ホ", "ボ"],
    ]);
    export const VOICED_MORAE = new Set(RENDAKU_TABLE.values());
}
