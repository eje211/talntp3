# first line: 130
    @staticmethod
    @memory.cache
    def morphologique(a: str, b: str) -> bool:
        """
        :param a: a word
        :param b: a word
        :return: True if both a and b sound the same.
        """
        return soundex(a) == soundex(b)
