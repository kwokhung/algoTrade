import futu as ft
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import talib
import algo
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class Code(object):
    config = None
    api_svr_ip = ''
    api_svr_port = 0
    unlock_password = ''
    quote_ctx = None
    hk_trade_ctx = None
    hkcc_trade_ctx = None
    us_trade_ctx = None
    trade_ctx = None
    trade_env = ''
    codes = None
    code_length = 0
    code_index = -1
    code = ''
    start = ''
    end = ''
    qty_to_buy = 0
    enable = False
    short_sell_enable = False
    qty_to_sell = 0
    my_observer = None

    def __init__(self):
        self.get_config()
        self.quote_ctx, self.hk_trade_ctx, self.hkcc_trade_ctx, self.us_trade_ctx = algo.Helper.context_setting(self.api_svr_ip, self.api_svr_port, self.unlock_password)

        self.get_codes()
        self.roll_code()

        self.fig = plt.figure(figsize=(8, 6))
        self.fig.subplots_adjust(bottom=0.28)

        self.sma_parameters = [10, 20, 60]

        # month
        # self.macd_parameters = [3, 10, 8]
        # week
        # self.macd_parameters = [11, 30, 9]
        # day
        # self.macd_parameters = [12, 26, 9]
        # hour / minute
        # self.macd_parameters = [5, 35, 5]
        self.macd_parameters = [12, 26, 9]

        self.my_event_handler = PatternMatchingEventHandler(patterns=['*/code.csv'], ignore_patterns='', ignore_directories=False, case_sensitive=True)

        # self.my_event_handler.on_created = on_created
        # self.my_event_handler.on_deleted = on_deleted
        self.my_event_handler.on_modified = self.on_modified
        # self.my_event_handler.on_moved = on_moved

        self.my_observer = Observer()
        self.my_observer.schedule(self.my_event_handler, path='C:/temp/', recursive=True)

        self.my_observer.start()

    def __del__(self):
        if self.quote_ctx is not None:
            self.quote_ctx.close()

        if self.hk_trade_ctx is not None:
            self.hk_trade_ctx.close()

        if self.hkcc_trade_ctx is not None:
            self.hkcc_trade_ctx.close()

        if self.us_trade_ctx is not None:
            self.us_trade_ctx.close()

        if self.my_observer is not None:
            self.my_observer.stop()
            self.my_observer.join()

    def print(self):
        print('Code {}'.format(self.code))

    def get_config(self):
        self.config = pd.read_csv('C:/temp/config.csv')
        self.api_svr_ip = self.config['api_svr_ip'][0]
        self.api_svr_port = int(self.config['api_svr_port'][0])
        self.unlock_password = self.config['unlock_password'][0]

        print(self.config)

    def on_modified(self, event):
        if 'code.csv' in event.src_path:
            self.get_codes()

    def get_codes(self):
        self.codes = pd.read_csv('C:/temp/code.csv')
        self.code_length = len(self.codes['code'])
        self.code_index = -1

        print(self.codes)

    def roll_code(self):
        self.code_index = self.code_index + 1

        if self.code_index == self.code_length:
            self.code_index = 0

        self.trade_env = self.codes['trade_env'][self.code_index]

        self.code = self.codes['code'][self.code_index]

        self.start = self.codes['start'][self.code_index]

        if self.start == 'today':
            self.start = time.strftime("%Y-%m-%d")

        self.end = self.codes['end'][self.code_index]

        if self.end == 'today':
            self.end = time.strftime("%Y-%m-%d")

        self.qty_to_buy = self.codes['qty_to_buy'][self.code_index]

        if self.codes['enable'][self.code_index] == 'yes':
            self.enable = True
        else:
            self.enable = False

        if self.codes['short_sell_enable'][self.code_index] == 'yes':
            self.short_sell_enable = True
        else:
            self.short_sell_enable = False

        self.qty_to_sell = self.codes['qty_to_sell'][self.code_index]

        self.print()

        self.trade_ctx = algo.Helper.trade_context_setting(self.hk_trade_ctx,
                                                           self.hkcc_trade_ctx,
                                                           self.us_trade_ctx,
                                                           self.code)

    def animate(self, i):
        print('Animate: {}'.format(i))

        while not self.enable:
            self.roll_code()

        if self.enable:
            try:
                ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

                if ret_code == ft.RET_OK:
                    sma_1, sma_2, sma_3, macd, signal, hist = algo.Program.chart(self.fig, self.code, klines,
                                                                                 self.sma_parameters[0],
                                                                                 self.sma_parameters[1],
                                                                                 self.sma_parameters[2],
                                                                                 self.macd_parameters[0],
                                                                                 self.macd_parameters[1],
                                                                                 self.macd_parameters[2])
                    # algo.Program.trade_macd(self.quote_ctx, self.trade_ctx, self.trade_env, self.code, self.qty_to_buy, macd, signal, hist)
            except TypeError:
                print('get_kline failed')

        self.roll_code()

    def chart(self):
        ani = animation.FuncAnimation(self.fig, self.animate, interval=3000)
        plt.show()

    def trade(self):
        code_index = 0

        while True:
            print('Trade: {}'.format(code_index))

            if self.enable:
                try:
                    ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

                    if ret_code == ft.RET_OK:
                        macd, signal, hist = talib.MACD(np.array(klines['close']),
                                                        self.macd_parameters[0],
                                                        self.macd_parameters[1],
                                                        self.macd_parameters[2])
                        algo.Program.trade_macd(self.quote_ctx, self.trade_ctx, self.trade_env, self.code,
                                                self.qty_to_buy, macd, signal, hist)

                    time.sleep(3)
                except TypeError:
                    print('get_kline failed')

            self.roll_code()

            code_index = code_index + 1

    def test(self):
        code_index = 0

        # while code_index < self.code_length:
        while True:
            print('Test: {}'.format(code_index))

            if self.enable:
                try:
                    ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

                    if ret_code == ft.RET_OK:
                        # algo.Program.test_macd(self.code, klines, self.macd_parameters[0], self.macd_parameters[1], self.macd_parameters[2])
                        # algo.Program.test_sma(self.code, klines, self.sma_parameters[0], self.sma_parameters[1], self.sma_parameters[2])
                        algo.Program.test_macd_sma(self.code,
                                                   self.short_sell_enable,
                                                   klines,
                                                   self.macd_parameters[0],
                                                   self.macd_parameters[1],
                                                   self.macd_parameters[2],
                                                   self.sma_parameters[0],
                                                   self.sma_parameters[1],
                                                   self.sma_parameters[2])

                    time.sleep(3)
                except TypeError:
                    print('get_kline failed')

            self.roll_code()

            code_index = code_index + 1

    def test_year(self):
        trade_days = self.quote_ctx.get_trading_days(ft.Market.HK, start='2019-04-01', end='2019-04-26')

        time_column = pd.DataFrame(columns=['time_key'])

        for trade_day in trade_days[1]:
            time_column.loc[len(time_column)] = [trade_day['time']]

        year_result = pd.concat([time_column], axis=1)

        code_index = 0

        while code_index < self.code_length:
            print('Test: {}'.format(code_index))

            if self.enable:
                code_column = pd.DataFrame(columns=[self.code])

                for trade_day in trade_days[1]:
                    try:
                        ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, trade_day['time'], trade_day['time'])

                        if ret_code == ft.RET_OK:
                            test_result = algo.Program.test_macd_sma(self.code,
                                                                     self.short_sell_enable,
                                                                     klines,
                                                                     self.macd_parameters[0],
                                                                     self.macd_parameters[1],
                                                                     self.macd_parameters[2],
                                                                     self.sma_parameters[0],
                                                                     self.sma_parameters[1],
                                                                     self.sma_parameters[2])

                            cumulated_p_l = test_result['cumulated p&l'].iloc[-1]
                            code_column.loc[len(code_column)] = [cumulated_p_l]

                        time.sleep(3)
                    except TypeError:
                        print('get_kline failed')

                year_result = pd.concat([year_result, code_column], axis=1)
                print(year_result)

            self.roll_code()

            code_index = code_index + 1

        year_result.to_csv('C:/temp/result/year_result_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")))


