import futu as ft
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import talib
import algo


class Code(object):

    def __init__(self, trade_env, unlock_password):
        self.api_svr_ip = '127.0.0.1'
        self.api_svr_port = 11111

        self.trade_env = trade_env
        self.unlock_password = unlock_password

        self.codes = pd.read_csv('C:/temp/code.csv')
        print(self.codes)

        self.code_index = -1
        self.code_length = len(self.codes['code'])

        self.code = ''
        self.start = ''
        self.end = ''
        self.qty_to_buy = 0
        self.enable = False
        self.update_code()

        self.quote_ctx, self.trade_ctx = algo.Helper.context_setting(self.api_svr_ip, self.api_svr_port, self.trade_env, self.unlock_password, self.code)

        self.fig = plt.figure(figsize=(8, 6))
        self.fig.subplots_adjust(bottom=0.28)

    def __del__(self):
        self.quote_ctx.close()
        self.trade_ctx.close()

    def print(self):
        print('Code {}'.format(self.code))

    def update_code(self):
        self.code_index = self.code_index + 1

        if self.code_index == self.code_length:
            self.code_index = 0

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

    def animate(self, i):
        print('Animate: {}'.format(i))

        ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

        if ret_code == ft.RET_OK:
            if self.enable:
                sma_10, sma_20, sma_60, macd, signal, hist = algo.Program.chart(self.fig, self.code, klines)
                algo.Program.trade_macd(self.quote_ctx, self.trade_ctx, self.trade_env, self.code, self.qty_to_buy, macd, signal, hist)

            self.update_code()

    def animate_chart(self):
        ani = animation.FuncAnimation(self.fig, self.animate, interval=3000)
        plt.show()

    def trade(self):
        i = 0

        while True:
            print('Trade: {}'.format(i))

            ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

            if ret_code == ft.RET_OK:
                if self.enable:
                    macd, signal, hist = talib.MACD(np.array(klines['close']), 12, 26, 9)
                    algo.Program.trade_macd(self.quote_ctx, self.trade_ctx, self.trade_env, self.code, self.qty_to_buy, macd, signal, hist)

                self.update_code()

            time.sleep(3)
            i = i + 1

    def test(self):
        i = 0

        while i < self.code_length:
            print('Test: {}'.format(i))

            ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

            if ret_code == ft.RET_OK:
                if self.enable:
                    change_rate = np.array(klines['change_rate']) / 100
                    action = np.array(klines['close']) - np.array(klines['close'])
                    position = np.array(klines['close']) - np.array(klines['close'])
                    p_l = np.array(klines['close']) - np.array(klines['close'])
                    cumulated_p_l = np.array(klines['close']) - np.array(klines['close'])
                    macd, signal, hist = talib.MACD(np.array(klines['close']), 12, 26, 9)

                    for i in range(33, len(klines['close']) - 1):
                        if macd[i] < signal[i] and position[i-1] > 0:
                            action[i] = -1
                        elif macd[i] > signal[i] and position[i-1] <= 0:
                            action[i] = 1
                        else:
                            action[i] = 0

                        position[i] = position[i-1] + action[i]
                        p_l[i] = position[i-1] * change_rate[i]
                        cumulated_p_l[i] = cumulated_p_l[i-1] + p_l[i]
                        print('cumulated p&l({}): {}%'.format(i, cumulated_p_l[i] * 100))

                self.update_code()

            i = i + 1
