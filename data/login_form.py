from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = EmailField('Эл. почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить пользователя в браузере?')
    submit = SubmitField('Войти')
