# first line: 105
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
