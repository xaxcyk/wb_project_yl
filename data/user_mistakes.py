import sqlalchemy as sa
import sqlalchemy.orm as orm
from .db_session import SqlAlchemyBase


class UserMistake(SqlAlchemyBase):
    __tablename__ = 'user_mistakes'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
    word_id = sa.Column(sa.Integer, sa.ForeignKey('word_rules.id'), nullable=False)
    category = sa.Column(sa.String, nullable=True)

    # Связи
    user = orm.relationship('User', backref='mistakes')
    word = orm.relationship('WordRule')