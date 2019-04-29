import futu as ft
import pandas as pd
import requests


class Quote(object):

    @staticmethod
    def get_kline(quote_ctx, code, start, end):
        if 'US.' in code:
            return Quote.get_kline_worldtradingdata(code)

        ret_code, klines, page_req_key = quote_ctx.request_history_kline(
            code=code,
            start=start,
            end=end,
            ktype=ft.KLType.K_1M,
            autype=ft.AuType.QFQ,
            fields=[
                ft.KL_FIELD.DATE_TIME,
                ft.KL_FIELD.OPEN,
                ft.KL_FIELD.HIGH,
                ft.KL_FIELD.LOW,
                ft.KL_FIELD.CLOSE,
                ft.KL_FIELD.CHANGE_RATE,
                ft.KL_FIELD.TRADE_VOL
                # , ft.KL_FIELD. LAST_CLOSE, ft.KL_FIELD.TRADE_VAL, ft.KL_FIELD.TURNOVER_RATE
            ],
            max_count=60 * 24)

        if ret_code == ft.RET_OK:
            print('{}: {}'.format(klines['time_key'].iloc[-1], klines['close'].iloc[-1]))

            klines.to_csv('C:/temp/{}_klines.csv'.format(code))

            return ft.RET_OK, klines
        else:
            print('return_code: {}'.format(ret_code))

            return ft.RET_ERROR

    @staticmethod
    def get_kline_worldtradingdata(code):
        request_parameters = {'symbol': code.replace('US.', ''), 'range': '1', 'interval': '1', 'sort': 'asc', 'api_token': 'p2MH2x7gGdbRFUM24CxGESjDhJf541J2T1fOjQzDhQVWXXG61pmQLzKPhS1A'}
        response = requests.get('https://www.worldtradingdata.com/api/v1/intraday', request_parameters)

        if response.status_code != 200:
            print('status_code: {}'.format(response.status_code))

            return ft.RET_ERROR

        try:
            response_data = response.json()
            symbol = response_data['symbol']
            intraday = response_data['intraday']

            for time_key in intraday:
                klines.loc[len(klines)] = [code, time_key, intraday[time_key]['open'], intraday[time_key]['high'],
                                           intraday[time_key]['low'], intraday[time_key]['close'], 0,
                                           intraday[time_key]['volume']]

            klines = pd.DataFrame(columns=['code', 'time_key', 'open', 'high', 'low', 'close', 'change_rate', 'volume'])
        except KeyError:
            klines = pd.read_csv('C:/temp/worldtradingdata_klines.csv')

        print(klines.tail(5))
        print('{}: {}'.format(klines['time_key'].iloc[-1], klines['close'].iloc[-1]))

        klines.to_csv('C:/temp/{}_klines.csv'.format(code))
        return ft.RET_OK, klines

    @staticmethod
    def get_last_price(quote_ctx, code):
        if 'US.' in code:
            return Quote.get_last_price_worldtradingdata(code)

        ret_code, market_snapshot = quote_ctx.get_market_snapshot([code])

        if ret_code != ft.RET_OK:
            raise Exception('Failed to get snapshot')

        last_price = market_snapshot['last_price'][0]

        return last_price

    @staticmethod
    def get_last_price_worldtradingdata(code):
        request_parameters = {'symbol': code.replace('US.', ''), 'api_token': 'p2MH2x7gGdbRFUM24CxGESjDhJf541J2T1fOjQzDhQVWXXG61pmQLzKPhS1A'}
        response = requests.get('https://www.worldtradingdata.com/api/v1/stock', request_parameters)

        if response.status_code != 200:
            print('status_code: {}'.format(response.status_code))

            return ft.RET_ERROR

        try:
            response_data = response.json()
            last_price = float(response_data['data'][0]['price'])
        except KeyError:
            last_price = 0
        except IndexError:
            last_price = 0
        except ValueError:
            last_price = 0

        return last_price

