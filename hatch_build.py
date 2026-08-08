import gzip
from pathlib import Path
import shutil

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.metadata.plugin.interface import MetadataHookInterface
import urllib.request


KANJIDIC2_URL = "https://www.edrdg.org/kanjidic/kanjidic2.xml.gz"
KANJIDIC2_FILENAME = "kanjidic2.xml"


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict):
        data_dir = Path(self.root) / "src" / "nbsplitter" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        dict_file = data_dir / KANJIDIC2_FILENAME
        if not dict_file.exists():
            with urllib.request.urlopen(KANJIDIC2_URL) as response:
                with gzip.GzipFile(fileobj=response) as gz_file:
                    with open(dict_file, "wb") as out_file:
                        shutil.copyfileobj(gz_file, out_file)


class CustomMetadataHook(MetadataHookInterface):
    def update(self, metadata: dict):
        requirements_file = Path(self.root) / "requirements.in"
        if requirements_file.exists():
            dependencies = []
            with open(requirements_file, "rt") as file:
                for line in file:
                    line = line.strip()
                    if (
                        line
                        and (not line.startswith("#"))
                        and (not line.startswith("-"))
                    ):
                        dependencies.append(line)
        metadata["dependencies"] = dependencies
