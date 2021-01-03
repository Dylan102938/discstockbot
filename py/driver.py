from flask import Flask, request, jsonify
from flask_cors import CORS
from handler import *
import urllib.parse

app = Flask(__name__)
CORS(app)


@app.route('/exec_order',methods=["POST"])
def exec_order():
    if request.method == "POST":
        h = Handler()

        command = request.json['command']
        ticker = request.json['ticker']
        strike_price = float(request.json['strike_price'])
        option_type = request.json['option_type']
        price = float(request.json['price'])
        exp_date = request.json['exp_date']
        pct = float(request.json['pct'])

        data = h.execute_order(command, ticker, strike_price, option_type, price, exp_date, pct)
        return jsonify({'order_statuses': data})


@app.route('/get_exp_date',methods=["GET"])
def get_exp_date():
    if request.method == "GET":
        return nearest_friday()


@app.route('/get_option',methods=["POST"])
def get_option():
    if request.method == "POST":
        ticker = request.json['ticker']
        strike_price = request.json['strike_price']
        option_type = request.json['option_type']
        exp_date = request.json['exp_date']

        db, cursor = database.connect_db()
        query = "SELECT oauth FROM accounts WHERE name='oscar.s.lee@gmail.com' LIMIT 1;"
        cursor.execute(query)
        oauth_token = cursor.fetchall()[0][0]

        rh = Robinhood()
        rh.login(oauth=oauth_token)
        try:
            ticker = ticker.upper().strip()
        except AttributeError as message:
            print(message)
            return None

        option_id = id_for_option(ticker, exp_date, strike_price, option_type)
        instrument_url = urllib.parse.quote_plus(urls['option_instruments'](option_id))
        url = urls['option_data'](instrument_url)

        result = rh.send_get(url)
        return result


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000,debug=True)
