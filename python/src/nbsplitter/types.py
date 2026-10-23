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

from abc import ABC, abstractmethod
from collections.abc import Sequence


class Grapheme(ABC):
    """A single grapheme.

    Represents the smallest unit of written text that maintains its intended
    pronunciation. Can either be a single character or a multi-character
    compound with a distinct pronunciation.
    """

    @abstractmethod
    def surface(self) -> str:
        """The original Japanese form of this grapheme."""
        pass

    @abstractmethod
    def reading_form(self) -> str:
        """The reading form of this grapheme (in katakana)."""
        pass


class _Grapheme(Grapheme):
    def __init__(self, surface: str, reading: str):
        self._surface = surface
        self._reading = reading

    def surface(self):
        return self._surface

    def reading_form(self):
        return self._reading

    def __repr__(self):
        return self._surface
    __str__ = __repr__


class GraphemeList(ABC):
    """A list of graphemes."""

    @abstractmethod
    def surface(self) -> list[str]:
        """A list containing every grapheme's original Japanese form."""
        pass

    @abstractmethod
    def reading_form(self) -> list[str]:
        """A list containing every grapheme's reading form (in katakana)."""
        pass

    @abstractmethod
    def __getitem__(self, index: int) -> Grapheme:
        pass


class _GraphemeList(Sequence, GraphemeList):
    def __init__(self, graphemes: list[Grapheme]):
        self._graphemes = graphemes

    def __len__(self):
        return len(self._graphemes)

    def __getitem__(self, index):
        return self._graphemes[index]

    def surface(self):
        return [grapheme.surface() for grapheme in self._graphemes]

    def reading_form(self):
        return [grapheme.reading_form() for grapheme in self._graphemes]

    def __repr__(self):
        return " ".join(self.surface())
    __str__ = __repr__
