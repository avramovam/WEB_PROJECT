import sqlite3

from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user
from math import floor
from ntpath import isfile

from data import db_session
from data.login_form import LoginForm
from data.users import User
from data.tournaments import Tournaments
from data.register import RegisterForm
import json
import cgi
import cgitb

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

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
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Wrong login or password", form=form)
    return render_template('login.html', title='Authorization', form=form)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Register', form=form,
                                   message="Passwords don't match")
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Register', form=form,
                                   message="This user already exists")
        user = User(
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

@app.route('/user/id=<int:id>', methods=['GET', 'POST'])
@login_required
def profile(id):
    con = sqlite3.connect("db/alldata.sqlite")
    cur = con.cursor()
    result = cur.execute(f"""SELECT name, surname, email, age, favourite FROM users WHERE id={id}""").fetchall()[0]
    if 'http://127.0.0.1:8080/game?gameid' in request.referrer:
        previous = request.referrer
        game_id = int(previous[previous.find('gameid=')+7:])
        gamedata = games[game_id]
        fav = result[4]
        if result[4] is None:
            fav = str(game_id) + ','
        elif str(game_id) in fav:
            pass
        else:
            fav += f'{game_id},'
        cur.execute(f"""UPDATE users SET favourite = (? ) WHERE id = (? )""", (fav, id))
        con.commit()
    spis_of_games = {}
    new_result = cur.execute(f"""SELECT favourite FROM users WHERE id={id}""").fetchall()[0] # если пользователь переходит со страницы игры
    for i in new_result[0].split(',')[:-1]:
        gamedata = games[int(i)]
        spis_of_games[gamedata['name']] = gamedata.get('url_info', {}).get('url', 'no link')
    return render_template("admin.html", name=result[0], surname=result[1], email=result[2], age=result[3],
                           games=spis_of_games)


@app.route('/profile_edit/id=<int:id>', methods=['GET', 'POST'])
@login_required
def profile_edit(id):
    form = RegisterForm()
    if request.method == "GET":
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id == id).first()
        if users:
            form.email.data = users.email
            form.password.data = users.hashed_password
            form.password_again.data = users.hashed_password
            form.name.data = users.name
            form.surname.data = users.surname
            form.age.data = users.age
        else:
            e404(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id == id).first()
        if users:
            users.email = form.email.data
            users.password = form.password.data
            users.password_again = form.password.data
            users.name = form.name.data
            users.surname = form.surname.data
            users.age = form.age.data
            db_sess.commit()
            return redirect(f'/')
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
    f_name = (lambda name: a_name in name) if a_name is not None else (lambda name: True)
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
    tournaments = db_sess.query(Tournaments).filter(Tournaments.gameid == id).all()
    print(tournaments)
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
                           # если steamlink == no link, то ссылку не создавать (таких случаев кстати не должно быть)
                           )
#endregion

if __name__ == '__main__':
    if not isfile('db/alldata.sqlite'):
        print('База данных не найдена - генерируется новая.')
        db_session.global_init("db/alldata.sqlite")
        db_sess = db_session.create_session()
        rootuser = User(name='Root', surname='User', age='99', email='root@admin.com', level=3)
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