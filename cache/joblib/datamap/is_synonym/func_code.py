# first line: 85
    @staticmethod
    @memory.cache
    def is_synonym(a: Tuple[int, FrozenSet[str], FrozenSet[str]], b: Tuple[int, FrozenSet[str], FrozenSet[str]]) -> bool:
        return a[0] == b[0]
