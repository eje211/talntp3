# first line: 102
    @classmethod
    @memory.cache
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
