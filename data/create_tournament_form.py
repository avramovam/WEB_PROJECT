import datetime

from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, TextAreaField
from wtforms.fields.datetime import DateTimeLocalField
from wtforms.validators import DataRequired


class TournamentForm(FlaskForm):
    name = StringField('Название турнира', validators=[DataRequired()])
    desc = TextAreaField('Описание')
    contacts = StringField('Как связаться с организатором?', validators=[DataRequired()])
    start = DateTimeLocalField('Время начала', validators=[DataRequired()], default=datetime.datetime.now(), format="%Y-%m-%dT%H:%M")
    show = BooleanField('Сделать скрытым? (Скрытые турниры не показываются в списке игр)')
    submit = SubmitField('Создать')
