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
    api_svr_ip = '127.0.0.1'
    api_svr_port = 11111
    quote_ctx = None
    hk_trade_ctx = None
    hkcc_trade_ctx = None
    us_trade_ctx = None
    trade_ctx = None
    trade_env = ''
    unlock_password = ''
    codes = None
    code_length = 0
    code_index = -1
    code = ''
    start = ''
    end = ''
    qty_to_buy = 0
    enable = False
    my_observer = None

    def __init__(self):
        self.quote_ctx, self.hk_trade_ctx, self.hkcc_trade_ctx, self.us_trade_ctx = algo.Helper.context_setting(self.api_svr_ip, self.api_svr_port, self.trade_env, self.unlock_password)

        self.get_codes()
        self.roll_code()

        self.fig = plt.figure(figsize=(8, 6))
        self.fig.subplots_adjust(bottom=0.28)

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
        self.unlock_password = self.codes['unlock_password'][self.code_index]

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

        self.print()

        self.trade_ctx = algo.Helper.trade_context_setting(self.hk_trade_ctx, self.hkcc_trade_ctx, self.us_trade_ctx, self.code)

    def animate(self, i):
        print('Animate: {}'.format(i))

        while not self.enable:
            self.roll_code()

        if self.enable:
            ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

            if ret_code == ft.RET_OK:
                sma_10, sma_20, sma_60, macd, signal, hist = algo.Program.chart(self.fig, self.code, klines, self.macd_parameters[0], self.macd_parameters[1], self.macd_parameters[2])
                # algo.Program.trade_macd(self.quote_ctx, self.trade_ctx, self.trade_env, self.code, self.qty_to_buy, macd, signal, hist)

        self.roll_code()

    def chart(self):
        ani = animation.FuncAnimation(self.fig, self.animate, interval=3000)
        plt.show()

    def trade(self):
        code_index = 0

        while True:
            print('Trade: {}'.format(code_index))

            if self.enable:
                ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

                if ret_code == ft.RET_OK:
                    macd, signal, hist = talib.MACD(np.array(klines['close']), self.macd_parameters[0], self.macd_parameters[1], self.macd_parameters[2])
                    algo.Program.trade_macd(self.quote_ctx, self.trade_ctx, self.trade_env, self.code, self.qty_to_buy, macd, signal, hist)

                time.sleep(3)

            self.roll_code()

            code_index = code_index + 1

    def test(self):
        code_index = 0

        # while code_index < self.code_length:
        while True:
            print('Test: {}'.format(code_index))

            if self.enable:
                ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

                if ret_code == ft.RET_OK:
                    change_rate = np.array(klines['change_rate']) / 100
                    action = np.array(klines['close']) - np.array(klines['close'])
                    position = np.array(klines['close']) - np.array(klines['close'])
                    p_l = np.array(klines['close']) - np.array(klines['close'])
                    cumulated_p_l = np.array(klines['close']) - np.array(klines['close'])

                    macd, signal, hist = talib.MACD(np.array(klines['close']), self.macd_parameters[0], self.macd_parameters[1], self.macd_parameters[2])

                    for i in range(self.macd_parameters[1] + self.macd_parameters[2] - 2, len(klines['close'])):
                        if macd[i] < signal[i] and position[i-1] > 0:
                            action[i] = -1
                        elif macd[i] > signal[i] and position[i-1] <= 0:
                            action[i] = 1
                        else:
                            action[i] = 0

                        position[i] = position[i-1] + action[i]
                        p_l[i] = position[i-1] * change_rate[i]
                        cumulated_p_l[i] = cumulated_p_l[i-1] + p_l[i]

                        # print('close({}): {}'.format(i, np.array(klines['close'])[i]))
                        # print('change_rate({}): {}%'.format(i, change_rate[i] * 100))
                        # print('action({}): {}'.format(i, action[i]))
                        # print('position({}): {}'.format(i, position[i]))
                        # print('p&l({}): {}%'.format(i, p_l[i] * 100))
                        # print('cumulated p&l({}): {}%'.format(i, cumulated_p_l[i] * 100))

                    test_result = pd.DataFrame({'code': np.array(klines['code']), 'time_key': np.array(klines['time_key']), 'close': np.array(klines['close']), 'change_rate': change_rate, 'macd': macd, 'signal': signal, 'hist': hist, 'action': action, 'position': position, 'p&l': p_l, 'cumulated p&l': cumulated_p_l})
                    print(test_result.tail(5))
                    test_result.to_csv('C:/temp/{}_result_{}.csv'.format(self.code, time.strftime("%Y%m%d%H%M%S")))

                time.sleep(3)

            self.roll_code()

            code_index = code_index + 1
