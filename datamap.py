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
from time import sleep
from urllib.error import HTTPError


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
    def is_synonym(a: Tuple[int, FrozenSet[str], FrozenSet[str]], b: Tuple[int, FrozenSet[str], FrozenSet[str]]) -> bool:
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
    @memory.cache
    def part_of(cls, a: str, b: str) -> bool:
        """
        Returns whether word a is semantically a part of b.
        :param a: a word
        :param b: a word
        :param synonyms: synonyms of a
        :return:
        """
        definition = cls.parser.fetch(b)
        a = cls.get_synonyms(a)
        synonyms = '|'.join(a)
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
        """
        :param a: a word
        :param b: a word
        :return: True if both a and b sound the same.
        """
        return soundex(a) == soundex(b)

    @classmethod
    @memory.cache
    def defintion(cls, word: str):
        """
        Fetches a definition from Wordnik.
        :param word: The word to define.
        :return: The definition from Wordnik.
        """
        client = swagger.ApiClient(cls.WORDNIK_API_KEY, cls.WORDNIK_API_URL)
        word_api = WordApi.WordApi(client)
        return word_api.getRelatedWords(word)

    @classmethod
    @memory.cache
    def get_synonyms(cls, word: str) -> Set[str]:
        synonyms = {word}
        try:
            definitions = cls.defintion(word)
        except HTTPError as e:
            if e.code == 404:
                return set()
            else:
                raise
        for definition in definitions:
            if word not in definition.words:
                continue
            if definition.relationshipType in cls.relations[Relation.SYNONYM]:
                synonyms = synonyms.union(definition.words)
        return synonyms

    @classmethod
    @memory.cache
    def relation(cls, a: str, b: str) -> Union[bool, Relation]:
        """
        Tries to use a Wordnik definition to deduce a relationship from word a to word b.
        :param a: Source word.
        :param b: Target word.
        :return: Whether the relationship was found then the relationship
            or a set of homonyms of a b if no relationship can be found.
        """
        relations = []
        try:
            definitions = cls.defintion(b)
        except HTTPError as e:
            if e.code == 404: 
                return False
            else:
                raise
        for definition in definitions:
            for word in definition.words:
                if a in word:
                    for relation, dict_relation in cls.relations.items():
                        if definition.relationshipType in dict_relation:
                            relations.append(relation)
        if relations:
            relations.sort(key=lambda r: r.value)
            return relations[0]
        return False


    @classmethod
    def étiqueter(cls, a: str, b: str) -> Relation:
        """
        Tries to label a semantic relationship from word a to word b automatically. Very approximate at best.
        Inaccurate at worse.
        :param a: Source word.
        :param b: Target word.
        :return: Relationship.
        """
        sleep(10)
        m_a = cls.get_metadata(a)
        try:
            m_b = cls.get_metadata(b)
        except IndexError:
            return Relation.RELATED
        if cls.is_synonym(m_a, m_b):
            return Relation.SYNONYM
        result = cls.relation(a, b)
        if result:
            return result
        if cls.part_of(a, b):
            return Relation.PARTOF
        if cls.hyponyme(a, m_a, m_b):
            return Relation.HYPO
        if cls.cohyponyme(m_a, m_b):
            return Relation.COHYPO
        if cls.morphologique(a, b):
            return Relation.MORPHO
        return Relation.RELATED

