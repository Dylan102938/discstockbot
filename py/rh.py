from uuid import uuid4
from helper import *
import database
import requests
import random
import time

urls = {
    'login': lambda: 'https://api.robinhood.com/oauth2/token/',
    'challenge': lambda challenge_id: 'https://api.robinhood.com/challenge/{0}/respond/'.format(challenge_id),
    'account': lambda: 'https://api.robinhood.com/accounts/',
    'orders': lambda: 'https://api.robinhood.com/options/orders/',
    'option_orders': lambda order_id=None: 'https://api.robinhood.com/options/orders/{0}/'.format(order_id) if order_id else 'https://api.robinhood.com/options/orders/',
    'option_instruments': lambda id=None: 'https://api.robinhood.com/options/instruments/{0}/'.format(id) if id else 'https://api.robinhood.com/options/instruments/',
    'option_data': lambda url: 'https://api.robinhood.com/marketdata/options/?instruments={0}'.format(url),
    'owned_options': lambda: 'https://api.robinhood.com/options/aggregate_positions/?nonzero=True'
}

class Robinhood:
    def __init__(self):
        self.session = requests.session()
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en;q=1, fr;q=0.9, de;q=0.8, ja;q=0.7, nl;q=0.6, it;q=0.5",  # noqa: E501
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "X-Robinhood-API-Version": "1.0.0",
            "Connection": "keep-alive",
            "User-Agent": "Robinhood/823 (iPhone; iOS 7.1.2; Scale/2.00)",
        }
        self.session.headers = self.headers

    def login(self, username=None, password=None, oauth=None, mfa_code=False, equity=0):
        data = dict()
        if not oauth:
            device_token = generate_device_token()

            url = urls['login']()
            payload = {
                'client_id': 'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS',
                'expires_in': 86400,
                'grant_type': 'password',
                'password': password,
                'scope': 'internal',
                'username': username,
                'challenge_type': 'sms',
                'device_token': device_token
            }

            if mfa_code:
                payload['mfa_code'] = mfa_code

            data = self.send_post(url, payload)

            if data:
                if 'mfa_required' in data:
                    mfa_token = input("Please type in the MFA code: ")
                    payload['mfa_code'] = mfa_token
                    res = self.send_post(url, payload, jsonify_data=False)
                    while (res.status_code != 200):
                        mfa_token = input(
                            "That MFA code was not correct. Please type in another MFA code: ")
                        payload['mfa_code'] = mfa_token
                        res = self.send_post(url, payload, jsonify_data=False)
                    data = res.json()

                elif 'challenge' in data:
                    challenge_id = data['challenge']['id']
                    sms_code = input('Enter Robinhood code for validation: ')
                    res = self.send_post(urls['challenge'](challenge_id), {'response': sms_code})
                    while 'challenge' in res and res['challenge']['remaining_attempts'] > 0:
                        sms_code = input('That code was not correct. {0} tries remaining. Please type in another code: '.format(
                            res['challenge']['remaining_attempts']))
                        res = self.send_post(urls['challenge'](challenge_id), {'response': sms_code})
                    self.session.headers['X-ROBINHOOD-CHALLENGE-RESPONSE-ID'] = challenge_id
                    data = self.send_post(url, payload)

                if 'access_token' in data:
                    token = '{0} {1}'.format(data['token_type'], data['access_token'])
                    self.session.headers['Authorization'] = token
                    data['detail'] = "logged in with brand new authentication code."

                    db, cursor = database.connect_db()
                    database.add_user(db, cursor, username, token, int(data['expires_in']), data['refresh_token'])

                else:
                    raise Exception(data['detail'])

            else:
                raise Exception('Error: Trouble connecting to robinhood API. Check internet connection.')

        else:
            self.session.headers['Authorization'] = oauth
            data['oauth_token'] = oauth
            data['detail'] = "logged in with old authentication code."

        self.equity = equity
        return(data)

    def refresh_oauth(self, oauth, refresh):
        self.session.headers['Authorization'] = oauth

        url = urls['login']()
        device_token = generate_device_token()
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "scope": "internal",
            "client_id": "c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS",
            "expires_in": 86400,
            "device_token": device_token
        }

        data = self.send_post(url, payload)
        if data:
            if 'access_token' in data:
                token = '{0} {1}'.format(data['token_type'], data['access_token'])
                data['oauth_token'] = token
                data['detail'] = "logged in with refresh token."

                refresh_time = int(time.time()) + data['expires_in']

                db, cursor = database.connect_db()
                database.update_user(db, cursor,
                            'UPDATE accounts SET oauth=%s, refresh=%s, refresh_time=%s WHERE oauth=%s',
                            (token, data['refresh_token'], refresh_time, oauth))

        else:
            raise Exception('Error: Trouble connecting to robinhood API. Check internet connection.')

        return(data)

    def load_account_profile(self, info=None):
        url = urls['account']()
        data = self.send_get(url, 'indexzero')

        return(data)

    def place_buy(self, symbol, expirationDate, strike, optionType, price, quantity):
        try:
            symbol = symbol.upper().strip()
        except AttributeError as message:
            print(message)
            return None

        optionID = id_for_option(symbol, expirationDate, strike, optionType)

        payload = {
            'account': self.load_account_profile()['url'],
            'direction': 'debit',
            'time_in_force': 'gfd',
            'legs': [
                {'position_effect': 'open', 'side': 'buy',
                    'ratio_quantity': 1, 'option': urls['option_instruments'](optionID)},
            ],
            'type': 'limit',
            'trigger': 'immediate',
            'price': price,
            'quantity': quantity,
            'override_day_trade_checks': False,
            'override_dtbp_checks': False,
            'ref_id': str(uuid4()),
        }

        url = urls['option_orders']()
        data = self.send_post(url, payload, json=True)

        return(data)

    def place_sell(self, symbol, expirationDate, strike, optionType, price, quantity):
        try:
            symbol = symbol.upper().strip()
        except AttributeError as message:
            print(message)
            return None

        optionID = id_for_option(symbol, expirationDate, strike, optionType)

        payload = {
            'account': self.load_account_profile()['url'],
            'direction': 'credit',
            'time_in_force': 'gfd',
            'legs': [
                {'position_effect': 'close', 'side': 'sell',
                    'ratio_quantity': 1, 'option': urls['option_instruments'](optionID)},
            ],
            'type': 'limit',
            'trigger': 'immediate',
            'price': price,
            'quantity': quantity,
            'override_day_trade_checks': False,
            'override_dtbp_checks': False,
            'ref_id': str(uuid4()),
        }

        url = urls['option_orders']()
        data = self.send_post(url, payload, json=True)

        return(data)

    def get_positions(self, target=None):
        url = urls['owned_options']()

        data = self.send_get(url)
        option_list = []
        for option in data['results']:
            if len(option['legs']) < 2:
                option_list.append(option)

        if not target:
            return option_list

        else:
            for o in option_list:
                if target['ticker'] == o['symbol'] and target['option_type'] == o['legs'][0]['option_type']:
                    return o

    def send_post(self, url, payload=None, timeout=16, json=False, jsonify_data=True):
        data = None
        res = None
        try:
            if json:
                self.session.headers['Content-Type'] = 'application/json'
                res = self.session.post(url, json=payload, timeout=timeout)
                self.session.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=utf-8';
            else:
                res = self.session.post(url, data=payload, timeout=timeout)
            data = res.json()

        except Exception as message:
            print("Error in send_post: {0}".format(message))

        if jsonify_data:
            return(data)
        else:
            return(res)

    def send_get(self, url, dataType='regular', payload=None, jsonify_data=True):
        if (dataType == 'results' or dataType == 'pagination'):
            data = [None]
        else:
            data = None

        res = None
        if jsonify_data:
            try:
                res = self.session.get(url, params=payload)
                res.raise_for_status()
                data = res.json()
            except (requests.exceptions.HTTPError, AttributeError) as message:
                print(message)
                return(data)
        else:
            res = self.session.get(url, params=payload)
            return(res)

        if (dataType == 'results'):
            try:
                data = data['results']
            except KeyError as message:
                print("{0} is not a key in the dictionary".format(message))
                return([None])
        elif (dataType == 'pagination'):
            counter = 2
            nextData = data
            try:
                data = data['results']
            except KeyError as message:
                print("{0} is not a key in the dictionary".format(message))
                return([None])

            if nextData['next']:
                print('Found Additional pages.')
            while nextData['next']:
                try:
                    res = self.session.get(nextData['next'])
                    res.raise_for_status()
                    nextData = res.json()
                except:
                    print('Additional pages exist but could not be loaded.')
                    return(data)
                print('Loading page '+str(counter)+' ...')
                counter += 1
                for item in nextData['results']:
                    data.append(item)
        elif (dataType == 'indexzero'):
            try:
                data = data['results'][0]
            except KeyError as message:
                print("{0} is not a key in the dictionary".format(message))
                return(None)
            except IndexError as message:
                return(None)

        return(data)
