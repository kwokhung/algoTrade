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
from sqlalchemy import create_engine
from firebase_admin import messaging


class Program(object):
    logger = logging.getLogger('algoTrade')

    engine = create_engine('mysql://algotrade:12345678@127.0.0.1:3306/algotrade?charset=utf8')

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
    def send_to_topic():
        topic = 'people'

        message = messaging.Message(
            notification=messaging.Notification(
                title='Algo Trade Alert',
                body='This alert is sent from algoTrade.py.'
            ),
            data={
                'landing_page': 'second',
                'price': '$1,234.56'
            },
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='fcm_push_icon'
                )
            ),
            topic=topic
        )

        response = messaging.send(message)

        print('Successfully sent message:', response)

    @staticmethod
    def trade(quote_ctx, trade_ctx, trade_env, is_time_to_stop_trade, is_time_to_liquidate, code, qty_to_buy, short_sell_enable, qty_to_sell, strategy, neg_to_liquidate, pos_to_liquidate, not_dare_to_buy, not_dare_to_sell, encourage_factor, time_key, close, prev_close_price, macd, signal, sma_1, sma_2):
        i = len(close) - 1

        algo.Program.logger.info('{} ({}): Trade for {}'.format(time_key[i], i, code))

        if not algo.Trade.check_tradable(quote_ctx, trade_ctx, trade_env, code):
            algo.Program.logger.info('{} ({}): Not Tradable'.format(time_key[i], i))
            return

        if algo.Program.order_exist(trade_ctx, trade_env, code):
            algo.Program.logger.info('{} ({}): Clear Order'.format(time_key[i], i))
            algo.Trade.clear_order(trade_ctx, trade_env, code)

        if algo.Program.time_to_liquidate(is_time_to_liquidate, code, time_key[i], i):
            algo.Program.force_to_liquidate(quote_ctx, trade_ctx, trade_env, code, time_key[i], i)
        elif algo.Program.get_position(trade_ctx, trade_env, code) != 0:
            if algo.Program.need_to_cut_loss(trade_ctx, trade_env, code, neg_to_liquidate, time_key[i], close[i], prev_close_price) or \
                    algo.Program.need_to_cut_profit(trade_ctx, trade_env, code, pos_to_liquidate, time_key[i]):
                algo.Program.force_to_liquidate(quote_ctx, trade_ctx, trade_env, code, time_key[i], i)
        elif not algo.Program.time_to_stop_trade(is_time_to_stop_trade, code, time_key[i], i):
            if algo.Program.sell_signal_occur(i, time_key, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, prev_close_price, not_dare_to_sell, encourage_factor):
                if short_sell_enable:
                    if True or close[i] < prev_close_price:
                        algo.Program.suggest_sell(quote_ctx, trade_ctx, trade_env, code, short_sell_enable, qty_to_sell, time_key[i])
                    else:
                        algo.Program.logger.info('{} ({}): Not lower than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))
                else:
                    algo.Program.logger.info('{} ({}): Cannot short sell'.format(time_key[i], i))
            elif algo.Program.buy_signal_occur(i, time_key, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, prev_close_price, not_dare_to_buy, encourage_factor):
                if True or close[i] > prev_close_price:
                    algo.Program.suggest_buy(quote_ctx, trade_ctx, trade_env, code, qty_to_buy, time_key[i])
                else:
                    algo.Program.logger.info('{} ({}): Not higher than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))

        algo.Program.update_p_l(trade_ctx, trade_env, code)

    @staticmethod
    def test(quote_ctx, trade_ctx, trade_env, is_time_to_stop_trade, is_time_to_liquidate, code, short_sell_enable, strategy, neg_to_liquidate, pos_to_liquidate, not_dare_to_buy, not_dare_to_sell, encourage_factor, klines, macd_parameter1, macd_parameter2, macd_parameter3, sma_parameter1, sma_parameter2, sma_parameter3):
        algo.Program.logger.info('Test for {}'.format(code))

        # prev_close_price = algo.Quote.get_prev_close_price(quote_ctx, code)
        prev_close_price = klines['last_close'].iloc[0]

        time_key = np.array(klines['time_key'])
        close = np.array(klines['close'])
        change_rate = close - close
        action = close - close
        position = close - close
        p_l = close - close
        cumulated_p_l = close - close
        highest_p_l = close - close
        lowest_p_l = close - close
        realized_p_l = close - close

        sma_1 = talib.SMA(close, sma_parameter1)
        sma_2 = talib.SMA(close, sma_parameter2)
        sma_3 = talib.SMA(close, sma_parameter3)

        macd, signal, hist = talib.MACD(close, macd_parameter1, macd_parameter2, macd_parameter3)

        for i in range(5, len(close)):
            if algo.Program.time_to_liquidate(is_time_to_liquidate, code, time_key[i], i):
                if position[i - 1] > 0:
                    algo.Program.logger.info('{} ({}): Force sell: @{}'.format(time_key[i], i, close[i]))
                    action[i] = -1
                elif position[i - 1] < 0:
                    algo.Program.logger.info('{} ({}): Force buy back: @{}'.format(time_key[i], i, close[i]))
                    action[i] = 1
                else:
                    action[i] = 0
            elif position[i - 1] != 0:
                if (position[i - 1] > 0 and close[i] < prev_close_price and cumulated_p_l[i - 1] * 100 < -(neg_to_liquidate * 0.5)) or \
                        (position[i - 1] < 0 and close[i] > prev_close_price and cumulated_p_l[i - 1] * 100 < -(neg_to_liquidate * 0.5)) or\
                        (cumulated_p_l[i - 1] * 100 < -neg_to_liquidate) or \
                        (highest_p_l[i - 1] * 100 > (pos_to_liquidate * 0.5) and cumulated_p_l[i - 1] * 100 < (pos_to_liquidate * 0.5)) or\
                        (False and cumulated_p_l[i - 1] * 100 < (highest_p_l[i - 1] * 100 * 0.5)) or\
                        (cumulated_p_l[i - 1] * 100 > pos_to_liquidate):
                    if position[i - 1] > 0 and close[i] < prev_close_price and cumulated_p_l[i - 1] * 100 < -(neg_to_liquidate * 0.5):
                        algo.Program.logger.info('{}: Need to cut loss quick after drop below previous close: {} < -{} ({})'.format(time_key[i], (cumulated_p_l[i - 1] * 100), (neg_to_liquidate * 0.5), code))
                    if position[i - 1] < 0 and close[i] > prev_close_price and cumulated_p_l[i - 1] * 100 < -(neg_to_liquidate * 0.5):
                        algo.Program.logger.info('{}: Need to cut loss quick after rise above previous close: {} < -{} ({})'.format(time_key[i], (cumulated_p_l[i - 1] * 100), (neg_to_liquidate * 0.5), code))
                    if cumulated_p_l[i - 1] * 100 < -neg_to_liquidate:
                        algo.Program.logger.info('{}: Need to cut loss: {} < -{} ({})'.format(time_key[i], (cumulated_p_l[i - 1] * 100), neg_to_liquidate, code))
                    if highest_p_l[i - 1] * 100 > (pos_to_liquidate * 0.5) and cumulated_p_l[i - 1] * 100 < (pos_to_liquidate * 0.5):
                        algo.Program.logger.info('{}: Need to retain profit quick after drop from highest profit: {} < {} < {} < {} ({})'.format(time_key[i], (cumulated_p_l[i - 1] * 100), (pos_to_liquidate * 0.5), (pos_to_liquidate * 0.5), (highest_p_l[i - 1] * 100), code))
                    if False and cumulated_p_l[i - 1] * 100 < (highest_p_l[i - 1] * 100 * 0.5):
                        algo.Program.logger.info('{}: Need to retain profit quick after drop from highest profit: {} < {} < {} ({})'.format(time_key[i], (cumulated_p_l[i - 1] * 100), (highest_p_l[i - 1] * 100 * 0.5), (highest_p_l[i - 1] * 100), code))
                    if cumulated_p_l[i - 1] * 100 > pos_to_liquidate:
                        algo.Program.logger.info('{}: Need to cut profit: {} > {} ({})'.format(time_key[i], (cumulated_p_l[i - 1] * 100), pos_to_liquidate, code))
                    if position[i - 1] > 0:
                        algo.Program.logger.info('{} ({}): Force sell: @{}'.format(time_key[i], i, close[i]))
                        action[i] = -1
                    elif position[i - 1] < 0:
                        algo.Program.logger.info('{} ({}): Force buy back: @{}'.format(time_key[i], i, close[i]))
                        action[i] = 1
                    else:
                        action[i] = 0
            elif not algo.Program.time_to_stop_trade(is_time_to_stop_trade, code, time_key[i], i):
                if algo.Program.sell_signal_occur(i, time_key, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, prev_close_price, not_dare_to_sell, encourage_factor):
                    if short_sell_enable:
                        if True or close[i] < prev_close_price:
                            algo.Program.logger.info('{} ({}): Short sell: @{}'.format(time_key[i], i, close[i]))
                            action[i] = -1
                        else:
                            algo.Program.logger.info('{} ({}): Not lower than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))

                            action[i] = 0
                    else:
                        algo.Program.logger.info('{} ({}): Cannot short sell'.format(time_key[i], i))

                        action[i] = 0
                elif algo.Program.buy_signal_occur(i, time_key, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, prev_close_price, not_dare_to_buy, encourage_factor):
                    if True or close[i] > prev_close_price:
                        algo.Program.logger.info('{} ({}): Buy: @{}'.format(time_key[i], i, close[i]))
                        action[i] = 1
                    else:
                        algo.Program.logger.info('{} ({}): Not higher than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))

                        action[i] = 0
                else:
                    action[i] = 0
            else:
                action[i] = 0

            change_rate[i] = (close[i] / close[i - 1]) - 1 if close[i - 1] != 0 else 0
            position[i] = position[i - 1] + action[i]
            p_l[i] = position[i - 1] * change_rate[i]
            cumulated_p_l[i] = cumulated_p_l[i - 1] + p_l[i]

            if cumulated_p_l[i] > highest_p_l[i - 1]:
                highest_p_l[i] = cumulated_p_l[i]
            else:
                highest_p_l[i] = highest_p_l[i - 1]

            if cumulated_p_l[i] < lowest_p_l[i - 1]:
                lowest_p_l[i] = cumulated_p_l[i]
            else:
                lowest_p_l[i] = lowest_p_l[i - 1]

            realized_p_l[i] = realized_p_l[i - 1]

            if position[i] == 0 and cumulated_p_l[i] != 0:
                realized_p_l[i] += cumulated_p_l[i]
                cumulated_p_l[i] = 0
                highest_p_l[i] = 0
                lowest_p_l[i] = 0

        test_result = pd.DataFrame({'code': np.array(klines['code']), 'time_key': time_key,
                                    'close': close, 'change_rate': change_rate, 'macd': macd,
                                    'signal': signal, 'hist': hist, 'sma_1': sma_1,
                                    'sma_2': sma_2, 'sma_3': sma_3, 'action': action, 'position': position, 'p&l': p_l,
                                    'cumulated p&l': cumulated_p_l, 'highest p&l': highest_p_l, 'lowest p&l': lowest_p_l, 'realized p&l': realized_p_l})
        print(test_result.tail(1))
        test_result.to_csv('C:/temp/result/{}_result_{}.csv'.format(code, time.strftime('%Y%m%d%H%M%S')), float_format='%f')

        return test_result

    @staticmethod
    def time_to_liquidate(is_time_to_liquidate, code, time_key, i):
        date_time = datetime.datetime.strptime(time_key, '%Y-%m-%d %H:%M:%S')

        if is_time_to_liquidate:
            algo.Program.logger.info('{} ({}): It is time to liquidate'.format(date_time, i))

            return True

        if 'HK.' in code:
            liquidation_time = datetime.time(16, 0, 0)
        elif 'SH.' in code:
            liquidation_time = datetime.time(14, 45, 0)
        elif 'SZ.' in code:
            liquidation_time = datetime.time(14, 45, 0)
        elif 'US.' in code:
            liquidation_time = datetime.time(15, 30, 0)

        if ('HK.' in code or 'SH.' in code or 'SZ.' in code or 'US.' in code) and date_time.time() >= liquidation_time:
            algo.Program.logger.info('{} ({}): Time to liquidate'.format(date_time, i))

            return True

        return False

    @staticmethod
    def time_to_stop_trade(is_time_to_stop_trade, code, time_key, i):
        date_time = datetime.datetime.strptime(time_key, '%Y-%m-%d %H:%M:%S')

        if is_time_to_stop_trade:
            algo.Program.logger.info('{} ({}): It is time to stop trade'.format(date_time, i))

            return True

        if 'HK.' in code:
            stop_trade_time = datetime.time(16, 0, 0)
        elif 'SH.' in code:
            stop_trade_time = datetime.time(14, 15, 0)
        elif 'SZ.' in code:
            stop_trade_time = datetime.time(14, 15, 0)
        elif 'US.' in code:
            stop_trade_time = datetime.time(15, 0, 0)

        if ('HK.' in code or 'SH.' in code or 'SZ.' in code or 'US.' in code) and date_time.time() >= stop_trade_time:
            algo.Program.logger.info('{} ({}): Time to stop trade'.format(date_time, i))

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
    def get_current_status(trade_ctx, trade_env, code):
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

        algo.Program.logger.info('qty ({}) / pl_ratio ({})'.format(qty, pl_ratio))

        return qty, pl_ratio

    @staticmethod
    def need_to_cut_loss(trade_ctx, trade_env, code, neg_to_liquidate, time_key, last_close, prev_close_price):
        qty, pl_ratio = algo.Program.get_current_status(trade_ctx, trade_env, code)

        if qty > 0 and last_close < prev_close_price and pl_ratio < -(neg_to_liquidate * 0.5):
            algo.Program.logger.info('{}: Need to cut loss quick after drop below previous close: {} < -{} ({})'.format(time_key, pl_ratio, (neg_to_liquidate * 0.5), code))

            return True
        elif qty < 0 and last_close > prev_close_price and pl_ratio < -(neg_to_liquidate * 0.5):
            algo.Program.logger.info('{}: Need to cut loss quick after rise above previous close: {} < -{} ({})'.format(time_key, pl_ratio, (neg_to_liquidate * 0.5), code))

            return True
        elif qty != 0 and pl_ratio < -neg_to_liquidate:
            algo.Program.logger.info('{}: Need to cut loss: {} < -{} ({})'.format(time_key, pl_ratio, neg_to_liquidate, code))

            return True

        return False

    @staticmethod
    def need_to_cut_profit(trade_ctx, trade_env, code, pos_to_liquidate, time_key):
        qty, pl_ratio = algo.Program.get_current_status(trade_ctx, trade_env, code)

        highest_p_l, lowest_p_l = algo.Program.get_p_l(code)

        if qty != 0 and highest_p_l > (pos_to_liquidate * 0.5) and pl_ratio < (pos_to_liquidate * 0.5):
            algo.Program.logger.info('{}: Need to retain profit quick after drop from highest profit: {} < {} < {} < {} ({})'.format(time_key, pl_ratio, (pos_to_liquidate * 0.5), (pos_to_liquidate * 0.5), highest_p_l, code))

            return True
        elif False and qty != 0 and pl_ratio < (highest_p_l * 0.5):
            algo.Program.logger.info('{}: Need to retain profit quick after drop from highest profit: {} < {} < {} ({})'.format(time_key, pl_ratio, (highest_p_l * 0.5), highest_p_l, code))

            return True
        elif qty != 0 and pl_ratio > pos_to_liquidate:
            algo.Program.logger.info('{}: Need to cut profit: {} > {} ({})'.format(time_key, pl_ratio, pos_to_liquidate, code))

            return True

        return False

    @staticmethod
    def update_p_l(trade_ctx, trade_env, code):
        qty, pl_ratio = algo.Program.get_current_status(trade_ctx, trade_env, code)

        try:
            # p_l = pd.read_csv('C:/temp/pl.csv')
            p_l = pd.read_sql('pl', algo.Program.engine)

            prev_highest_p_l = p_l.loc[p_l['code'] == code, 'highest p&l']

            if len(prev_highest_p_l) > 0:
                if pl_ratio > prev_highest_p_l.iloc[0]:
                    new_highest_p_l = pl_ratio
                else:
                    new_highest_p_l = prev_highest_p_l.iloc[0]

                if qty == 0:
                    new_highest_p_l = 0

                p_l.loc[p_l['code'] == code, 'highest p&l'] = new_highest_p_l
            else:
                if pl_ratio > 0:
                    new_highest_p_l = pl_ratio
                else:
                    new_highest_p_l = 0

                if qty == 0:
                    new_highest_p_l = 0

                p_l = p_l.append({
                    'code': code,
                    'highest p&l': new_highest_p_l,
                    'lowest p&l': 0
                }, ignore_index=True)

            prev_lowest_p_l = p_l.loc[p_l['code'] == code, 'lowest p&l']

            if len(prev_lowest_p_l) > 0:
                if pl_ratio < prev_lowest_p_l.iloc[0]:
                    new_lowest_p_l = pl_ratio
                else:
                    new_lowest_p_l = prev_lowest_p_l.iloc[0]

                if qty == 0:
                    new_lowest_p_l = 0

                p_l.loc[p_l['code'] == code, 'lowest p&l'] = new_lowest_p_l
            else:
                if pl_ratio < 0:
                    new_lowest_p_l = pl_ratio
                else:
                    new_lowest_p_l = 0

                if qty == 0:
                    new_lowest_p_l = 0

                p_l = p_l.append({
                    'code': code,
                    'highest p&l': 0,
                    'lowest p&l': new_lowest_p_l
                }, ignore_index=True)

            # p_l.to_csv('C:/temp/pl.csv', float_format='%f', index=False)
            p_l.to_sql('pl', algo.Program.engine, index=False, if_exists='replace')

            # print(p_l)
        except Exception as error:
            algo.Program.logger.info('update_p_l failed ({})'.format(error))

    @staticmethod
    def get_p_l(code):
        try:
            # p_l = pd.read_csv('C:/temp/pl.csv')
            p_l = pd.read_sql('pl', algo.Program.engine)

            prev_highest_p_l = p_l.loc[p_l['code'] == code, 'highest p&l']

            highest_p_l = prev_highest_p_l.iloc[0] if len(prev_highest_p_l) > 0 else 0

            prev_lowest_p_l = p_l.loc[p_l['code'] == code, 'lowest p&l']

            lowest_p_l = prev_lowest_p_l.iloc[0] if len(prev_lowest_p_l) > 0 else 0

            algo.Program.logger.info('{} / {}'.format(highest_p_l, lowest_p_l))
        except Exception as error:
            algo.Program.logger.info('get_p_l failed ({})'.format(error))

        return highest_p_l, lowest_p_l

    @staticmethod
    def buy_signal_occur(i, time_key, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, prev_close_price, not_dare_to_buy, encourage_factor):
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
            elif not algo.Program.dare_to_buy_g(i, time_key, close, prev_close_price, not_dare_to_buy):
                return False
            else:
                return True
        elif strategy == 'H':
            if not algo.Program.dare_to_buy_h(i, time_key, close, prev_close_price, not_dare_to_buy):
                return False
            else:
                return True
        elif strategy == 'I1':
            if not algo.Program.dare_to_buy_i1(i, time_key, close, prev_close_price, not_dare_to_buy):
                return False
            else:
                return True
        elif strategy == 'I2':
            if not algo.Program.dare_to_buy_i2(i, time_key, close, prev_close_price, not_dare_to_buy):
                return False
            else:
                return True
        elif strategy == 'J':
            if not algo.Program.dare_to_buy_j(i, time_key, close, prev_close_price, not_dare_to_buy):
                return False
            else:
                return True
        elif strategy == 'K':
            if not algo.Program.dare_to_buy_k(i, time_key, close, prev_close_price, not_dare_to_buy):
                return False
            else:
                return True
        elif strategy == 'L':
            if not algo.Program.dare_to_buy_l(i, time_key, close, prev_close_price, not_dare_to_buy, encourage_factor):
                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def dare_to_buy_g(i, time_key, close, prev_close_price, not_dare_to_buy):
        algo.Program.logger.info('{} ({}): Buy Signal occur: @{}'.format(time_key[i], i, close[i]))

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage > not_dare_to_buy:
                algo.Program.logger.info('{} ({}): Not dare to buy: @{} ({} > {})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_buy))

                return False

        if close[i] <= prev_close_price:
            algo.Program.logger.info('{} ({}): Not higher than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))

            return False

        return True

    @staticmethod
    def dare_to_buy_h(i, time_key, close, prev_close_price, not_dare_to_buy):
        if close[i] <= close[i - 1] or \
                close[i - 1] < close[i - 2] or \
                close[i - 2] < close[i - 3] or \
                close[i - 3] < close[i - 4] or \
                close[i - 4] < close[i - 5]:
            return False

        algo.Program.logger.info('{} ({}): Buy Signal occur: @{}'.format(time_key[i], i, close[i]))

        return True

    @staticmethod
    def dare_to_buy_i1(i, time_key, close, prev_close_price, not_dare_to_buy):
        algo.Program.logger.info('{} ({}): Buy Signal occur: @{}'.format(time_key[i], i, close[i]))

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage > not_dare_to_buy:
                algo.Program.logger.info('{} ({}): Not dare to buy: @{} ({} > {})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_buy))

                return False

        return True

    @staticmethod
    def dare_to_buy_i2(i, time_key, close, prev_close_price, not_dare_to_buy):
        return False

    @staticmethod
    def dare_to_buy_j(i, time_key, close, prev_close_price, not_dare_to_buy):
        if close[i] <= close[i - 1] or \
                close[i - 1] < close[i - 2] or \
                close[i - 2] < close[i - 3] or \
                close[i - 3] < close[i - 4] or \
                close[i - 4] < close[i - 5]:
            return False

        algo.Program.logger.info('{} ({}): Buy Signal occur: @{}'.format(time_key[i], i, close[i]))

        if False and close[i] >= prev_close_price:
            algo.Program.logger.info('{} ({}): Not lower than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))

            return False

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage < -not_dare_to_buy:
                return True

        algo.Program.logger.info('{} ({}): Not dare to buy: @{} ({} >= -{})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_buy))

        return False

    @staticmethod
    def dare_to_buy_k(i, time_key, close, prev_close_price, not_dare_to_buy):
        if close[i] <= close[i - 1] or \
                close[i - 1] < close[i - 2] or \
                close[i - 2] < close[i - 3] or \
                close[i - 3] < close[i - 4] or \
                close[i - 4] < close[i - 5]:
            return False

        algo.Program.logger.info('{} ({}): Buy Signal occur: @{}'.format(time_key[i], i, close[i]))

        if close[i] <= prev_close_price:
            algo.Program.logger.info('{} ({}): Not higher than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))

            return False

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage > not_dare_to_buy:
                algo.Program.logger.info('{} ({}): Not dare to buy: @{} ({} > {})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_buy))

                return False

        return True

    @staticmethod
    def dare_to_buy_l(i, time_key, close, prev_close_price, not_dare_to_buy, encourage_factor):
        # algo.Program.send_to_topic()

        if close[i] < close[i - 1] or \
                close[i - 1] < close[i - 2] or \
                close[i - 2] <= close[i - 3]:
            return False

        turning_point = i - 3

        while True:
            if close[turning_point] == close[turning_point - 1]:
                turning_point -= 1
            else:
                break

        if close[turning_point] >= close[turning_point - 1] or \
                close[turning_point - 1] > close[turning_point - 2] or \
                close[turning_point - 2] > close[turning_point - 3]:
            return False

        algo.Program.logger.info('{} ({}): Buy Signal occur: @{}'.format(time_key[i], i, close[i]))

        # return True

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage > not_dare_to_buy:
                algo.Program.logger.info('{} ({}): Rise too much, not dare to buy: @{} ({} > {})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_buy))

                return False

        min_change_rate_percentage = 0

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage < -not_dare_to_buy * encourage_factor:
                algo.Program.logger.info('{} ({}): Encourage to buy: @{} ({} < -{})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_buy * encourage_factor))

                return True

            if change_rate_percentage < min_change_rate_percentage:
                min_change_rate_percentage = change_rate_percentage

        algo.Program.logger.info('{} ({}): Drop not too much, not encourage to buy: @{} ({} >= -{})'.format(time_key[i], i, close[i], min_change_rate_percentage, not_dare_to_buy * encourage_factor))

        return False

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
    def sell_signal_occur(i, time_key, close, macd, signal, sma_1, sma_2, short_sell_enable, strategy, prev_close_price, not_dare_to_sell, encourage_factor):
        if not short_sell_enable:
            return False

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
            elif not algo.Program.dare_to_sell_g(i, time_key, close, prev_close_price, not_dare_to_sell):
                return False
            else:
                return True
        elif strategy == 'H':
            if not algo.Program.dare_to_sell_h(i, time_key, close, prev_close_price, not_dare_to_sell):
                return False
            else:
                return True
        elif strategy == 'I1':
            if not algo.Program.dare_to_sell_i1(i, time_key, close, prev_close_price, not_dare_to_sell):
                return False
            else:
                return True
        elif strategy == 'I2':
            if not algo.Program.dare_to_sell_i2(i, time_key, close, prev_close_price, not_dare_to_sell):
                return False
            else:
                return True
        elif strategy == 'J':
            if not algo.Program.dare_to_sell_j(i, time_key, close, prev_close_price, not_dare_to_sell):
                return False
            else:
                return True
        elif strategy == 'K':
            if not algo.Program.dare_to_sell_k(i, time_key, close, prev_close_price, not_dare_to_sell):
                return False
            else:
                return True
        elif strategy == 'L':
            if not algo.Program.dare_to_sell_l(i, time_key, close, prev_close_price, not_dare_to_sell, encourage_factor):
                return False
            else:
                return True
        else:
            return False

    @staticmethod
    def dare_to_sell_g(i, time_key, close, prev_close_price, not_dare_to_sell):
        algo.Program.logger.info('{} ({}): Sell Signal occur: @{}'.format(time_key[i], i, close[i]))

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage < -not_dare_to_sell:
                algo.Program.logger.info('{} ({}): Not dare to sell: @{} ({} < -{})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_sell))

                return False

        if close[i] >= prev_close_price:
            algo.Program.logger.info('{} ({}): Not lower than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))

            return False

        return True

    @staticmethod
    def dare_to_sell_h(i, time_key, close, prev_close_price, not_dare_to_sell):
        if close[i] >= close[i - 1] or \
                close[i - 1] > close[i - 2] or \
                close[i - 2] > close[i - 3] or \
                close[i - 3] > close[i - 4] or \
                close[i - 4] > close[i - 5]:
            return False

        algo.Program.logger.info('{} ({}): Sell Signal occur: @{}'.format(time_key[i], i, close[i]))

        return True

    @staticmethod
    def dare_to_sell_i1(i, time_key, close, prev_close_price, not_dare_to_sell):
        return False

    @staticmethod
    def dare_to_sell_i2(i, time_key, close, prev_close_price, not_dare_to_sell):
        algo.Program.logger.info('{} ({}): Sell Signal occur: @{}'.format(time_key[i], i, close[i]))

        return True

    @staticmethod
    def dare_to_sell_j(i, time_key, close, prev_close_price, not_dare_to_sell):
        if close[i] >= close[i - 1] or \
                close[i - 1] > close[i - 2] or \
                close[i - 2] > close[i - 3] or \
                close[i - 3] > close[i - 4] or \
                close[i - 4] > close[i - 5]:
            return False

        algo.Program.logger.info('{} ({}): Sell Signal occur: @{}'.format(time_key[i], i, close[i]))

        if False and close[i] <= prev_close_price:
            algo.Program.logger.info('{} ({}): Not higher than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))

            return False

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage > not_dare_to_sell:
                return True

        algo.Program.logger.info('{} ({}): Not dare to sell: @{} ({} <= {})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_sell))

        return False

    @staticmethod
    def dare_to_sell_k(i, time_key, close, prev_close_price, not_dare_to_sell):
        if close[i] >= close[i - 1] or \
                close[i - 1] > close[i - 2] or \
                close[i - 2] > close[i - 3] or \
                close[i - 3] > close[i - 4] or \
                close[i - 4] > close[i - 5]:
            return False

        algo.Program.logger.info('{} ({}): Sell Signal occur: @{}'.format(time_key[i], i, close[i]))

        if close[i] >= prev_close_price:
            algo.Program.logger.info('{} ({}): Not lower than last close: @{} ({})'.format(time_key[i], i, close[i], prev_close_price))

            return False

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage < -not_dare_to_sell:
                algo.Program.logger.info('{} ({}): Not dare to sell: @{} ({} < -{})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_sell))

                return False

        return True

    @staticmethod
    def dare_to_sell_l(i, time_key, close, prev_close_price, not_dare_to_sell, encourage_factor):
        if close[i] > close[i - 1] or \
                close[i - 1] > close[i - 2] or \
                close[i - 2] >= close[i - 3]:
            return False

        turning_point = i - 3

        while True:
            if close[turning_point] == close[turning_point - 1]:
                turning_point -= 1
            else:
                break

        if close[turning_point] <= close[turning_point - 1] or \
                close[turning_point - 1] < close[turning_point - 2] or \
                close[turning_point - 2] < close[turning_point - 3]:
            return False

        algo.Program.logger.info('{} ({}): Sell Signal occur: @{}'.format(time_key[i], i, close[i]))

        # return True

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage < -not_dare_to_sell:
                algo.Program.logger.info('{} ({}): Drop too much, not dare to sell: @{} ({} < -{})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_sell))

                return False

        max_change_rate_percentage = 0

        for running in range(i - 1, -1, -1):
            change_rate = (close[i] / close[running]) - 1 if close[running] != 0 else 0
            change_rate_percentage = change_rate * 100

            if change_rate_percentage > not_dare_to_sell * encourage_factor:
                algo.Program.logger.info('{} ({}): Encourage to sell: @{} ({} > {})'.format(time_key[i], i, close[i], change_rate_percentage, not_dare_to_sell * encourage_factor))
                return True

            if change_rate_percentage > max_change_rate_percentage:
                max_change_rate_percentage = change_rate_percentage

        algo.Program.logger.info('{} ({}): Rise not too much, not encourage to sell: @{} ({} <= {})'.format(time_key[i], i, close[i], max_change_rate_percentage, not_dare_to_sell * encourage_factor))

        return False

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
    def suggest_buy(quote_ctx, trade_ctx, trade_env, code, qty_to_buy, time_key):
        try:
            algo.Program.logger.info('{}: Suggest to buy'.format(time_key))

            position = algo.Trade.get_position(trade_ctx, trade_env, code)
            algo.Program.logger.info('{}: Position: {}'.format(time_key, position))

            last_price = algo.Quote.get_last_price(quote_ctx, code)
            algo.Program.logger.info('{}: Last price: {}'.format(time_key, last_price))

            if position < 0:
                buy_qty = 0 - position
                algo.Program.logger.info('{}: Buy Back {}'.format(time_key, buy_qty))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.buy(trade_ctx, trade_env, code, buy_qty, last_price)
            elif qty_to_buy - position > 0:
                buy_qty = qty_to_buy - position
                algo.Program.logger.info('{}: Buy {}'.format(time_key, buy_qty))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.buy(trade_ctx, trade_env, code, buy_qty, last_price)
            else:
                algo.Program.logger.info('{}: Position is full: {} >= {}'.format(time_key, position, qty_to_buy))
        except Exception as error:
            algo.Program.logger.info('suggest_buy failed ({})'.format(error))

    @staticmethod
    def suggest_sell(quote_ctx, trade_ctx, trade_env, code, short_sell_enable, qty_to_sell, time_key):
        try:
            algo.Program.logger.info('{}: Suggest to sell'.format(time_key))

            position = algo.Trade.get_position(trade_ctx, trade_env, code)
            algo.Program.logger.info('{}: Position: {}'.format(time_key, position))

            last_price = algo.Quote.get_last_price(quote_ctx, code)
            algo.Program.logger.info('{}: Last price: {}'.format(time_key, last_price))

            if position > 0:
                algo.Program.logger.info('{}: Sell {}'.format(time_key, position))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.sell(trade_ctx, trade_env, code, position, last_price)
            elif short_sell_enable and qty_to_sell + position > 0:
                sell_qty = qty_to_sell + position
                algo.Program.logger.info('{}: Short Sell {}'.format(time_key, sell_qty))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.sell(trade_ctx, trade_env, code, sell_qty, last_price)
            else:
                algo.Program.logger.info('{}: Position is full: {} <= -{}'.format(time_key, position, qty_to_sell))
        except Exception as error:
            algo.Program.logger.info('suggest_sell failed ({})'.format(error))

    @staticmethod
    def force_to_liquidate(quote_ctx, trade_ctx, trade_env, code, time_key, i):
        try:
            print('Force to liquidate')

            position = algo.Trade.get_position(trade_ctx, trade_env, code)
            print('Position: {}'.format(position))

            last_price = algo.Quote.get_last_price(quote_ctx, code)
            print('Last price: {}'.format(last_price))

            if position > 0:
                algo.Program.logger.info('{} ({}): Force Sell {}'.format(time_key, i, position))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.sell(trade_ctx, trade_env, code, position, last_price)
            elif position < 0:
                algo.Program.logger.info('{} ({}): Force Buy Back {}'.format(time_key, i, position))
                algo.Trade.clear_order(trade_ctx, trade_env, code)
                algo.Trade.buy(trade_ctx, trade_env, code, position, last_price)
            else:
                algo.Program.logger.info('{} ({}): Position is zero'.format(time_key, i))
        except Exception as error:
            algo.Program.logger.info('force_to_liquidate failed ({})'.format(error))

