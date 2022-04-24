import datetime
import sqlalchemy
from flask_login import UserMixin
from .users import User

from .db_session import SqlAlchemyBase


class Tournament(SqlAlchemyBase):
    __tablename__ = 'tournaments'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    desc = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    author = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey(User.id), nullable=True)
    contacts = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    members = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    start = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now())
    flags = sqlalchemy.Column(sqlalchemy.Integer, default=0) # см ./about_tournaments.md
    gameid = sqlalchemy.Column(sqlalchemy.Integer, default=0)


    def __repr__(self):
        return f'<Tournament#{self.id} of {self.gameid}> {self.name} | {self.members} | {self.start} | {bin(self.flags)[2:]}'
