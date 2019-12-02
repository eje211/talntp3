# first line: 162
    @classmethod
    @memory.cache
    def relation(cls, a: str, b: str) -> Union[bool, Relation]:
        """
        Tries to use a Wordnik definition to deduce a relationship from word a to word b.
        :param a: Source word.
        :param b: Target word.
        :return: Whether the relationship was found then the relationship
            or a set of homonyms of a b if no relationship can be found.
        """
        relations = []
        definitions = cls.defintion(b)
        for definition in definitions:
            for word in definition.words:
                if a in word:
                    for relation, dict_relation in cls.relations.items():
                        if definition.relationshipType in dict_relation:
                            relations.append(relation)
        if relations:
            relations.sort(key=lambda r: r.value)
            return relations[0]
        return False
