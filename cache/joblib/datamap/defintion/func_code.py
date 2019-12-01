# first line: 124
    @classmethod
    @memory.cache
    def defintion(cls, word: str):
        client = swagger.ApiClient(cls.WORDNIK_API_KEY, cls.WORDNIK_API_URL)
        word_api = WordApi.WordApi(client)
        return word_api.getRelatedWords(word)
