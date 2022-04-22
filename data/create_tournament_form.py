from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField, BooleanField
from wtforms.fields import DateTimeField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    name = StringField('Название турнира', validators=[DataRequired()])
    start = DateTimeField('Время начала в UTC', validators=[DataRequired()])

    show = BooleanField('Сделать скрытым? (Скрытые турниры не показываются в списке игр)')
    submit = SubmitField('Отправить')
