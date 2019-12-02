import csv
import sys
import regex as re
from gensim.parsing.preprocessing import remove_stopwords

import gensim.models
import spacy
from spacy.lexeme import Lexeme
from spacy.lang.en import English
try:
    spacy.prefer_gpu()
except AttributeError:
    pass

from config import config
import warnings
from typing import List, Union
 warnings.filterwarnings('ignore')
csv.field_size_limit(sys.maxsize)


class TP3Gensim:

    TEXT_VECTOR_OUTPUT = config.get('files', 'embeddings file')
    
    model = None
    
    @staticmethod
    def clean_sentence(sentence):
                result = []
                last = 0
                matches = re.finditer(r"[^'\w]+", sentence)
                for match in matches:
                    result.append(sentence[last:match.start()])
                    last = match.end()
                if last != len(sentence):
                    result.append(sentence[last:])
                return result

    @classmethod
    def get_model_data(cls):
        with open('data/train_posts.csv') as f:
            token_reader = csv.reader(f, delimiter=',', quotechar='"')
            for row in token_reader:
                row = row[0]
                row = cls.clean_sentence(row)
                yield row

    @classmethod
    def train_model(cls):
        cls.model = gensim.models.Word2Vec(sentences=list(cls.get_model_data()))

    @classmethod
    def get_words(cls, rem_stopwords=True):
        from collections import defaultdict
        from operator import itemgetter
        result = defaultdict(int)
        for words in cls.get_model_data():
            for word in words:
                result[word] += 1
        if rem_stopwords:
            result = [r for r in result.items() if remove_stopwords(r[0])]
        else:
            result = [r for r in result.items()]
        result.sort(key=itemgetter(1), reverse=True)
        return result

    @classmethod
    def dump_words(cls, rem_stopwords=True):
        words = cls.get_words(rem_stopwords)
        with open(cls.OUTPUT_DATAFILE, 'w') as f:
            for word, count in words:
                f.write(f'{word}\t{count}\n')

    @classmethod
    def export_text(cls, stop=None):
        index = 0
        if not hasattr(cls, 'model'):
            cls.train_model()
        with open(cls.TEXT_VECTOR_OUTPUT, 'a') as f:
            f.write(f'{len(cls.model.wv.vocab)} {len(list(cls.model.wv["i"]))}\n')
            for key in cls.model.wv.vocab:
                index += 1
                f.write(f'{key} {" ".join([str(e) for e in list(cls.model.wv[key])])}\n')
                if index == stop:
                    break


# À partir du dosser 'data'
# python -m spacy init-model --prune-vectors 139000 en . -v text_vector.txt


class TP3Spacy:
    DATA_DIR = 'data'

    OUTPUT_DATAFILE = config.get('files', 'words data file')

    SIMILARITY_TOLERANCE = config.getfloat('misc', 'similarity tolerance')

    REPORT_SIZE = config.getint('misc', 'report size')

    nlp: Union[None, English] = None

    @classmethod
    def get_adata(cls):
        cls.nlp = spacy.load(cls.DATA_DIR)

    @classmethod
    def most_similar(cls, word: Lexeme) -> List[Lexeme]:
        """
        Basé sur: https://stackoverflow.com/a/58932131/313273
        """
        queries = [w for w in word.vocab
                if w.is_lower == word.is_lower and w.prob >= -25
                and word.similarity(w) > cls.SIMILARITY_TOLERANCE]
        by_similarity = sorted(queries, key=lambda w: word.similarity(w), reverse=True)
        return by_similarity

    @classmethod
    def produce_report_data(cls):
        if not hasattr(cls, 'nlp'):
            cls.get_adata()
        index = 0
        words = []
        with open(cls.OUTPUT_DATAFILE, 'r') as f:
            while index < cls.REPORT_SIZE:
                index += 1
                line = f.readline()
                line = line.split('\t')
                line = line[0]
                words.append(line)
        words = [cls.nlp.vocab[w] for w in words]
        cls.report = {}
        for word in words:
            similar = cls.most_similar(word)
            cls.report[word.text] = [s.text for s in similar]



