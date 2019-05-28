import algo
import futu as ft
from futu.quote.quote_get_warrant import Request
import pandas as pd
import requests


class Quote(object):

    # print(algo.Quote.get_trading_days(self.quote_ctx, ft.Market.HK, None, None))
    # print(algo.Quote.get_stock_basicinfo(self.quote_ctx, ft.Market.HK, ft.SecurityType.WARRANT, None))
    # print(algo.Quote.get_autype_list(self.quote_ctx, self.code))
    # print(algo.Quote.get_market_snapshot(self.quote_ctx, self.code))
    # print(algo.Quote.get_rt_data(self.quote_ctx, self.code))
    # print(algo.Quote.get_plate_stock(self.quote_ctx, 'HK.HSI Constituent'))
    # print(algo.Quote.get_plate_list(self.quote_ctx, self.code))
    # print(algo.Quote.get_broker_queue(self.quote_ctx, self.code))
    # print(algo.Quote.query_subscription(self.quote_ctx))
    # print(algo.Quote.get_global_state(self.quote_ctx))
    # print(algo.Quote.get_stock_quote(self.quote_ctx, self.code))
    # print(algo.Quote.get_rt_ticker(self.quote_ctx, self.code))
    # print(algo.Quote.get_cur_kline(self.quote_ctx, self.code))
    # print(algo.Quote.get_order_book(self.quote_ctx, self.code))
    # print(algo.Quote.get_referencestock_list(self.quote_ctx, self.code))
    # print(algo.Quote.get_owner_plate(self.quote_ctx, self.code))
    # print(algo.Quote.get_holding_change_list(self.quote_ctx, self.code))
    # print(algo.Quote.get_option_chain(self.quote_ctx, self.code))
    # print(algo.Quote.get_history_kl_quota(self.quote_ctx))
    # print(algo.Quote.get_rehab(self.quote_ctx, self.code))
    # print(algo.Quote.get_warrant(self.quote_ctx, self.code))
    # print(algo.Quote.get_capital_flow(self.quote_ctx, self.code))
    # print(algo.Quote.get_capital_distribution(self.quote_ctx, self.code))

    @staticmethod
    def get_trading_days(quote_ctx, market, start, end):
        ret_code, trading_days = quote_ctx.get_trading_days(market=market, start=start, end=end)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, trading_days
        else:
            print('return_code: ({}) {}'.format(ret_code, trading_days))

            return ft.RET_ERROR

    @staticmethod
    def get_stock_basicinfo(quote_ctx, market, stock_type, code_list):
        ret_code, stock_basicinfo = quote_ctx.get_stock_basicinfo(market=market, stock_type=stock_type, code_list=code_list)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, stock_basicinfo
        else:
            print('return_code: ({}) {}'.format(ret_code, stock_basicinfo))

            return ft.RET_ERROR

    @staticmethod
    def get_autype_list(quote_ctx, code):
        ret_code, autype_list = quote_ctx.get_autype_list(code_list=[code])

        if ret_code == ft.RET_OK:
            return ft.RET_OK, autype_list
        else:
            print('return_code: ({}) {}'.format(ret_code, autype_list))

            return ft.RET_ERROR

    @staticmethod
    def get_market_snapshot(quote_ctx, code):
        ret_code, market_snapshot = quote_ctx.get_market_snapshot(code_list=[code])

        if ret_code == ft.RET_OK:
            return ft.RET_OK, market_snapshot
        else:
            print('return_code: ({}) {}'.format(ret_code, market_snapshot))

            return ft.RET_ERROR

    @staticmethod
    def get_rt_data(quote_ctx, code):
        try:
            quote_ctx.subscribe([code], [ft.SubType.RT_DATA])

            ret_code, rt_data = quote_ctx.get_rt_data(code=code)

            if ret_code == ft.RET_OK:
                return ft.RET_OK, rt_data
            else:
                print('return_code: ({}) {}'.format(ret_code, rt_data))

                return ft.RET_ERROR
        finally:
            quote_ctx.unsubscribe([code], [ft.SubType.RT_DATA])

    @staticmethod
    def get_plate_stock(quote_ctx, plate_code):
        ret_code, plate_stock = quote_ctx.get_plate_stock(plate_code=plate_code)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, plate_stock
        else:
            print('return_code: ({}) {}'.format(ret_code, plate_stock))

            return ft.RET_ERROR

    @staticmethod
    def get_plate_list(quote_ctx, code):
        market = algo.Helper.get_market(code)

        ret_code, plate_list = quote_ctx.get_plate_list(market=market, plate_class=ft.Plate.ALL)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, plate_list
        else:
            print('return_code: ({}) {}'.format(ret_code, plate_list))

            return ft.RET_ERROR

    @staticmethod
    def get_broker_queue(quote_ctx, code):
        try:
            quote_ctx.subscribe([code], [ft.SubType.BROKER])

            ret_code, bid_broker_queue, ask_broker_queue = quote_ctx.get_broker_queue(code=code)

            if ret_code == ft.RET_OK:
                return ft.RET_OK, bid_broker_queue, ask_broker_queue
            else:
                print('return_code: ({}) {} / {}'.format(ret_code, bid_broker_queue, ask_broker_queue))

                return ft.RET_ERROR
        finally:
            quote_ctx.unsubscribe([code], [ft.SubType.BROKER])

    @staticmethod
    def query_subscription(quote_ctx):
        ret_code, subscription = quote_ctx.query_subscription(is_all_conn=True)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, subscription
        else:
            print('return_code: ({}) {}'.format(ret_code, subscription))

            return ft.RET_ERROR

    @staticmethod
    def get_global_state(quote_ctx):
        ret_code, global_state = quote_ctx.get_global_state()

        if ret_code == ft.RET_OK:
            return ft.RET_OK, global_state
        else:
            print('return_code: ({}) {}'.format(ret_code, global_state))

            return ft.RET_ERROR

    @staticmethod
    def get_stock_quote(quote_ctx, code):
        try:
            quote_ctx.subscribe([code], [ft.SubType.QUOTE])

            ret_code, stock_quote = quote_ctx.get_stock_quote(code_list=[code])

            if ret_code == ft.RET_OK:
                return ft.RET_OK, stock_quote
            else:
                print('return_code: ({}) {}'.format(ret_code, stock_quote))

                return ft.RET_ERROR
        finally:
            quote_ctx.unsubscribe([code], [ft.SubType.QUOTE])

    @staticmethod
    def get_rt_ticker(quote_ctx, code):
        try:
            quote_ctx.subscribe([code], [ft.SubType.TICKER])

            ret_code, rt_ticker = quote_ctx.get_rt_ticker(code=code, num=1000)

            if ret_code == ft.RET_OK:
                return ft.RET_OK, rt_ticker
            else:
                print('return_code: ({}) {}'.format(ret_code, rt_ticker))

                return ft.RET_ERROR
        finally:
            quote_ctx.unsubscribe([code], [ft.SubType.TICKER])

    @staticmethod
    def get_order_book(quote_ctx, code):
        try:
            quote_ctx.subscribe([code], [ft.SubType.ORDER_BOOK])

            ret_code, order_book = quote_ctx.get_order_book(code=code)

            if ret_code == ft.RET_OK:
                return ft.RET_OK, order_book
            else:
                print('return_code: ({}) {}'.format(ret_code, order_book))

                return ft.RET_ERROR
        finally:
            quote_ctx.unsubscribe([code], [ft.SubType.ORDER_BOOK])

    @staticmethod
    def get_referencestock_list(quote_ctx, code):
        ret_code, referencestock_list = quote_ctx.get_referencestock_list(code=code, reference_type=ft.SecurityReferenceType.WARRANT)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, referencestock_list
        else:
            print('return_code: ({}) {}'.format(ret_code, referencestock_list))

            return ft.RET_ERROR

    @staticmethod
    def get_owner_plate(quote_ctx, code):
        ret_code, owner_plate = quote_ctx.get_owner_plate(code_list=[code])

        if ret_code == ft.RET_OK:
            return ft.RET_OK, owner_plate
        else:
            print('return_code: ({}) {}'.format(ret_code, owner_plate))

            return ft.RET_ERROR

    @staticmethod
    def get_holding_change_list(quote_ctx, code):
        ret_code, holding_change_list = quote_ctx.get_holding_change_list(code=code, holder_type=ft.StockHolder.INSTITUTE, start=None, end=None)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, holding_change_list
        else:
            print('return_code: ({}) {}'.format(ret_code, holding_change_list))

            return ft.RET_ERROR

    @staticmethod
    def get_option_chain(quote_ctx, code):
        ret_code, option_chain = quote_ctx.get_option_chain(code=code, start=None, end=None, option_type=ft.OptionType.ALL, option_cond_type=ft.OptionCondType.ALL)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, option_chain
        else:
            print('return_code: ({}) {}'.format(ret_code, option_chain))

            return ft.RET_ERROR

    @staticmethod
    def get_history_kl_quota(quote_ctx):
        ret_code, history_kl_quota = quote_ctx.get_history_kl_quota(get_detail=True)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, history_kl_quota
        else:
            print('return_code: ({}) {}'.format(ret_code, history_kl_quota))

            return ft.RET_ERROR

    @staticmethod
    def get_rehab(quote_ctx, code):
        ret_code, rehab = quote_ctx.get_rehab(code=code)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, rehab
        else:
            print('return_code: ({}) {}'.format(ret_code, rehab))

            return ft.RET_ERROR

    @staticmethod
    def get_warrant(quote_ctx, code):
        req = Request()
        req.sort_field = ft.SortField.TURNOVER

        ret_code, warrant = quote_ctx.get_warrant(stock_owner=code, req=req)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, warrant
        else:
            print('return_code: ({}) {}'.format(ret_code, warrant))

            return ft.RET_ERROR

    @staticmethod
    def get_capital_flow(quote_ctx, code):
        ret_code, capital_flow = quote_ctx.get_capital_flow(stock_code=code)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, capital_flow
        else:
            print('return_code: ({}) {}'.format(ret_code, capital_flow))

            return ft.RET_ERROR

    @staticmethod
    def get_capital_distribution(quote_ctx, code):
        ret_code, capital_distribution = quote_ctx.get_capital_distribution(stock_code=code)

        if ret_code == ft.RET_OK:
            return ft.RET_OK, capital_distribution
        else:
            print('return_code: ({}) {}'.format(ret_code, capital_distribution))

            return ft.RET_ERROR

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
                ft.KL_FIELD.TRADE_VOL,
                ft.KL_FIELD.LAST_CLOSE
                # , ft.KL_FIELD. LAST_CLOSE, ft.KL_FIELD.TRADE_VAL, ft.KL_FIELD.TURNOVER_RATE
            ],
            max_count=60 * 24)

        if ret_code == ft.RET_OK:
            if len(klines['time_key']) > 0:
                print('{}: {}'.format(klines['time_key'].iloc[-1], klines['close'].iloc[-1]))

                klines.to_csv('C:/temp/{}_klines.csv'.format(code), float_format='%f')

                return ft.RET_OK, klines
            else:
                print('no klines')

                return ft.RET_ERROR
        else:
            print('return_code: ({}) {} / {}'.format(ret_code, klines, page_req_key))

            return ft.RET_ERROR

    @staticmethod
    def get_kline_worldtradingdata(code):
        request_parameters = {'symbol': code.replace('aUS.', ''), 'range': '7', 'interval': '1', 'sort': 'asc', 'api_token': 'p2MH2x7gGdbRFUM24CxGESjDhJf541J2T1fOjQzDhQVWXXG61pmQLzKPhS1A'}
        response = requests.get('https://www.worldtradingdata.com/api/v1/intraday', request_parameters)

        if response.status_code != 200:
            print('status_code: {}'.format(response.status_code))

            return ft.RET_ERROR

        try:
            response_data = response.json()
            symbol = response_data['symbol']
            intraday = response_data['intraday']

            klines = pd.DataFrame(columns=['code', 'time_key', 'open', 'high', 'low', 'close', 'change_rate', 'volume'])

            for time_key in intraday:
                klines.loc[len(klines)] = [code, time_key, float(intraday[time_key]['open']), float(intraday[time_key]['high']),
                                           float(intraday[time_key]['low']), float(intraday[time_key]['close']), 0.0,
                                           int(intraday[time_key]['volume'])]
        except KeyError:
            klines = pd.read_csv('C:/temp/worldtradingdata_klines.csv')

        if len(klines['time_key']) > 0:
            print(klines.tail(5))
            print('{}: {}'.format(klines['time_key'].iloc[-1], klines['close'].iloc[-1]))

            klines.to_csv('C:/temp/{}_klines.csv'.format(code), float_format='%f')

            return ft.RET_OK, klines
        else:
            print('no klines')

            return ft.RET_ERROR

    @staticmethod
    def get_last_price(quote_ctx, code):
        if 'US.' in code:
            return Quote.get_last_price_worldtradingdata(code)

        ret_code, market_snapshot = Quote.get_market_snapshot(quote_ctx, code)

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

    @staticmethod
    def get_prev_close_price(quote_ctx, code):
        ret_code, market_snapshot = Quote.get_market_snapshot(quote_ctx, code)

        if ret_code != ft.RET_OK:
            raise Exception('Failed to get snapshot')

        prev_close_price = market_snapshot['prev_close_price'][0]

        return prev_close_price
