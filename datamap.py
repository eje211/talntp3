import requests
from typing import Tuple, FrozenSet
from functools import lru_cache
from jellyfish import soundex
from enum import Enum, auto
from wiktionaryparser import WiktionaryParser
import regex as re


class Relation(Enum):
    """
    Les types de relations possibles entre les embeddings.
    """
    HOMONYM = auto()
    COHYPO = auto()
    HYPO = auto()
    RELATED = auto()
    MORPHO = auto()
    PARTOF = auto()


class DataMap:
    """
    Gets relative data information from words.
    """

    #  URL for the Wikipedia API
    URL = 'http://en.wikipedia.org/w/api.php'

    WANTED_CATEGORIES = [
        14,  # Namespace
        100  # Portal
    ]

    parser = WiktionaryParser()

    @classmethod
    @lru_cache(maxsize=None)
    def get_metadata(cls, word: str) -> Tuple[int, FrozenSet[str], FrozenSet[str]]:
        """
        Fetches information from Wikipedia based on a given word
        :param word: The provided word
        :return: The context for word based on the information from Wikipedia
        """
        params = dict(
            action='query',
            srsearch=word,
            format='json',
            list='search')
        resp = requests.get(url=cls.URL, params=params)
        data = resp.json()
        page_id = data['query']['search'][0]['pageid']
        params = dict(
            action='parse',
            pageid=page_id,
            format='json',
            prop='categories|links')
        resp = requests.get(url=cls.URL, params=params)
        data = resp.json()['parse']
        links = data['links']
        links = frozenset(l['*'] for l in links if l['ns'] in cls.WANTED_CATEGORIES)
        categories = data['categories']
        categories = frozenset(c['*'] for c in categories if "hidden" not in c)
        return page_id, links, categories

    @staticmethod
    @lru_cache(maxsize=None)
    def homonym(a: Tuple[int, FrozenSet[str], FrozenSet[str]], b: Tuple[int, FrozenSet[str], FrozenSet[str]]) -> bool:
        return a[0] == b[0]

    @staticmethod
    @lru_cache(maxsize=None)
    def cohyponyme(a: Tuple[int, FrozenSet[str], FrozenSet[str]], b: Tuple[int, FrozenSet[str], FrozenSet[str]]):
        return a[1] & b[1] != set() or a[2] & b[2] != set()

    @classmethod
    @lru_cache(maxsize=None)
    def hyponyme(cls, word: str, a: Tuple[int, FrozenSet[str], FrozenSet[str]],
                 b: Tuple[int, FrozenSet[str], FrozenSet[str]]) -> bool:
        if not  cls.cohyponyme(a, b):
            return False
        parts = b[1] | b[2]
        return bool([p for p in parts if word in p])

    @classmethod
    @lru_cache(maxsize=None)
    def part_of(cls, a, b):
        definition = cls.parser.fetch(b, a)
        try:
            main_definition = definition[0]['definitions'][1]['text']
        except IndexError:
            return False
        for d in main_definition:
            if re.match(f'parts? of.*{a}', d):
                return True
        return False


    @staticmethod
    @lru_cache(maxsize=None)
    def morphologique(a: str, b: str) -> bool:
        return soundex(a) == soundex(b)

    @classmethod
    @lru_cache(maxsize=None)
    def étiqueter(cls, a: str, b: str) -> Relation:
        m_a = cls.get_metadata(a)
        try:
            m_b = cls.get_metadata(b)
        except IndexError:
            return Relation.RELATED
        if cls.homonym(m_a, m_b):
            return Relation.HOMONYM
        if cls.part_of(a, b):
            return Relation.PARTOF
        if cls.hyponyme(a, m_a, m_b):
            return Relation.HYPO
        if cls.cohyponyme(m_a, m_b):
            return Relation.COHYPO
        if cls.morphologique(a, b):
            return Relation.MORPHO
        return Relation.RELATED

