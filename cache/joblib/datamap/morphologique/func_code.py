# first line: 119
    @staticmethod
    @memory.cache
    def morphologique(a: str, b: str) -> bool:
        return soundex(a) == soundex(b)
