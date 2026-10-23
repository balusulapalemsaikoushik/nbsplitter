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

declare const graphemeBrand: unique symbol;
declare const graphemeListBrand: unique symbol;

/** @internal */
export interface GraphemeData {
    /** The original Japanese form of this grapheme. */
    surface: string;
    /** The reading form of this grapheme (in katakana). */
    readingForm: string;
}

/**
 * A single grapheme.
 * 
 * Represents the smallest unit of written text that maintains its intended pronunciation. Can
 * either be a single character or a multi-character compound with a distinct pronunciation.
 */
export type Grapheme = GraphemeData & { [graphemeBrand]: true; };

/**
 * A list of graphemes.
 */
export interface GraphemeList extends ReadonlyArray<Grapheme> {
    /** A list containing every grapheme's original Japanese form. */
    get surface(): string[];
    /** A list containing every grapheme's reading form (in katakana). */
    get readingForm(): string[];
    [graphemeListBrand]: true;
}
