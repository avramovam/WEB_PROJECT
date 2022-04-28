import sqlite3

import requests
import sqlalchemy
from flask import Flask, render_template, request, redirect, url_for, session
from flask_login import LoginManager, login_user, login_required, logout_user
from math import floor
from ntpath import isfile
from werkzeug.exceptions import NotFound

from datetime import datetime, timezone, timedelta
from data import db_session
from data.db_session import func as sql_funcs
from data.login_form import LoginForm
from data.users import User
from data.tournaments import Tournament
from data.register import RegisterForm
from data.forgot_pass import Forgot_Password_Form
from data.change_password import Change_Pass_Form
from data.create_tournament_form import TournamentForm
import json
from dotenv import load_dotenv
from mail_sender import send_email
from random import randint
import urllib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

#region [ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ]
def get_current_user() -> User:
    return db_sess.query(User).filter(User.id == int(session['_user_id'])).first()
#endregion

#region [ОБРАБОТКА ОШИБОК]
@app.errorhandler(404)
def e404(error):
    return render_template('404.html'), error.code
#endregion

#region [ЛОГИН И РЕГИСТРАЦИЯ]
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db_sess.query(User).get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.email == form.email_or_nickname.data).first()
        if not user: # введена не почта
            user = db_sess.query(User).filter(User.nickname == form.email_or_nickname.data).first()
            if not user: # введено неправильно
                return render_template('login.html', message="Введен неверный никнейм, почта или пароль.", form=form)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Введен неверный никнейм, почта или пароль.", form=form)
    return render_template('login.html', form=form)


@app.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    form = Forgot_Password_Form()
    if form.validate_on_submit():
        user = db_sess.query(User).filter(User.email == form.email.data, User.name == form.name.data, User.surname == form.surname.data,
                                          User.age == form.age.data).first()
        if not user:
            return render_template('forget_password.html', message='Такого пользователя не существует', form=form)
        if user:
            db_sess.execute(
                sqlalchemy.update(User)
                    .where(User.email == form.email.data, User.name == form.name.data, User.surname == form.surname.data,
                                          User.age == form.age.data)
                    .values(hashed_password='')
            )
            db_sess.commit()
            return redirect('/confirm_profile')
    return render_template('forget_password.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Register', form=form,
                                   message="Пароль не соответствует повторённому паролю")
        if (bool(db_sess.query(User).filter(User.email == form.email.data).first()) or
            bool(db_sess.query(User).filter(User.nickname == form.nickname.data).first())):
            return render_template('register.html', title='Register', form=form,
                                   message="Пользователь с таким ником или почтой уже есть")
        user = User(
            nickname=form.nickname.data,
            name=form.name.data,
            surname=form.surname.data,
            age=form.age.data,
            email=form.email.data,
            level=0,
        )

        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

# не убирать, это админ-панель. позже решим, что с ней делать
@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    return e404(NotFound)

@app.route('/user', methods=['GET', 'POST'])
def profile():
    id = int(request.args.get('id', 0))
    if not (1 <= id <= db_sess.query(sql_funcs.max(User.id)).first()[0]):
        return e404(NotFound)
    user = db_sess.query(User).filter(User.id == id).first()
    if '/game?gameid' in request.referrer:
        previous = request.referrer
        game_id = int(previous[previous.find('gameid=')+7:])
        fav = user.favourite
        if fav is None:
            fav = str(game_id) + ','
        elif str(game_id) in fav:
            fav = fav.replace(f'{game_id},', '')
        else:
            fav += f'{game_id},'
        db_sess.execute(
            sqlalchemy.update(User)
                .where(User.id == id)
                .values(favourite=fav)
        )
        db_sess.commit()
    list_of_games = []
    new_result = db_sess.query(User).filter(User.id == id).first().favourite # если пользователь переходит со страницы игры
    tournaments = db_sess.query(Tournament).filter(Tournament.members.like(f'%{user.id}%')).all()
    for i in new_result.split(',')[:-1]:
        gameid = int(i)
        list_of_games.append([gameid, games[gameid]['name']])
    return render_template("user.html", nickname=user.nickname, name=user.name, surname=user.surname, email=user.email, age=user.age,
                           games=list_of_games, level_profile=user.level, tournaments=tournaments)

