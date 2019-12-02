# first line: 83
    @staticmethod
    @memory.cache
    def homonym(a: Tuple[int, FrozenSet[str], FrozenSet[str]], b: Tuple[int, FrozenSet[str], FrozenSet[str]]) -> bool:
        return a[0] == b[0]
