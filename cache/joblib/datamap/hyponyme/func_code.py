# first line: 93
    @classmethod
    @memory.cache
    def hyponyme(cls, word: str, a: Tuple[int, FrozenSet[str], FrozenSet[str]],
                 b: Tuple[int, FrozenSet[str], FrozenSet[str]]) -> bool:
        if not  cls.cohyponyme(a, b):
            return False
        parts = b[1] | b[2]
        return bool([p for p in parts if word in p])
