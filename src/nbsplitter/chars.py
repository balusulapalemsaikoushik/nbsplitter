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


SOKUON = "ッ"

YOON = {"ャ", "ュ", "ョ"}
CHOON = {"ー"}
SMALL_VOWELS = {"ァ", "ィ", "ゥ", "ェ", "ォ"}
KANA_MODIFIERS = YOON | CHOON | SMALL_VOWELS

A_ROW = {
    "ア", "カ", "サ", "タ", "ナ", "ハ", "マ", "ヤ", "ラ", "ワ", "ガ", "ザ", "ダ", "バ", "パ",
    "ャ",
}
I_ROW = {
    "イ", "キ", "シ", "チ", "ニ", "ヒ", "ミ", "リ", "ギ", "ジ", "ヂ", "ビ", "ピ",
}
U_ROW = {
    "ウ", "ク", "ス", "ツ", "ヌ", "フ", "ム", "ユ", "ル", "グ", "ズ", "ヅ", "ブ", "プ",
    "ュ"
}
E_ROW = {"エ", "ケ", "セ", "テ", "ネ", "ヘ", "メ", "レ", "ゲ", "ゼ", "デ", "ベ", "ペ"}
O_ROW = {
    "オ", "コ", "ソ", "ト", "ノ", "ホ", "モ", "ヨ", "ロ", "ゴ", "ゾ", "ド", "ボ", "ポ",
    "ョ",
}

A_LONG = "ア"
I_LONG = "イ"
U_LONG = "ウ"
E_LONG = "エ"
O_LONG = "オ"

E_OFFGLIDE = "イ"
O_OFFGLIDE = "ウ"

HATSUON = "ン"

# Submorphemic particles that can neither be considered kanji nor kana
MISC_READINGS = {
    "ヶ": ["カ", "ガ", "コ"],
    "ヵ": ["カ", "ガ", "コ"],
}

CLIPPABLE_MORAE = {"ツ", "チ", "ク", "キ"}

RENDAKU_TABLE = {
    "カ": "ガ",
    "キ": "ギ",
    "ク": "グ",
    "ケ": "ゲ",
    "コ": "ゴ",
    "サ": "ザ",
    "シ": "ジ",
    "ス": "ズ",
    "セ": "ゼ",
    "ソ": "ゾ",
    "タ": "ダ",
    "チ": "ヂ",
    "ツ": "ヅ",
    "テ": "デ",
    "ト": "ド",
    "ハ": "バ",
    "ヒ": "ビ",
    "フ": "ブ",
    "ヘ": "ベ",
    "ホ": "ボ",
}
VOICED_MORAE = set(RENDAKU_TABLE.values())
