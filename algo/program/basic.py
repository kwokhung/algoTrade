import algo
import numpy as np
import matplotlib.pyplot as plt
import mpl_finance as mpf
import talib


class Program(object):

    @staticmethod
    def chart(fig, code, klines):
        for ax in fig.axes:
            fig.delaxes(ax)

        ax = fig.add_subplot(3, 1, 1)
        ax1 = fig.add_subplot(3, 1, 2, sharex=ax)
        ax2 = fig.add_subplot(3, 1, 3, sharex=ax)

        sma_10 = talib.SMA(np.array(klines['close']), 10)
        sma_20 = talib.SMA(np.array(klines['close']), 20)
        sma_60 = talib.SMA(np.array(klines['close']), 60)

        ax.clear()

        ax.set_xticks(range(0, len(klines['time_key']), 30))
        ax.set_xticklabels(klines['time_key'][::30], rotation=90)
        ax.xaxis.set_tick_params(labelsize=0)

        ax.plot(sma_10, label='10 SMA')
        ax.plot(sma_20, label='20 SMA')
        ax.plot(sma_60, label='60 SMA')

        ax.legend(loc='upper left')
        ax.grid(True)

        mpf.candlestick2_ochl(
            ax,
            klines['open'],
            klines['close'],
            klines['high'],
            klines['low'],
            width=1,
            colorup='r',
            colordown='green',
            alpha=0.6)

        macd, signal, hist = talib.MACD(np.array(klines['close']), 12, 26, 9)

        ax1.clear()

        ax1.set_xticks(range(0, len(klines['time_key']), 30))
        ax1.set_xticklabels(klines['time_key'][::30], rotation=90)
        ax1.xaxis.set_tick_params(labelsize=0)

        ax1.plot(macd, label='DIF')
        ax1.plot(signal, label='DEA')

        ax1.legend(loc='upper left')
        ax1.grid(True)

        ax2.clear()

        ax2.set_xticks(range(0, len(klines['time_key']), 30))
        ax2.set_xticklabels(klines['time_key'][::30], rotation=30, horizontalalignment='right')

        mpf.volume_overlay(
            ax2,
            klines['open'],
            klines['close'],
            klines['volume'],
            colorup='r',
            colordown='g',
            width=1,
            alpha=0.8)

        ax2.grid(True)

        plt.subplots_adjust(hspace=0)
        plt.ylabel('Stock Price ({})'.format(code))
        plt.xlabel('Time (Min)')

        return sma_10, sma_20, sma_60, macd, signal, hist

    @staticmethod
    def trade_macd(quote_ctx, trade_ctx, trade_env, code, qty_to_buy, macd, signal, hist):
        if not algo.Trade.check_tradable(quote_ctx, code):
            return

        if macd[-1] < signal[-1]:
            if macd[-2] > signal[-2]:
                print('Turning point from high to low')

            algo.Program.suggest_sell(quote_ctx, trade_ctx, trade_env, code)

        if macd[-1] > signal[-1]:
            if macd[-2] < signal[-2]:
                print('Turning point from low to high')

            algo.Program.suggest_buy(quote_ctx, trade_ctx, trade_env, code, qty_to_buy)

    @staticmethod
    def suggest_buy(quote_ctx, trade_ctx, trade_env, code, qty_to_buy):
        print('Suggest to buy')

        position = algo.Trade.get_position(trade_ctx, trade_env, code)
        print('Position: {}'.format(position))

        last_price = algo.Quote.get_last_price(quote_ctx, code)
        print('Last price: {}'.format(last_price))

        if position < qty_to_buy:
            buy_qty = qty_to_buy - position
            print('Buy {}'.format(buy_qty))
            algo.Trade.clear_order(trade_ctx, trade_env, code)
            algo.Trade.buy(trade_ctx, trade_env, code, buy_qty, last_price)

    @staticmethod
    def suggest_sell(quote_ctx, trade_ctx, trade_env, code):
        print('Suggest to sell')

        position = algo.Trade.get_position(trade_ctx, trade_env, code)
        print('Position: {}'.format(position))

        last_price = algo.Quote.get_last_price(quote_ctx, code)
        print('Last price: {}'.format(last_price))

        if position > 0:
            print('Sell {}'.format(position))
            algo.Trade.clear_order(trade_ctx, trade_env, code)
            algo.Trade.sell(trade_ctx, trade_env, code, position, last_price)
