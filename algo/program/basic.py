import algo
import futu as ft
import time
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mpl_finance as mpf
import talib
import logging


class Program(object):
    logger = logging.getLogger('algoTrade')

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
    def trade(quote_ctx, trade_ctx, trade_env, code, qty_to_buy, short_sell_enable, qty_to_sell, strategy, neg_to_liquidate, pos_to_liquidate, not_dare_to_buy, not_dare_to_sell, time_key, close, prev_close_price, macd, signal, sma_1, sma_2):
        algo.Program.logger.info('trade for {}'.format(code))

        if not algo.Trade.check_tradable(quote_ctx, trade_ctx, trade_env, code):
            algo.Program.logger.info('not tradable')
            return

        if algo.Program.order_exist(trade_ctx, trade_env, code):
            algo.Program.logger.info('Clear Order')
            algo.Trade.clear_order(trade_ctx, trade_env, code)

        i = len(close) - 1

        if algo.Program.time_to_liquidate(code, time_key[i]):
            algo.Program.force_to_liquidate(quote_ctx, trade_ctx, trade_env, code)
        elif algo.Program.get_position(trade_ctx, trade_env, code) != 0:
            if algo.Program.need_to_cut_loss(trade_ctx, trade_env, code, neg_to_liquidate, close(i), prev_close_price) or \
                    algo.Program.need_to_cut_profit(trade_ctx, trade_env, code, pos_to_liquidate):
                algo.Program.force_to_liquidate(quote_ctx, trade_ctx, trade_env, code)
        elif not algo.Program.time_to_stop_trade(code, time_key[i]):
            if algo.Program.sell_signal_occur(i, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, not_dare_to_sell):
                if short_sell_enable:
                    if close[i] < prev_close_price:
                        algo.Program.suggest_sell(quote_ctx, trade_ctx, trade_env, code, short_sell_enable, qty_to_sell)
                    else:
                        algo.Program.logger.info('not lower than last close: {}. @{} ({})'.format(i, close[i], prev_close_price))
                else:
                    algo.Program.logger.info('cannot short sell')
            elif algo.Program.buy_signal_occur(i, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, not_dare_to_buy):
                if close[i] > prev_close_price:
                    algo.Program.suggest_buy(quote_ctx, trade_ctx, trade_env, code, qty_to_buy)
                else:
                    algo.Program.logger.info('not higher than last close: {}. @{} ({})'.format(i, close[i], prev_close_price))

    @staticmethod
    def test(quote_ctx, trade_ctx, trade_env, code, short_sell_enable, strategy, neg_to_liquidate, pos_to_liquidate, not_dare_to_buy, not_dare_to_sell, klines, macd_parameter1, macd_parameter2, macd_parameter3, sma_parameter1, sma_parameter2, sma_parameter3):
        algo.Program.logger.info('test for {}'.format(code))

        # prev_close_price = algo.Quote.get_prev_close_price(quote_ctx, code)
        prev_close_price = klines['last_close'].iloc[0]

        time_key = np.array(klines['time_key'])
        close = np.array(klines['close'])
        change_rate = close - close
        action = close - close
        position = close - close
        p_l = close - close
        cumulated_p_l = close - close
        realized_p_l = close - close

        sma_1 = talib.SMA(close, sma_parameter1)
        sma_2 = talib.SMA(close, sma_parameter2)
        sma_3 = talib.SMA(close, sma_parameter3)

        macd, signal, hist = talib.MACD(close, macd_parameter1, macd_parameter2, macd_parameter3)

        for i in range(5, len(close)):
            if algo.Program.time_to_liquidate(code, time_key[i]):
                if position[i - 1] > 0:
                    algo.Program.logger.info('Force sell {}. @{}'.format(i, close[i]))
                    action[i] = -1
                elif position[i - 1] < 0:
                    algo.Program.logger.info('Force buy back {}. @{}'.format(i, close[i]))
                    action[i] = 1
                else:
                    action[i] = 0
            elif position[i - 1] != 0:
                if (position[i - 1] > 0 and close[i] < prev_close_price and cumulated_p_l[i - 1] * 100 < -(neg_to_liquidate * 5 / 8)) or \
                        (position[i - 1] < 0 and close[i] > prev_close_price and cumulated_p_l[i - 1] * 100 < -(neg_to_liquidate * 5 / 8)) or\
                        (cumulated_p_l[i - 1] * 100 < -neg_to_liquidate) or \
                        (cumulated_p_l[i - 1] * 100 > pos_to_liquidate):
                    if position[i - 1] > 0:
                        algo.Program.logger.info('Force sell {}. @{}'.format(i, close[i]))
                        action[i] = -1
                    elif position[i - 1] < 0:
                        algo.Program.logger.info('Force buy back {}. @{}'.format(i, close[i]))
                        action[i] = 1
                    else:
                        action[i] = 0
            elif not algo.Program.time_to_stop_trade(code, time_key[i]):
                if algo.Program.sell_signal_occur(i, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, not_dare_to_sell):
                    if short_sell_enable:
                        if close[i] < prev_close_price:
                            algo.Program.logger.info('Short sell {}. @{}'.format(i, close[i]))
                            action[i] = -1
                        else:
                            algo.Program.logger.info('not lower than last close: {}. @{} ({})'.format(i, close[i], prev_close_price))

                            action[i] = 0
                    else:
                        algo.Program.logger.info('cannot short sell')

                        action[i] = 0
                elif algo.Program.buy_signal_occur(i, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, not_dare_to_buy):
                    if close[i] > prev_close_price:
                        algo.Program.logger.info('Buy {}. @{}'.format(i, close[i]))
                        action[i] = 1
                    else:
                        algo.Program.logger.info('not higher than last close: {}. @{} ({})'.format(i, close[i], prev_close_price))

                        action[i] = 0
                else:
                    action[i] = 0
            else:
                action[i] = 0

            change_rate[i] = (close[i] / close[i - 1]) - 1 if close[i - 1] != 0 else 0
            position[i] = position[i - 1] + action[i]
            p_l[i] = position[i - 1] * change_rate[i]
            cumulated_p_l[i] = cumulated_p_l[i - 1] + p_l[i]
            realized_p_l[i] = realized_p_l[i - 1]

            if position[i] == 0 and cumulated_p_l[i] != 0:
                realized_p_l[i] = realized_p_l[i] + cumulated_p_l[i]
                cumulated_p_l[i] = 0

        test_result = pd.DataFrame({'code': np.array(klines['code']), 'time_key': time_key,
                                    'close': close, 'change_rate': change_rate, 'macd': macd,
                                    'signal': signal, 'hist': hist, 'sma_1': sma_1,
                                    'sma_2': sma_2, 'sma_3': sma_3, 'action': action, 'position': position, 'p&l': p_l,
                                    'cumulated p&l': cumulated_p_l, 'realized p&l': realized_p_l})
        print(test_result.tail(1))
        test_result.to_csv('C:/temp/result/{}_result_{}.csv'.format(code, time.strftime("%Y%m%d%H%M%S")), float_format='%f')

        return test_result

    @staticmethod
    def test_1(quote_ctx, trade_ctx, trade_env, code, short_sell_enable, strategy, klines, macd_parameter1, macd_parameter2, macd_parameter3, sma_parameter1, sma_parameter2, sma_parameter3):
        time_key = np.array(klines['time_key'])
        close = np.array(klines['close'])
        change_rate = close - close
        action = close - close
        position = close - close
        p_l = close - close
        cumulated_p_l = close - close

        sma_1 = talib.SMA(close, sma_parameter1)
        sma_2 = talib.SMA(close, sma_parameter2)
        sma_3 = talib.SMA(close, sma_parameter3)

        macd, signal, hist = talib.MACD(close, macd_parameter1, macd_parameter2, macd_parameter3)

        for i in range(macd_parameter2 + macd_parameter3 - 2, len(close)):
            if algo.Program.time_to_liquidate(code, time_key[i]) or\
                    (position[i - 1] != 0 and cumulated_p_l[i - 1] * 100 <= 0.5) or\
                    (position[i - 1] != 0 and cumulated_p_l[i - 1] * 100 > 1.0):
                if position[i - 1] > 0:
                    action[i] = -1
                elif position[i - 1] < 0:
                    action[i] = 1
                else:
                    action[i] = 0
            elif algo.Program.sell_signal_occur(i, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy):
                if position[i - 1] > 0:
                    action[i] = -1
                elif position[i - 1] == 0 and short_sell_enable:
                    action[i] = -1
                else:
                    action[i] = 0
            elif algo.Program.buy_signal_occur(i, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy):
                if position[i - 1] <= 0:
                    action[i] = 1
                else:
                    action[i] = 0
            else:
                action[i] = 0

            change_rate[i] = (close[i] / close[i - 1]) - 1 if close[i - 1] != 0 else 0
            position[i] = position[i - 1] + action[i]
            p_l[i] = position[i - 1] * change_rate[i]
            cumulated_p_l[i] = cumulated_p_l[i - 1] + p_l[i]

            # print('close({}): {}'.format(i, close[i]))
            # print('change_rate({}): {}%'.format(i, change_rate[i]))
            # print('action({}): {}'.format(i, action[i]))
            # print('position({}): {}'.format(i, position[i]))
            # print('p&l({}): {}%'.format(i, p_l[i] * 100))
            # print('cumulated p&l({}): {}%'.format(i, cumulated_p_l[i] * 100))

        test_result = pd.DataFrame({'code': np.array(klines['code']), 'time_key': time_key,
                                    'close': close, 'change_rate': change_rate, 'macd': macd,
                                    'signal': signal, 'hist': hist, 'sma_1': sma_1,
                                    'sma_2': sma_2, 'sma_3': sma_3, 'action': action, 'position': position, 'p&l': p_l,
                                    'cumulated p&l': cumulated_p_l})
        print(test_result.tail(1))
        test_result.to_csv('C:/temp/result/{}_result_{}.csv'.format(code, time.strftime("%Y%m%d%H%M%S")), float_format='%f')

        return test_result

    @staticmethod
    def time_to_liquidate(code, time_key):
        date_time = datetime.datetime.strptime(time_key, '%Y-%m-%d %H:%M:%S')

        if 'HK.' in code:
            liquidation_time = datetime.time(15, 45, 0)
        elif 'SH.' in code:
            liquidation_time = datetime.time(14, 45, 0)
        elif 'SZ.' in code:
            liquidation_time = datetime.time(14, 45, 0)
        elif 'US.' in code:
            liquidation_time = datetime.time(15, 45, 0)

        if ('HK.' in code or 'SH.' in code or 'SZ.' in code or 'US.' in code) and date_time.time() >= liquidation_time:
            algo.Program.logger.info('Time to liquidate: {}'.format(date_time))

            return True

        return False

    @staticmethod
    def time_to_stop_trade(code, time_key):
        date_time = datetime.datetime.strptime(time_key, '%Y-%m-%d %H:%M:%S')

        if 'HK.' in code:
            stop_trade_time = datetime.time(15, 15, 0)
        elif 'SH.' in code:
            stop_trade_time = datetime.time(14, 15, 0)
        elif 'SZ.' in code:
            stop_trade_time = datetime.time(14, 15, 0)
        elif 'US.' in code:
            stop_trade_time = datetime.time(15, 15, 0)

        if ('HK.' in code or 'SH.' in code or 'SZ.' in code or 'US.' in code) and date_time.time() >= stop_trade_time:
            algo.Program.logger.info('Time to stop trade: {}'.format(date_time))

            return True

        return False

    @staticmethod
    def get_position(trade_ctx, trade_env, code):
        positions = algo.Trade.get_positions(trade_ctx, trade_env, code)

        try:
            qty = int(positions['qty'])
        except TypeError:
            qty = 0
        except KeyError:
            qty = 0

        return qty

    @staticmethod
    def order_exist(trade_ctx, trade_env, code):
        ret_code, order_list = trade_ctx.order_list_query(trd_env=trade_env)

        for i, row in order_list.iterrows():
            if row['code'] == code and (row['order_status'] == ft.OrderStatus.SUBMITTED or row['order_status'] == ft.OrderStatus.FILLED_PART):
                return True

        return False

    @staticmethod
    def need_to_cut_loss(trade_ctx, trade_env, code, neg_to_liquidate, last_close, prev_close_price):
        positions = algo.Trade.get_positions(trade_ctx, trade_env, code)

        try:
            qty = int(positions['qty'])
            pl_ratio = float(positions['pl_ratio'])
        except TypeError:
            qty = 0
            pl_ratio = 0.0
        except KeyError:
            qty = 0
            pl_ratio = 0.0

        if qty > 0 and last_close < prev_close_price and pl_ratio < -(neg_to_liquidate * 5 / 8):
            algo.Program.logger.info('Need to cut loss quick after drop below previous close: {} < -{} ({})'.format(pl_ratio, (neg_to_liquidate * 5 / 8), code))

            return True
        elif qty < 0 and last_close > prev_close_price and pl_ratio < -(neg_to_liquidate * 5 / 8):
            algo.Program.logger.info('Need to cut loss quick after rise above previous close: {} < -{} ({})'.format(pl_ratio, (neg_to_liquidate * 5 / 8), code))

            return True
        elif qty != 0 and pl_ratio < -neg_to_liquidate:
            algo.Program.logger.info('Need to cut loss: {} < -{} ({})'.format(pl_ratio, neg_to_liquidate, code))

            return True

        return False

    @staticmethod
    def need_to_cut_profit(trade_ctx, trade_env, code, pos_to_liquidate):
        positions = algo.Trade.get_positions(trade_ctx, trade_env, code)

        try:
            qty = int(positions['qty'])
            pl_ratio = float(positions['pl_ratio'])
        except TypeError:
            qty = 0
            pl_ratio = 0.0
        except KeyError:
            qty = 0
            pl_ratio = 0.0

        if qty != 0 and pl_ratio > pos_to_liquidate:
            algo.Program.logger.info('Need to cut profit: {} > {} ({})'.format(pl_ratio, pos_to_liquidate, code))

            return True

        return False

    @staticmethod
    def buy_signal_occur(i, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, not_dare_to_buy):
        if strategy == 'A':
            return algo.Program.sell_signal_before_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable) or\
                   algo.Program.sell_signal_after_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable)
        elif strategy == 'B':
            return algo.Program.buy_signal_before_cross(i, close, macd, signal, sma_1, sma_2) or\
                   algo.Program.buy_signal_after_cross(i, close, macd, signal, sma_1, sma_2)
        elif strategy == 'C':
            return algo.Program.sell_signal_before_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable)
        elif strategy == 'D':
            return algo.Program.buy_signal_before_cross(i, close, macd, signal, sma_1, sma_2)
        elif strategy == 'E':
            return algo.Program.sell_signal_after_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable)
        elif strategy == 'F':
            return algo.Program.buy_signal_after_cross(i, close, macd, signal, sma_1, sma_2)
        elif strategy == 'G':
            if close[i] <= close[i - 1] or\
                    close[i - 1] < close[i - 2] or\
                    close[i - 2] < close[i - 3] or\
                    close[i - 3] < close[i - 4] or\
                    close[i - 4] < close[i - 5]:
                return False
            elif not algo.Program.dare_to_buy(i, close, not_dare_to_buy):
                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def dare_to_buy(i, close, not_dare_to_buy):
        algo.Program.logger.info('buy_signal_occur: {}. @{}'.format(i, close[i]))

        running = i - 1

        while running >= 0:
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage > not_dare_to_buy:
                algo.Program.logger.info('not dare_to_buy: {}. @ {} ({} > {})'.format(i, close[i], change_rate_percentage, not_dare_to_buy))

                return False

            running = running - 1

        return True

    @staticmethod
    def buy_signal_before_cross(i, close, macd, signal, sma_1, sma_2):
        if not (macd[i] > signal[i]):
            return False

        if not (macd[i - 2] < signal[i - 2]):
            return False

        if not (macd[i - 3] < signal[i - 3]):
            return False

        if close[i] <= close[i - 1] or close[i - 1] <= close[i - 2] or close[i - 2] <= close[i - 3]:
            return False

        return True

    @staticmethod
    def buy_signal_after_cross(i, close, macd, signal, sma_1, sma_2):
        if not (macd[i] > signal[i]):
            return False

        if not (macd[i - 1] > signal[i - 1]):
            return False

        if not (macd[i - 2] > signal[i - 2]):
            return False

        return True

    @staticmethod
    def sell_signal_occur(i, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, not_dare_to_sell):
        if strategy == 'A':
            return algo.Program.buy_signal_before_cross(i, close, macd, signal, sma_1, sma_2) or\
                   algo.Program.buy_signal_after_cross(i, close, macd, signal, sma_1, sma_2)
        elif strategy == 'B':
            return algo.Program.sell_signal_before_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable) or \
                   algo.Program.sell_signal_after_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable)
        elif strategy == 'C':
            return algo.Program.buy_signal_before_cross(i, close, macd, signal, sma_1, sma_2)
        elif strategy == 'D':
            return algo.Program.sell_signal_before_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable)
        elif strategy == 'E':
            return algo.Program.buy_signal_after_cross(i, close, macd, signal, sma_1, sma_2)
        elif strategy == 'F':
            return algo.Program.sell_signal_after_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable)
        elif strategy == 'G':
            if close[i] >= close[i - 1] or\
                    close[i - 1] > close[i - 2] or\
                    close[i - 2] > close[i - 3] or\
                    close[i - 3] > close[i - 4] or\
                    close[i - 4] > close[i - 5]:
                return False
            elif not algo.Program.dare_to_sell(i, close, not_dare_to_sell):
                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def dare_to_sell(i, close, not_dare_to_sell):
        algo.Program.logger.info('sell_signal_occur: {}. @{}'.format(i, close[i]))

        running = i - 1

        while running >= 0:
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage < -not_dare_to_sell:
                algo.Program.logger.info('not dare_to_sell: {}. @ {} ({} < -{})'.format(i, close[i], change_rate_percentage, not_dare_to_sell))

                return False

            running = running - 1

        return True

    @staticmethod
    def sell_signal_before_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable):
        if not (macd[i] < signal[i]):
            return False

        if not (macd[i - 2] > signal[i - 2]):
            return False

        if not (macd[i - 3] > signal[i - 3]):
            return False

        if close[i] >= close[i - 1] or close[i - 1] >= close[i - 2] or close[i - 2] >= close[i - 3]:
            return False

        return True

    @staticmethod
    def sell_signal_after_cross(i, close, macd, signal, sma_1, sma_2, short_sell_enable):
        if not (macd[i] < signal[i]):
            return False

        if not (macd[i - 1] < signal[i - 1]):
            return False

        if not (macd[i - 2] < signal[i - 2]):
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

            if position < 0:
                buy_qty = 0 - position
                algo.Program.logger.info('Buy Back {}'.format(buy_qty))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.buy(trade_ctx, trade_env, code, buy_qty, last_price)
            elif qty_to_buy - position > 0:
                buy_qty = qty_to_buy - position
                algo.Program.logger.info('Buy {}'.format(buy_qty))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.buy(trade_ctx, trade_env, code, buy_qty, last_price)
            else:
                algo.Program.logger.info('Position is full: {} >= {}'.format(position, qty_to_buy))
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
                algo.Program.logger.info('Sell {}'.format(position))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.sell(trade_ctx, trade_env, code, position, last_price)
            elif short_sell_enable and qty_to_sell + position > 0:
                sell_qty = qty_to_sell + position
                algo.Program.logger.info('Short Sell {}'.format(sell_qty))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.sell(trade_ctx, trade_env, code, sell_qty, last_price)
            else:
                algo.Program.logger.info('Position is full: {} <= -{}'.format(position, qty_to_sell))
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
                algo.Program.logger.info('Force Sell {}'.format(position))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.sell(trade_ctx, trade_env, code, position, last_price)
            elif position < 0:
                algo.Program.logger.info('Force Buy Back {}'.format(position))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.buy(trade_ctx, trade_env, code, position, last_price)
            else:
                algo.Program.logger.info('Position is zero')
        except Exception as e:
            print(e)

