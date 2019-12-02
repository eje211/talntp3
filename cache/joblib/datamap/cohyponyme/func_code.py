# first line: 90
    @staticmethod
    @memory.cache
    def cohyponyme(a: Tuple[int, FrozenSet[str], FrozenSet[str]], b: Tuple[int, FrozenSet[str], FrozenSet[str]]):
        return a[1] & b[1] != set() or a[2] & b[2] != set()