@app.route('/is_your_email', methods=['GET', 'POST'])
def is_your_email():
    if request.method == 'GET':
        id = int(session['_user_id'])
        email = db_sess.query(User).filter(User.id == id).first().email
        return render_template('is_your_email.html', email=email)


load_dotenv()
@app.route('/mail', methods=['GET', 'POST'])
def mail_form():
    if request.method == 'GET':
        return render_template('mail_me.html')
    else:
        email = request.values.get('email')
        confirm_pass = randint(100000, 999999)
        db_sess.execute(
            sqlalchemy.update(User)
            .where(User.id == int(session['_user_id']))
            .values(confirm_code=confirm_pass, email=email)
        )
        db_sess.commit()
        try:
            if send_email(email, 'Подтверждение аккаунта', f'Ваш код для подтверждения: {confirm_pass}'):
                return redirect('/confirm_profile')
        except Exception as E:
            return render_template('mail_me.html', message=f'Во время отправки на адрес {email} произошла ошибка')

load_dotenv()
@app.route('/confirm_profile', methods=['GET', 'POST'])
def confirm_profile():
    if request.method == 'GET':
        if '/is_your_email' in request.referrer:
            id = int(session['_user_id'])
            email = db_sess.query(User).filter(User.id == id).first().email
            try:
                confirm_pass = randint(100000, 999999)
                db_sess.execute(
                    sqlalchemy.update(User)
                        .where(User.id == int(session['_user_id']))
                        .values(confirm_code=confirm_pass)
                )
                db_sess.commit()
                if send_email(email, 'Подтверждение аккаунта', f'Ваш код для подтверждения: {confirm_pass}'):
                    pass
            except Exception as E:
                return f'Во время отправки на адрес {email} произошла ошибка'

        if '/forget_password' in request.referrer:
            id = int(db_sess.query(User).filter(User.hashed_password == '').first().id)
            email = db_sess.query(User).filter(User.id == id).first().email
            try:
                confirm_pass = randint(100000, 999999)
                db_sess.execute(
                    sqlalchemy.update(User)
                        .where(User.id == id)
                        .values(confirm_code=confirm_pass)
                )
                db_sess.commit()
                if send_email(email, 'Восстановление аккаунта', f'Ваш код для подтверждения: {confirm_pass}'):
                    pass
            except Exception as E:
                return f'Во время отправки на адрес {email} произошла ошибка'

        return render_template('confirm_profile.html')
    if request.method == 'POST':
            passw = request.values.get('password')
            hash_p = db_sess.query(User).filter(User.hashed_password == '').first().hashed_password
            if hash_p == '':
                confirm_code = db_sess.query(User).filter(User.hashed_password == '').first().confirm_code
                if str(passw) == str(confirm_code):
                    return redirect('/change_password')
                else:
                    return render_template('confirm_profile.html', message='Коды не совпадают. Попробуйте снова')
            if str(passw) == str(get_current_user().confirm_code):
                db_sess.execute(
                    sqlalchemy.update(User)
                        .where(User.id == int(session['_user_id']))
                        .values(level=1)
                )
                db_sess.commit()
                return redirect('/')
            else:
                return render_template('confirm_profile.html', message='Коды не совпадают. Попробуйте снова')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    form = Change_Pass_Form()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('change_password.html', form=form,
                                   message="Пароли не совпадают")
        else:
            user = db_sess.query(User).filter(User.hashed_password == '').first()
            user.set_password(form.password.data)
            db_sess.commit()
            return redirect('/login')
    return render_template('change_password.html', form=form)


