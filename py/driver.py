from flask import Flask, request, jsonify
from flask_cors import CORS
from handler import *
import urllib.parse
import time

app = Flask(__name__)
CORS(app)


@app.route('/exec_order',methods=["POST"])
def exec_order():
    if request.method == "POST":
        h = Handler()
        rh = Robinhood()

        command = request.json['command']
        ticker = request.json['ticker']
        strike_price = float(request.json['strike_price'])
        option_type = request.json['option_type']
        price = float(request.json['price'])
        exp_date = request.json['exp_date']
        pct = float(request.json['pct'])

        try:
            watch_price = float(request.json['watch_price'])
        except:
            watch_price = None

        curr_price = float(rh.get_instrument_data(ticker)['last_trade_price'])
        counter = 0
        if option_type == 'call':
            while watch_price and curr_price < watch_price and counter < 3600:
                time.sleep(5)
                curr_price = float(rh.get_instrument_data(ticker)['last_trade_price'])
                counter += 1

        else:
            while watch_price and curr_price > watch_price and counter < 3600:
                time.sleep(5)
                curr_price = float(rh.get_instrument_data(ticker)['last_trade_price'])
                counter += 1

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

        rh = Robinhood()
        return rh.get_option_data(ticker, strike_price, option_type, exp_date)


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000,debug=True)
