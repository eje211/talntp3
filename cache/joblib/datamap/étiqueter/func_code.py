# first line: 184
    @classmethod
    @memory.cache
    def étiqueter(cls, a: str, b: str) -> Relation:
        """
        Tries to label a semantic relationship from word a to word b automatically. Very approximate at best.
        Inaccurate at worse.
        :param a: Source word.
        :param b: Target word.
        :return: Relationship.
        """
        m_a = cls.get_metadata(a)
        try:
            m_b = cls.get_metadata(b)
        except IndexError:
            return Relation.RELATED
        if cls.is_synonym(m_a, m_b):
            return Relation.SYNONYM
        result = cls.relation(a, b)
        if result:
            return result
        if cls.part_of(a, b):
            return Relation.PARTOF
        if cls.hyponyme(a, m_a, m_b):
            return Relation.HYPO
        if cls.cohyponyme(m_a, m_b):
            return Relation.COHYPO
        if cls.morphologique(a, b):
            return Relation.MORPHO
        return Relation.RELATED
