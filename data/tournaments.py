import datetime
import sqlalchemy
from flask_login import UserMixin

from .db_session import SqlAlchemyBase


class Tournaments(SqlAlchemyBase):
    __tablename__ = 'tournaments'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    desc = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    members = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    start = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)
    flags = sqlalchemy.Column(sqlalchemy.Integer, default=0) # см ./about_tournaments.md
    gameid = sqlalchemy.Column(sqlalchemy.Integer, default=0)


    def __repr__(self):
        return f'<Tournament#{self.id} of {self.gameid}> {self.name} | {self.members} | {self.state} {self.start}'
