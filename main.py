from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_user, login_required, logout_user

from data import db_session
from data.login_form import LoginForm
from data.users import User
from data.register import RegisterForm
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Wrong login or password", form=form)
    return render_template('login.html', title='Authorization', form=form)


@app.errorhandler(404)
def e404(error):
    return render_template('404.html'), error.code

@app.route("/")
def index():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()
    names = {name.id: (name.surname, name.name) for name in users}
    return render_template("index.html", names=names, title='Games')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")
@app.route('/search')
def page_search():
    a_name = request.args.get('name')
    f_name = (lambda g: a_name in g['name']) if a_name is not None else (lambda g: True)

    filtered = list()
    for i in range(len(games)):
        g = games[i]
        if f_name(g) and g not in filtered:
            filtered.append(g | {'id':i})
    return render_template('search.html', games=filtered)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Register', form=form,
                                   message="Passwords don't match")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Register', form=form,
                                   message="This user already exists")
        user = User(
            name=form.name.data,
            surname=form.surname.data,
            age=form.age.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/game')
def page_game():
    steamid = request.args.get('steamid')
    if steamid is not None: # указан steamid игры, который нужно найти
        for i in range(len(games)):
            if games[i]['url_info']['id'] == steamid:
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
    return render_template('game.html',
                           name=gamedata['name'], # единственный параметр, который есть у всех элементов games
                           desc=gamedata.get('full_desc', {'desc':'<Нет описания>'})['desc'],
                           date=gamedata.get('date', '<Даты выхода нет>'),
                           dev=gamedata.get('developer', '<Разработчик не указан>'),
                           cents=gamedata.get('price', '<Цена не указана>'),
                           steamid=gamedata.get('url_info', {}).get('id', '<Не указан SteamID>'),
                           steamlink=gamedata.get('ulr_info', {}).get('url', 'no link'),
                           imgurl=gamedata['img_url'] # ладно, может не единственный...
                           # если steamlink == no link, то ссылку не создавать (таких случаев кстати не должно быть)
                           )

if __name__ == '__main__':
    db_session.global_init("db/users.sqlite")
    print('Загружается games.json...')
    with open('db/games.json', 'r') as f:
        games: list[dict] = json.load(f)
    print('Загрузка завершена! Запускаем приложение...')
    app.run(port=8080, host='127.0.0.1')