@app.route('/profile_edit', methods=['GET', 'POST'])
@login_required
def profile_edit():
    id = int(session['_user_id'])
    form = RegisterForm()
    if request.method == 'GET':
        users = get_current_user()
        if users:
            form.nickname.data = users.nickname
            form.email.data = users.email
            form.password.data = users.hashed_password
            form.password_again.data = users.hashed_password
            form.name.data = users.name
            form.surname.data = users.surname
            form.age.data = users.age
        else:
            e404(404)
    if form.validate_on_submit():
        users = db_sess.query(User).filter(User.id == id).first()
        db_sess.execute(
            sqlalchemy.update(User)
                .where(User.id == id)
                .values(nickname='', email='')
        )
        db_sess.commit()
        if users:
            if (bool(db_sess.query(User).filter(User.email == form.email.data).first()) or
                    bool(db_sess.query(User).filter(User.nickname == form.nickname.data).first())):
                return render_template('profile_edit.html', form=form, message='Пользователь с таким ником или почтой уже есть')
            else:
                users.nickname = form.nickname.data
                users.email = form.email.data
                users.password = form.password.data
                users.password_again = form.password.data
                users.name = form.name.data
                users.surname = form.surname.data
                users.age = form.age.data
                db_sess.commit()
                return redirect(f'/user?id={id}')
        else:
            e404(404)
    return render_template('profile_edit.html', form=form)
#endregion

#region [ОСНОВНЫЕ СТРАНИЦЫ]
@app.route("/")
def index():
    users = db_sess.query(User).all()
    names = {name.id: (name.surname, name.name) for name in users}
    return render_template("index.html", names=names, title='Games')

@app.route('/search')
def page_search():
    a_name = request.args.get('name')
    a_name = a_name.lower() if a_name is not None else a_name
    f_name = (lambda name: a_name in name.lower()) if a_name is not None else (lambda name: True)
    a_tags = request.args.get('tags')
    a_tags = [x.strip().lower() for x in a_tags.split(',')] if a_tags is not None else None
    f_tags = (lambda tags: all(x in tags for x in a_tags)) if a_tags is not None else (lambda tags: True)
    a_page = request.args.get('page')
    a_page = int(a_page) if a_page is not None else 0

    pagesize = 20
    startwith = a_page*pagesize if a_page is not None else 0

    filtered = list()
    filtered_names = set()
    for i in range(len(games)):
        g = games[i]
        filters = (
                      f_name(g['name']) and
                      f_tags(set(arg.lower() for arg in g.get('popu_tags', [])))
                  )
        if g['name'] not in filtered_names and filters and g not in filtered:
            filtered.append(g | {'id':i, 'tournum':0, 'acttournum':0})
            filtered_names.add(g['name'])
    allargs = dict(request.args)
    stringified_args = [f'{k}={allargs[k]}' for k in allargs if k != 'page'] # список строк вида "arg=value"
    recursive_link = '/search?' + '&'.join(stringified_args) # для ссылки на след. страницу
    return render_template('search.html', games=filtered[startwith:startwith+pagesize],
                           link=recursive_link, page=a_page, maxpage=floor((len(filtered)-1)/pagesize))

