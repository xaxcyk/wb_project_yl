from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo

class RegisterForm(FlaskForm):
    username = StringField('Логин', validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    email = EmailField('Почта', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Email(message='Введите корректный адрес электронной почты')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    password_again = PasswordField('Повторите пароль', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        EqualTo('password', message='Пароли должны совпадать')
    ])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[
        DataRequired(message='Поле обязательно для заполнения'),
        Email(message='Введите корректный адрес электронной почты')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Поле обязательно для заполнения')
    ])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')