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

import { promises as fs } from "fs";
import path from "path";
import type { SudachiStateless } from "sudachi-wasm333";

const KANJIDIC2_PATH = path.join(import.meta.dirname, "data/kanjidic2.xml");
const SUDACHI_DICT_PATH = path.join(import.meta.dirname, "data/system_full.dic");

/** @internal */
export async function readKanjidic2File() {
    return await fs.readFile(KANJIDIC2_PATH, "utf8");
}

/** @internal */
export async function initializeSudachi(sudachi: SudachiStateless) {
    return await sudachi.initialize_node(fs.readFile, SUDACHI_DICT_PATH);
}
