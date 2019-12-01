# first line: 84
    @staticmethod
    @memory.cache
    def synonym(a: Tuple[int, FrozenSet[str], FrozenSet[str]], b: Tuple[int, FrozenSet[str], FrozenSet[str]]) -> bool:
        return a[0] == b[0]
