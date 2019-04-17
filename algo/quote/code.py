import futu as ft
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import mpl_finance as mpf
import talib


class Code(object):

    def __init__(self, code, start, end, qty_to_buy):
        self.code = code
        self.start = start
        self.end = end
        self.qty_to_buy = qty_to_buy
        self.position = 0

        self.api_svr_ip = '127.0.0.1'
        self.api_svr_port = 11111
        self.unlock_password = 'xxxxxx'
        self.trade_env = ft.TrdEnv.REAL

        self.quote_ctx, self.trade_ctx = self.context_setting()

        self.fig = plt.figure(figsize=(8, 6))
        self.ax = self.fig.add_subplot(3, 1, 1)
        self.ax1 = self.fig.add_subplot(3, 1, 2, sharex=self.ax)
        self.ax2 = self.fig.add_subplot(3, 1, 3, sharex=self.ax)
        self.fig.subplots_adjust(bottom=0.28)

    def __del__(self):
        self.quote_ctx.close()

    def print(self):
        print('Code {}'.format(self.code))

    def context_setting(self):
        quote_ctx = ft.OpenQuoteContext(host=self.api_svr_ip, port=self.api_svr_port)

        if 'HK.' in self.code:
            trade_ctx = ft.OpenHKTradeContext(host=self.api_svr_ip, port=self.api_svr_port)
        elif 'SH.' in self.code:
            trade_ctx = ft.OpenCNTradeContext(host=self.api_svr_ip, port=self.api_svr_port)
        elif 'SZ.' in self.code:
            trade_ctx = ft.OpenCNTradeContext(host=self.api_svr_ip, port=self.api_svr_port)
        elif 'US.' in self.code:
            if self.trade_env == ft.TrdEnv.SIMULATE:
                raise Exception('US Stock Trading does not support simulation')

            trade_ctx = ft.OpenUSTradeContext(host=self.api_svr_ip, port=self.api_svr_port)

        ret_code, ret_data = trade_ctx.unlock_trade(self.unlock_password)

        if ret_code != ft.RET_OK:
            raise Exception('Unlock Trading failed')

        return quote_ctx, trade_ctx

    def get_kline(self, start, end):
        ret_code, df, page_req_key = self.quote_ctx.request_history_kline(
            self.code,
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
            print('{}: {}'.format(df['time_key'].iloc[-1], df['close'].iloc[-1]))

            df.to_csv('C:/temp/{}.csv'.format(self.code))

            return ft.RET_OK, df
        else:
            print('return_code: {}'.format(ret_code))

            return ft.RET_ERROR

    def chart(self, df):
        sma_10 = talib.SMA(np.array(df['close']), 10)
        sma_20 = talib.SMA(np.array(df['close']), 20)
        sma_60 = talib.SMA(np.array(df['close']), 60)

        self.ax.clear()

        self.ax.set_xticks(range(0, len(df['time_key']), 30))
        self.ax.set_xticklabels(df['time_key'][::30], rotation=90)

        self.ax.plot(sma_10, label='10 SMA')
        self.ax.plot(sma_20, label='20 SMA')
        self.ax.plot(sma_60, label='60 SMA')

        self.ax.legend(loc='upper left')
        self.ax.grid(True)

        mpf.candlestick2_ochl(
            self.ax,
            df['open'],
            df['close'],
            df['high'],
            df['low'],
            width=1,
            colorup='r',
            colordown='green',
            alpha=0.6)

        macd, signal, hist = talib.MACD(np.array(df['close']), 12, 26, 9)

        self.ax1.clear()

        self.ax1.set_xticks(range(0, len(df['time_key']), 30))
        self.ax1.set_xticklabels(df['time_key'][::30], rotation=90)

        self.ax1.plot(macd, label='DIF')
        self.ax1.plot(signal, label='DEA')

        self.ax1.legend(loc='upper left')
        self.ax1.grid(True)

        self.ax2.clear()

        self.ax2.set_xticks(range(0, len(df['time_key']), 30))
        self.ax2.set_xticklabels(df['time_key'][::30], rotation=30, horizontalalignment='right')

        mpf.volume_overlay(
            self.ax2,
            df['open'],
            df['close'],
            df['volume'],
            colorup='r',
            colordown='g',
            width=1,
            alpha=0.8)

        plt.subplots_adjust(hspace=0)
        plt.ylabel('Stock Price ({})'.format(self.code))
        plt.xlabel('Time (Min)')

        self.trade_macd(macd, signal, hist)

    def plot_chart(self, df):
        self.chart(df)

        plt.show()

    def animate(self, i):
        print('Animate: {}'.format(i))

        ret_code, df = self.get_kline(self.start, self.end)

        if ret_code == ft.RET_OK:
            self.chart(df)

    def animate_chart(self):
        ani = animation.FuncAnimation(self.fig, self.animate, interval=3000)
        plt.show()

    def trade_macd(self, macd, signal, hist):
        if macd[-1] < signal[-1]:
            if macd[-2] > signal[-2]:
                print('Turning point from high to low')

            self.suggest_sell()

        if macd[-1] > signal[-1]:
            if macd[-2] < signal[-2]:
                print('Turning point from low to high')

            self.suggest_buy()

    def suggest_buy(self):
        print('Suggest to buy')

        position = self.get_position()
        print('Position: {}'.format(position))

        last_price = self.get_last_price()
        print('Last price: {}'.format(last_price))

        if position <= 0:
            print('Buy {}'.format(self.qty_to_buy))
            self.buy(self.qty_to_buy, last_price)

    def suggest_sell(self):
        print('Suggest to sell')

        position = self.get_position()
        print('Position: {}'.format(position))

        last_price = self.get_last_price()
        print('Last price: {}'.format(last_price))

        if position > 0:
            print('Sell {}'.format(position))
            self.sell(position, last_price)

    def get_position(self):
        ret_code, position_list = self.trade_ctx.position_list_query(trd_env=self.trade_env)

        if ret_code != ft.RET_OK:
            raise Exception('Failed to get positions')

        positions = position_list.set_index('code')

        try:
            position = int(positions['qty'][self.code])
        except KeyError:
            position = 0

        return position

    def get_last_price(self):
        ret_code, market_snapshot = self.quote_ctx.get_market_snapshot([self.code])

        if ret_code != ft.RET_OK:
            raise Exception('Failed to get snapshot')

        last_price = market_snapshot['last_price'][0]

        return last_price

    def buy(self, qty, price):
        """
        ret_code, acc_info = self.trade_ctx.accinfo_query(trd_env=self.trade_env)

        if ret_code != ft.RET_OK:
            raise Exception('Failed to get accinfo')

        ret_code, market_snapshot = self.quote_ctx.get_market_snapshot([self.code])

        if ret_code != ft.RET_OK:
            raise Exception('Failed to get snapshot')

        lot_size = market_snapshot['lot_size'][0]
        last_price = market_snapshot['last_price'][0]
        power = acc_info['Power'][0]
        qty = int(math.floor(power / last_price))
        qty = qty // lot_size * lot_size
        """
        ret_code, order = self.trade_ctx.place_order(
            qty=qty,
            price=price,
            code=self.code,
            trd_side=ft.TrdSide.BUY,
            order_type=ft.OrderType.NORMAL,
            trd_env=self.trade_env)

        return ret_code, order

    def sell(self, qty, price):
        ret_code, order = self.trade_ctx.place_order(
            qty=qty,
            price=price,
            code=self.code,
            trd_side=ft.TrdSide.SELL,
            order_type=ft.OrderType.NORMAL,
            trd_env=self.trade_env)

        return ret_code, order
