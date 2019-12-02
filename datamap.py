import requests
from typing import Tuple, FrozenSet, Set, Union
from jellyfish import soundex
from enum import Enum
from wiktionaryparser import WiktionaryParser
import regex as re
from wordnik import swagger, WordApi
from config import config
from joblib import Memory
from morph import flatten


class Relation(Enum):
    """
    Les types de relations possibles entre les embeddings.
    """
    SYNONYM = 7
    COHYPO = 5
    HYPO = 2
    RELATED = 8
    MORPHO = 9
    PARTOF = 1
    HYPERNYM = 4


class DataMap:
    """
    Gets relative data information from words.
    """

    relations = {
        Relation.SYNONYM: frozenset(['etymologically-related-term', 'synonym']),
        Relation.RELATED: frozenset(['cross-reference']),
        Relation.HYPERNYM: frozenset(['hypernym']),
        Relation.MORPHO: frozenset(['rhyme']),
        Relation.COHYPO: frozenset(['same-context'])
    }

    #  URL for the Wikipedia API
    WIKIPEDIA_API_URL = 'http://en.wikipedia.org/w/api.php'

    WORDNIK_API_URL = 'http://api.wordnik.com/v4'
    WORDNIK_API_KEY = config.get('wordnik', 'API key')

    WANTED_CATEGORIES = [
        14,  # Namespace
        100  # Portal
    ]

    CACHE_DIRECTORY = config.get('files', 'data cache')
    memory = Memory(CACHE_DIRECTORY, verbose=0)

    parser = WiktionaryParser()

    @classmethod
    @memory.cache
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
        resp = requests.get(url=cls.WIKIPEDIA_API_URL, params=params)
        data = resp.json()
        page_id = data['query']['search'][0]['pageid']
        params = dict(
            action='parse',
            pageid=page_id,
            format='json',
            prop='categories|links')
        resp = requests.get(url=cls.WIKIPEDIA_API_URL, params=params)
        data = resp.json()['parse']
        links = data['links']
        links = frozenset(l['*'] for l in links if l['ns'] in cls.WANTED_CATEGORIES)
        categories = data['categories']
        categories = frozenset(c['*'] for c in categories if "hidden" not in c)
        return page_id, links, categories

    @staticmethod
    @memory.cache
    def synonym(a: Tuple[int, FrozenSet[str], FrozenSet[str]], b: Tuple[int, FrozenSet[str], FrozenSet[str]]) -> bool:
        return a[0] == b[0]

    @staticmethod
    @memory.cache
    def cohyponyme(a: Tuple[int, FrozenSet[str], FrozenSet[str]], b: Tuple[int, FrozenSet[str], FrozenSet[str]]):
        return a[1] & b[1] != set() or a[2] & b[2] != set()

    @classmethod
    @memory.cache
    def hyponyme(cls, word: str, a: Tuple[int, FrozenSet[str], FrozenSet[str]],
                 b: Tuple[int, FrozenSet[str], FrozenSet[str]]) -> bool:
        if not  cls.cohyponyme(a, b):
            return False
        parts = b[1] | b[2]
        return bool([p for p in parts if word in p])

    @classmethod
    def part_of(cls, a: str, b: str, synonyms: Set[str]) -> bool:
        definition = cls.parser.fetch(b)
        synonyms.add(a)
        synonyms = '|'.join(synonyms)
        try:
            definitions = [d['definitions'] for d in definition]
            definitions = flatten(definitions)
            definitions = [d['text'] for d in definitions]
            definitions = flatten(definitions)
        except IndexError:
            return False
        for d in definitions:
            if re.search(f'(?:parts? of|elements? of|portions? of|in an?).*(?:{synonyms})', d) is not None:
                return True
        return False

    @staticmethod
    @memory.cache
    def morphologique(a: str, b: str) -> bool:
        return soundex(a) == soundex(b)

    @classmethod
    @memory.cache
    def defintion(cls, word: str):
        client = swagger.ApiClient(cls.WORDNIK_API_KEY, cls.WORDNIK_API_URL)
        word_api = WordApi.WordApi(client)
        return word_api.getRelatedWords(word)

    @classmethod
    def relation(cls, a: str, b: str) -> Tuple[bool, Union[Relation, Set[str]]]:
        synonyms = set()
        relations = []
        definitions = cls.defintion(b)
        for definition in definitions:
            print(definition.relationshipType)
            print(definition.words)
            for word in definition.words:
                if definition.relationshipType in cls.relations[Relation.SYNONYM]:
                    synonyms = synonyms.union(flatten([a]))
                if a in word:
                    for relation, dict_relation in cls.relations.items():
                        if definition.relationshipType in dict_relation:
                            relations.append(relation)
        if relations:
            relations.sort(key=lambda r: r.value)
            return True, relations[0]
        return False, synonyms


    @classmethod
    @memory.cache
    def étiqueter(cls, a: str, b: str) -> Relation:
        m_a = cls.get_metadata(a)
        try:
            m_b = cls.get_metadata(b)
        except IndexError:
            return Relation.RELATED
        if cls.synonym(m_a, m_b):
            return Relation.SYNONYM
        success, result = cls.relation(a, b)
        if success:
            return result
        if cls.part_of(a, b, result):
            return Relation.PARTOF
        if cls.hyponyme(a, m_a, m_b):
            return Relation.HYPO
        if cls.cohyponyme(m_a, m_b):
            return Relation.COHYPO
        if cls.morphologique(a, b):
            return Relation.MORPHO
        return Relation.RELATED

