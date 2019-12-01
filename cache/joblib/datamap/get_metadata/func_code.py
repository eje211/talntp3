# first line: 54
    @classmethod
    @memory.cache
    def get_metadata(cls, word: str) -> Tuple[int, FrozenSet[str], FrozenSet[str]]:
        """
        Fetches information from Wikipedia based on a given word
        :param word: The provided word
        :return: The context for word based on the information from Wikipedia
        """
        params = dict(
            action='query',
            srsearch=word,
            format='json',
            list='search')
        resp = requests.get(url=cls.WIKIPEDIA_API_URL, params=params)
        data = resp.json()
        page_id = data['query']['search'][0]['pageid']
        params = dict(
            action='parse',
            pageid=page_id,
            format='json',
            prop='categories|links')
        resp = requests.get(url=cls.WIKIPEDIA_API_URL, params=params)
        data = resp.json()['parse']
        links = data['links']
        links = frozenset(l['*'] for l in links if l['ns'] in cls.WANTED_CATEGORIES)
        categories = data['categories']
        categories = frozenset(c['*'] for c in categories if "hidden" not in c)
        return page_id, links, categories
