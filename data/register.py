from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField('Эл. почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторить пароль', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    age = StringField('Возраст', validators=[DataRequired()])
    submit = SubmitField('Отправить')
