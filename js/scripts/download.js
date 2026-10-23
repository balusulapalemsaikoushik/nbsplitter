import fs from "fs";
import { Readable } from "stream";
import { finished, pipeline } from "stream/promises";
import path from "path";
import zlib from "zlib";
import StreamZip from "node-stream-zip";

const KANJIDIC2_URL = "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz";
const KANJIDIC2_ZIP = "kanjidic2.gz";
const KANJIDIC2_FILENAME = "kanjidic2.xml";

const SUDACHI_DICT_URL = (
    "http://sudachi.s3-website-ap-northeast-1.amazonaws.com/sudachidict/sudachi-dictionary-latest-full.zip"
);
const SUDACHI_DICT_ZIP = "sudachi_dict.zip";
const SUDACHI_DICT_FILENAME = "system_full.dic";

async function downloadFile(url, path) {
    const response = await fetch(url);
    const fileStream = fs.createWriteStream(path);
    await finished(Readable.fromWeb(response.body).pipe(fileStream));
}

async function downloadKanjidic2(dataDir) {
    const zipFile = path.join(dataDir, KANJIDIC2_ZIP);

    await downloadFile(KANJIDIC2_URL, zipFile);
    
    const dictFile = path.join(dataDir, KANJIDIC2_FILENAME);
    const source = fs.createReadStream(zipFile);
    const gunzip = zlib.createGunzip();
    const destination = fs.createWriteStream(dictFile);
    await pipeline(source, gunzip, destination);
    
    if (fs.existsSync(zipFile)) {
        fs.unlinkSync(zipFile);
    }
}

async function downloadSudachiDict(dataDir) {
    const zipFile = path.join(dataDir, SUDACHI_DICT_ZIP);
    
    await downloadFile(SUDACHI_DICT_URL, zipFile);

    const zip = new StreamZip.async({ file: zipFile });
    const dictDir = Object.values(await zip.entries())[0].name;
    const source = `${dictDir}${SUDACHI_DICT_FILENAME}`;
    const destination = path.join(dataDir, SUDACHI_DICT_FILENAME);

    await zip.extract(source, destination);
    await zip.close();

    if (fs.existsSync(zipFile)) {
        fs.unlinkSync(zipFile);
    }
}

(async () => {
    const dataDir = path.join(import.meta.dirname, "..", "src", "data");
    
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir);
    }

    await downloadKanjidic2(dataDir);
    await downloadSudachiDict(dataDir);
})();
