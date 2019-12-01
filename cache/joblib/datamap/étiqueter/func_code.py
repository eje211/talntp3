# first line: 155
    @classmethod
    @memory.cache
    def étiqueter(cls, a: str, b: str) -> Relation:
        m_a = cls.get_metadata(a)
        try:
            m_b = cls.get_metadata(b)
        except IndexError:
            return Relation.RELATED
        if cls.synonym(m_a, m_b):
            return Relation.SYNONYM
        success, result = cls.relation(a, b)
        if success:
            return result
        if cls.part_of(a, b, result):
            return Relation.PARTOF
        if cls.hyponyme(a, m_a, m_b):
            return Relation.HYPO
        if cls.cohyponyme(m_a, m_b):
            return Relation.COHYPO
        if cls.morphologique(a, b):
            return Relation.MORPHO
        return Relation.RELATED
