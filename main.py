from flask import Flask, render_template, request, redirect
#from orm import db_session
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abcdef35q3pouihmglgtjcdkoiyug'

@app.errorhandler(404)
def e404(error):
    return render_template('404.html'), error.code

@app.route('/')
@app.route('/index')
def page_index():
    return render_template('index.html')

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
    print('Загружается games.json...')
    with open('db/games.json', 'r') as f:
        games: list[dict] = json.load(f)
    print('Загрузка завершена! Запускаем приложение...')
    app.run(port=8080, host='127.0.0.1')