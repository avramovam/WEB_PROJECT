'''
Здесь позже будут ORM модели (наверное)
'''

import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase

class Tournament(SqlAlchemyBase):
    __tablename__ = 'tours'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True) # название
    link = sqlalchemy.Column(sqlalchemy.String, nullable=True) # ссылка (если есть, сделать название гиперссылкой,
    #                                                                    если None - оставить обычной строчкой)
    desc = sqlalchemy.Column(sqlalchemy.String, nullable=True) # описание
    org = sqlalchemy.Column(sqlalchemy.String, nullable=True) # организатор
    memb = sqlalchemy.Column(sqlalchemy.String, nullable=True) # список участников, разделен \n
    winner = sqlalchemy.Column(sqlalchemy.Integer, default=(-1)) # индекс победителя (из списка),
    #                                                            если -1, то победитель неизвестен