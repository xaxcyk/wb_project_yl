import sqlalchemy as sa
from .db_session import SqlAlchemyBase


class WordRule(SqlAlchemyBase):
    __tablename__ = 'word_rules'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    word = sa.Column(sa.String, nullable=False, unique=True)
    correct_letter = sa.Column(sa.String, nullable=False)
    rule = sa.Column(sa.Text, nullable=False)
    category = sa.Column(sa.String, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'word': self.word,
            'correct_letter': self.correct_letter,
            'rule': self.rule,
            'category': self.category
        }