@app.route('/game')
def page_game():
    user_id = int(session['_user_id'])
    steamid = request.args.get('steamid')
    if steamid is not None: # указан steamid игры, который нужно найти
        for i in range(len(games)):
            if 'url_info' in games[i] and games[i]['url_info']['id'] == steamid:
                break # найден steamid
        else: # не найден steamid ---------------------------.
            return redirect('/', 301) # возвращаемся домой   |
        # сюда мы выходим в случае break   <-----------------'
        id = i
    else: # не указан steamid
        id = request.args.get('gameid', type=int) # указан gameid игры
        if id is None: # даже id нет
            redirect('/', 301) # возвращаемся домой
    gamedata = games[id]
    tournaments = db_sess.query(Tournament).filter(Tournament.gameid == id).all()
    fav_games = db_sess.query(User).filter(User.id == user_id).first().favourite.split(',')[:-1]
    return render_template('game.html',
                           name=gamedata['name'], # единственный параметр, который есть у всех элементов games
                           desc=gamedata.get('full_desc', {'desc':'<Нет описания>'})['desc'],
                           date=gamedata.get('date', '<Даты выхода нет>'),
                           dev=gamedata.get('developer', '<Разработчик не указан>'),
                           cents=gamedata.get('price', '<Цена не указана>'),
                           steamid=gamedata.get('url_info', {}).get('id', '<Не указан SteamID>'),
                           steamlink=gamedata.get('url_info', {}).get('url', 'no link'),
                           imgurl=gamedata['img_url'], # ладно, может не единственный...
                           tournaments=tournaments,
                           now=datetime.utcnow(),
                           myid=str(id),
                           favourite=fav_games
                           # если steamlink == no link, то ссылку не создавать (таких случаев кстати не должно быть)
                           )
#endregion

#region [ТУРНИРЫ]
@login_required
@app.route('/create_tournament', methods=['GET', 'POST'])
def create_tournament():
    gameid = request.args.get('gameid')
    if (gameid is None) or (not gameid.isdigit()):
        return render_template('whereiam.html') # страница в случае, если id игры не указан
    gameid = int(gameid)
    form = TournamentForm()
    if form.validate_on_submit():
        tournament = Tournament(name=form.name.data,
                                desc=form.desc.data,
                                author=session['_user_id'],
                                contacts=form.contacts.data,
                                members='',
                                start=form.start.data,
                                flags=(2*form.show.data),
                                gameid=gameid,
                                )
        db_sess.add(tournament)
        db_sess.commit()
        return redirect(f'/tournament?id={tournament.id}')

    return render_template('create_tournament.html',
                           name=games[gameid]['name'],
                           gameid=gameid,
                           form=form,
                           )

@app.route('/tournament', methods=['GET', 'POST'])
def tournament():
    id = request.args.get('id')
    if (id is None) or (not id.isdigit()):
        return render_template('whereiam.html')  # страница в случае, если id турнира не указан
    id = int(id)
    tournament_data = db_sess.query(Tournament).filter(Tournament.id == id).first()
    if not tournament_data:
        return render_template('whereiam.html')  # страница в случае, если id турнира неверен
    if request.method == 'GET':
        lst = []
        if tournament_data.members != '':
            for t in tournament_data.members.split(','):
                i = int(t.strip())
                u = db_sess.query(User).filter(User.id == i).first()
                lst.append((i, u.nickname))
        return render_template('tournament.html',
                               tourdata=tournament_data,
                               now=datetime.utcnow(),
                               participants=lst,
                               gamedata=games[tournament_data.gameid])
    else:
        if get_current_user().id == tournament_data.author:
            db_sess.execute(
                sqlalchemy.update(Tournament)
                    .where(Tournament.id == id)
                    .values(flags=(tournament_data.flags | (1<<0)))
            )
            db_sess.commit()
        return redirect(f'/tournament?id={id}')
#endregion

if __name__ == '__main__':
    if not isfile('db/alldata.sqlite'):
        print('База данных не найдена - генерируется новая.')
        db_session.global_init("db/alldata.sqlite")
        db_sess = db_session.create_session()
        rootuser = User(nickname='Omegame', name='Root', surname='User', age='99', email='root@admin.com', level=3)
        rootuser.set_password('ULTRA_RELIABLE_PASSWORD')
        db_sess.add(rootuser)
        db_sess.commit()
        db_sess.close()
    else:
        db_session.global_init("db/alldata.sqlite")
        db_sess = db_session.create_session()
    print('Загружается games.json...')
    with open('db/games.json', 'r') as f:
        games: list[dict] = json.load(f)
    #print(games[100]) # тестовый запуск
    print('Загрузка завершена! Запускаем приложение...')
    app.run(port=8080, host='127.0.0.1')