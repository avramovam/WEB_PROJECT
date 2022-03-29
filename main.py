from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
@app.route('/index')
def page_index():
    return render_template('index.html')

@app.route('/search')
def page_search():
    return render_template('search.html')

@app.route('/game')
def page_game():
    return render_template('game.html')

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')