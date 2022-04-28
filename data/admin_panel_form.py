import datetime

from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, TextAreaField, IntegerField, SelectField, RadioField
from wtforms.fields.datetime import DateTimeLocalField
from wtforms.validators import DataRequired


class AdminForm(FlaskForm):
    userid = IntegerField('ID пользователя', validators=[DataRequired()])
    level = RadioField('Уровень', choices=list(zip(range(3), ['Пользователь (не подтвержден)',
                                                              'Пользователь (подтвержден)',
                                                              'Администратор'])))
    submit = SubmitField('Подтвердить')