# first line: 132
    @classmethod
    @memory.cache
    def relation(cls, a: str, b: str) -> Tuple[bool, Union[Relation, Set[str]]]:
        synonyms = set()
        definitions = cls.defintion(b)
        definitions = [d['words'] for d in definitions]
        for definition in definitions:
            cls.d = definition
            print(definition)
            if a in definition['words']:
                for relation, dict_relation in cls.relations.items():
                    if relation is Relation.SYNONYM:
                        synonyms.add(a)
                    if definitions['relationshipType'] in dict_relation:
                        return True, relation
        return False, synonyms
