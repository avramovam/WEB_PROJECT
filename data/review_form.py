import datetime

from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, BooleanField, TextAreaField, SelectField
from wtforms.fields.datetime import DateTimeLocalField
from wtforms.validators import DataRequired


class ReviewForm(FlaskForm):
    title = StringField('Заголовок рецензии', validators=[DataRequired()])
    rating = SelectField('Ваша оценка', choices=list(zip(range(11), range(11))))
    desc = TextAreaField('Текст рецензии', validators=[DataRequired()])
    submit = SubmitField('Отправить')
