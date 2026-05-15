import sqlalchemy as sa
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    username = sa.Column(sa.String, nullable=False, unique=True)
    email = sa.Column(sa.String, nullable=False, unique=True, index=True)
    hashed_password = sa.Column(sa.String, nullable=False)

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)