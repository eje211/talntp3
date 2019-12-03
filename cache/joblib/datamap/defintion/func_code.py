# first line: 140
    @classmethod
    @memory.cache
    def defintion(cls, word: str):
        """
        Fetches a definition from Wordnik.
        :param word: The word to define.
        :return: The definition from Wordnik.
        """
        client = swagger.ApiClient(cls.WORDNIK_API_KEY, cls.WORDNIK_API_URL)
        word_api = WordApi.WordApi(client)
        return word_api.getRelatedWords(word)
