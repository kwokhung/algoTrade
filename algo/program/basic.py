import algo
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mpl_finance as mpf
import talib


class Program(object):

    @staticmethod
    def chart(fig, code, klines, sma_parameter1, sma_parameter2, sma_parameter3, macd_parameter1, macd_parameter2, macd_parameter3):
        for ax in fig.axes:
            fig.delaxes(ax)

        ax = fig.add_subplot(3, 1, 1)
        ax1 = fig.add_subplot(3, 1, 2, sharex=ax)
        ax2 = fig.add_subplot(3, 1, 3, sharex=ax)

        sma_1 = talib.SMA(np.array(klines['close']), sma_parameter1)
        sma_2 = talib.SMA(np.array(klines['close']), sma_parameter2)
        sma_3 = talib.SMA(np.array(klines['close']), sma_parameter3)

        ax.clear()

        ax.set_xticks(range(0, len(klines['time_key']), 30))
        ax.set_xticklabels(klines['time_key'][::30], rotation=90)
        ax.xaxis.set_tick_params(labelsize=0)

        ax.plot(sma_1, label='1st SMA')
        ax.plot(sma_2, label='2nd SMA')
        ax.plot(sma_3, label='3rd SMA')

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

        macd, signal, hist = talib.MACD(np.array(klines['close']), macd_parameter1, macd_parameter2, macd_parameter3)

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

        return sma_1, sma_2, sma_3, macd, signal, hist

    @staticmethod
    def trade_macd_sma(quote_ctx, trade_ctx, trade_env, code, qty_to_buy, short_sell_enable, qty_to_sell, macd, signal, sma_1, sma_2):
        if not algo.Trade.check_tradable(quote_ctx, trade_ctx, trade_env, code):
            return

        if algo.Program.sell_signal_from_macd_sma(-1, macd, signal, sma_1, sma_2, short_sell_enable):
            algo.Program.suggest_sell(quote_ctx, trade_ctx, trade_env, code, short_sell_enable, qty_to_sell)
        elif algo.Program.buy_signal_from_macd_sma(-1, macd, signal, sma_1, sma_2):
            algo.Program.suggest_buy(quote_ctx, trade_ctx, trade_env, code, qty_to_buy)

    @staticmethod
    def test_macd_sma(code, short_sell_enable, klines, macd_parameter1, macd_parameter2, macd_parameter3, sma_parameter1, sma_parameter2, sma_parameter3):
        # change_rate = np.array(klines['change_rate']) / 100
        close = np.array(klines['close'])
        change_rate = np.array(klines['close']) - np.array(klines['close'])
        action = np.array(klines['close']) - np.array(klines['close'])
        position = np.array(klines['close']) - np.array(klines['close'])
        p_l = np.array(klines['close']) - np.array(klines['close'])
        cumulated_p_l = np.array(klines['close']) - np.array(klines['close'])

        sma_1 = talib.SMA(np.array(klines['close']), sma_parameter1)
        sma_2 = talib.SMA(np.array(klines['close']), sma_parameter2)
        sma_3 = talib.SMA(np.array(klines['close']), sma_parameter3)

        macd, signal, hist = talib.MACD(np.array(klines['close']), macd_parameter1, macd_parameter2, macd_parameter3)

        for i in range(macd_parameter2 + macd_parameter3 - 2, len(klines['close'])):
            if algo.Program.sell_signal_from_macd_sma(i, macd, signal, sma_1, sma_2, short_sell_enable):
                if position[i - 1] > 0:
                    action[i] = -1
                elif position[i - 1] == 0 and short_sell_enable:
                    action[i] = -1
                else:
                    action[i] = 0
            elif algo.Program.buy_signal_from_macd_sma(i, macd, signal, sma_1, sma_2):
                if position[i - 1] <= 0:
                    action[i] = 1
                else:
                    action[i] = 0
            else:
                action[i] = 0

            change_rate[i] = (close[i] / close[i - 1]) - 1
            position[i] = position[i - 1] + action[i]
            p_l[i] = position[i - 1] * change_rate[i]
            cumulated_p_l[i] = cumulated_p_l[i - 1] + p_l[i]

            # print('close({}): {}'.format(i, close[i]))
            # print('change_rate({}): {}%'.format(i, change_rate[i]))
            # print('action({}): {}'.format(i, action[i]))
            # print('position({}): {}'.format(i, position[i]))
            # print('p&l({}): {}%'.format(i, p_l[i] * 100))
            # print('cumulated p&l({}): {}%'.format(i, cumulated_p_l[i] * 100))

        test_result = pd.DataFrame({'code': np.array(klines['code']), 'time_key': np.array(klines['time_key']),
                                    'close': np.array(klines['close']), 'change_rate': change_rate, 'macd': macd,
                                    'signal': signal, 'hist': hist, 'sma_1': sma_1,
                                    'sma_2': sma_2, 'sma_3': sma_3, 'action': action, 'position': position, 'p&l': p_l,
                                    'cumulated p&l': cumulated_p_l})
        print(test_result.tail(5))
        test_result.to_csv('C:/temp/result/{}_result_{}.csv'.format(code, time.strftime("%Y%m%d%H%M%S")), float_format='%f')

        return test_result

    @staticmethod
    def buy_signal_from_macd_sma(i, macd, signal, sma_1, sma_2):
        if macd[i] > signal[i] and False:
            return True

        if not (macd[i] > signal[i]):
            return False

        if not (macd[i] > signal[i] and macd[i - 2] > signal[i - 2] and macd[i - 4] > signal[i - 4]):
            return False

        if not (macd[i] > macd[i - 2] and macd[i - 2] > macd[i - 4]):
            return False

        if not (signal[i] > signal[i - 2] and signal[i - 1] > signal[i - 4]):
            return False

        if not (sma_1[i] > sma_2[i] and sma_1[i - 2] > sma_2[i - 2] and sma_1[i - 4] > sma_2[i - 4]):
            return False

        if not (sma_1[i] > sma_1[i - 2] and sma_1[i - 2] > sma_1[i - 4]):
            return False

        if not (sma_2[i] > sma_2[i - 2] and sma_2[i - 1] > sma_2[i - 4]):
            return False

        return True

    @staticmethod
    def sell_signal_from_macd_sma(i, macd, signal, sma_1, sma_2, short_sell_enable):
        if macd[i] < signal[i] and False:
            return True

        if not (macd[i] < signal[i]):
            return False

        if not (macd[i] < signal[i] and macd[i - 2] < signal[i - 2] and macd[i - 4] < signal[i - 4]):
            return False

        if not (macd[i] < macd[i - 2] and macd[i - 2] < macd[i - 4]):
            return False

        if not (signal[i] < signal[i - 2] and signal[i - 1] < signal[i - 4]):
            return False

        if not (sma_1[i] < sma_2[i] and sma_1[i - 2] < sma_2[i - 2] and sma_1[i - 4] < sma_2[i - 4]):
            return False

        if not (sma_1[i] < sma_1[i - 2] and sma_1[i - 2] < sma_1[i - 4]):
            return False

        if not (sma_2[i] < sma_2[i - 2] and sma_2[i - 1] < sma_2[i - 4]):
            return False

        return True

    @staticmethod
    def suggest_buy(quote_ctx, trade_ctx, trade_env, code, qty_to_buy):
        try:
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
        except Exception as e:
            print(e)

    @staticmethod
    def suggest_sell(quote_ctx, trade_ctx, trade_env, code, short_sell_enable, qty_to_sell):
        try:
            print('Suggest to sell')

            position = algo.Trade.get_position(trade_ctx, trade_env, code)
            print('Position: {}'.format(position))

            last_price = algo.Quote.get_last_price(quote_ctx, code)
            print('Last price: {}'.format(last_price))

            if position > 0:
                print('Sell {}'.format(position))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.sell(trade_ctx, trade_env, code, position, last_price)
            elif short_sell_enable:
                sell_qty = qty_to_sell + position
                print('Short Sell {}'.format(sell_qty))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.sell(trade_ctx, trade_env, code, sell_qty, last_price)
        except Exception as e:
            print(e)

    @staticmethod
    def force_to_liquidate(quote_ctx, trade_ctx, trade_env, code):
        try:
            print('Force to liquidate')

            position = algo.Trade.get_position(trade_ctx, trade_env, code)
            print('Position: {}'.format(position))

            last_price = algo.Quote.get_last_price(quote_ctx, code)
            print('Last price: {}'.format(last_price))

            if position > 0:
                print('Force Sell {}'.format(position))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.sell(trade_ctx, trade_env, code, position, last_price)
            elif position < 0:
                print('Force Buy back {}'.format(position))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.buy(trade_ctx, trade_env, code, position, last_price)
        except Exception as e:
            print(e)

