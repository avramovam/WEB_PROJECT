import requests

# Делаем запрос на сайт, передаем ему параметр.
data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()
usd = data['Valute']['USD']['Value']  # ищем нужную валюту и цену


def translateUsdToRub(cents):  # получаем цену игры
        if cents != 'free':
            price = int(cents) / 100 * usd
            return "%.2f" % price
        else:
            return 'free'
