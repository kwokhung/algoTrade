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
import logging
import logging.config


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
    name = ''
    lot_size = 0
    start = ''
    end = ''
    qty_to_buy = 0
    enable = False
    short_sell_enable = False
    qty_to_sell = 0
    force_to_liquidate = False
    strategy = ''
    neg_to_liquidate = 0
    pos_to_liquidate = 0
    not_dare_to_buy = 0
    not_dare_to_sell = 0
    my_observer = None

    logger = None
    code_list = None

    def __init__(self):
        logging.config.fileConfig('C:/temp/log/logging.config')
        algo.Code.logger = logging.getLogger('algoTrade')
        algo.Code.logger.info('algoTrade init')

        self.get_config()
        self.quote_ctx, self.hk_trade_ctx, self.hkcc_trade_ctx, self.us_trade_ctx = algo.Helper.context_setting(self.api_svr_ip, self.api_svr_port, self.unlock_password)

        self.get_codes()

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

        ret_code, plate_stock = algo.Quote.get_plate_stock(self.quote_ctx, 'HK.HSI Constituent')
        print(plate_stock)
        plate_stock.to_csv('C:/temp/result/plate_stock_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')

        algo.Code.code_list = plate_stock['code']
        print(algo.Code.code_list)
        algo.Code.code_list.to_csv('C:/temp/result/code_list_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f', header=True)

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
        if False and 'code.csv' in event.src_path:
            self.get_codes()

    def get_codes(self):
        self.codes = pd.read_csv('C:/temp/code.csv')
        self.code_length = len(self.codes['code'])
        self.code_index = -1

        self.roll_code()

        print(self.codes)

    def update_codes(self):
        updated_codes = self.codes.copy()

        length = len(updated_codes)

        for index in range(0, length):
            if False and updated_codes.loc[index, 'lot_size'] > 5000:
                updated_codes = updated_codes.drop(index)

        code_enabled = 0

        for index, row in updated_codes.iterrows():
            trade_ctx = algo.Helper.trade_context_setting(self.hk_trade_ctx,
                                                          self.hkcc_trade_ctx,
                                                          self.us_trade_ctx,
                                                          row['code'])
            if algo.Program.get_position(trade_ctx, row['trade_env'], row['code']) == 0 and\
                    not algo.Program.order_exist(trade_ctx, row['trade_env'], row['code']):
                updated_codes.loc[index, 'enable'] = 'no'
            else:
                algo.Code.logger.info('Enable code: {} ({})'.format(row['code'], row['name']))

                updated_codes.loc[index, 'enable'] = 'yes'

                code_enabled = code_enabled + 1

        updated_codes = updated_codes.reset_index(drop=True)

        # code_list = pd.Series(['HK.02800'])
        code_list = pd.Series(['HK.02800', 'HK.02822', 'HK.02823', 'HK.03188'])
        code_list = code_list.append(algo.Code.code_list.sample(n=len(algo.Code.code_list), replace=False), ignore_index=True)
        # print(code_list)

        for code in code_list:
            try:
                ret_code, warrant = algo.Quote.get_warrant(self.quote_ctx, code)
                # warrant[0].to_csv('C:/temp/result/warrant_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')

                favourables = warrant[0].loc[(warrant[0]['status'] == ft.WarrantStatus.NORMAL) &
                                             (warrant[0]['volume'] != 0) &
                                             (warrant[0]['price_change_val'] > 0) &
                                             ((((warrant[0]['type'] == ft.WrtType.CALL) | (warrant[0]['type'] == ft.WrtType.PUT)) & (warrant[0]['effective_leverage'] >= 5)) |
                                              (((warrant[0]['type'] != ft.WrtType.CALL) & (warrant[0]['type'] != ft.WrtType.PUT)) & (warrant[0]['leverage'] >= 5))) &
                                             ((((warrant[0]['type'] == ft.WrtType.CALL) | (warrant[0]['type'] == ft.WrtType.PUT)) & (warrant[0]['effective_leverage'] <= 10)) |
                                              (((warrant[0]['type'] != ft.WrtType.CALL) & (warrant[0]['type'] != ft.WrtType.PUT)) & (warrant[0]['leverage'] <= 10)))]

                if len(favourables) > 0:
                    # favourables.to_csv('C:/temp/result/favourables_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')

                    favourables_max = favourables.loc[favourables['volume'].idxmax()]
                    # favourables_max.to_csv('C:/temp/result/favourables_max_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f', header=False)

                    if updated_codes['code'].str.contains(favourables_max['stock']).any():
                        existed_code = updated_codes.loc[(updated_codes['code'] == favourables_max['stock']) & (updated_codes['enable'] == 'no')]

                        if len(existed_code) > 0:
                            algo.Code.logger.info('Enable code: {} ({})'.format(favourables_max['stock'], favourables_max['name']))

                            updated_codes.loc[updated_codes['code'] == favourables_max['stock'], 'enable'] = 'yes'

                            code_enabled = code_enabled + 1
                    else:
                        algo.Code.logger.info('Add code: {} ({})'.format(favourables_max['stock'], favourables_max['name']))

                        amount_per_lot = favourables_max['cur_price'] * favourables_max['lot_size']
                        lot_for_trade = (5000 // amount_per_lot) + 1
                        leverage = favourables_max['effective_leverage'] if favourables_max['type'] == ft.WrtType.CALL or favourables_max['type'] == ft.WrtType.PUT else favourables_max['leverage']

                        updated_codes = updated_codes.append({
                            'trade_env': ft.TrdEnv.REAL,
                            'code': favourables_max['stock'],
                            'name': favourables_max['name'],
                            'lot_size': favourables_max['lot_size'],
                            'start': 'today',
                            'end': 'today',
                            'qty_to_buy': lot_for_trade * favourables_max['lot_size'],
                            'enable': 'yes',
                            'short_sell_enable': 'no',
                            'qty_to_sell': lot_for_trade * favourables_max['lot_size'],
                            'force_to_liquidate': 'no',
                            'strategy': 'G',
                            'neg_to_liquidate': leverage * 0.8,
                            'pos_to_liquidate': leverage * 0.8,
                            'not_dare_to_buy': leverage,
                            'not_dare_to_sell': leverage,
                        }, ignore_index=True)

                        code_enabled = code_enabled + 1

                time.sleep(3)

                code_limit = 8

                if code_enabled >= code_limit:
                    algo.Code.logger.info('Code enabled reached limits: {} >= {}'.format(code_enabled, code_limit))

                    break
            except TypeError:
                print('get_warrant failed')

        updated_codes.to_csv('C:/temp/code.csv', float_format='%f', index=False)

        print(updated_codes)

        self.get_codes()

    def update_codes_old(self):
        for code in algo.Code.code_list:
            ret_code, warrant = algo.Quote.get_warrant(self.quote_ctx, code)
            # warrant[0].to_csv('C:/temp/result/warrant_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')

            favourables = warrant[0].loc[(warrant[0]['status'] == ft.WarrantStatus.NORMAL) &
                                         (warrant[0]['volume'] != 0) &
                                         (warrant[0]['price_change_val'] > 0) &
                                         ((((warrant[0]['type'] == ft.WrtType.CALL) | (warrant[0]['type'] == ft.WrtType.PUT)) & (warrant[0]['effective_leverage'] >= 5)) |
                                          (((warrant[0]['type'] != ft.WrtType.CALL) & (warrant[0]['type'] != ft.WrtType.PUT)) & (warrant[0]['leverage'] >= 5))) &
                                         ((((warrant[0]['type'] == ft.WrtType.CALL) | (warrant[0]['type'] == ft.WrtType.PUT)) & (warrant[0]['effective_leverage'] <= 10)) |
                                          (((warrant[0]['type'] != ft.WrtType.CALL) & (warrant[0]['type'] != ft.WrtType.PUT)) & (warrant[0]['leverage'] <= 10)))]

            if len(favourables) > 0:
                # favourables.to_csv('C:/temp/result/favourables_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')

                favourables_max = favourables.loc[favourables['volume'].idxmax()]
                # favourables_max.to_csv('C:/temp/result/favourables_max_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f', header=False)

                amount_per_lot = favourables_max['cur_price'] * favourables_max['lot_size']
                lot_for_trade = (5000 // amount_per_lot) + 1
                leverage = favourables_max['effective_leverage'] if favourables_max['type'] == ft.WrtType.CALL or favourables_max['type'] == ft.WrtType.PUT else favourables_max['leverage']

                code_to_add = pd.DataFrame(columns=[
                    'trade_env',
                    'code',
                    'name',
                    'lot_size',
                    'start',
                    'end',
                    'qty_to_buy',
                    'enable',
                    'short_sell_enable',
                    'qty_to_sell',
                    'force_to_liquidate',
                    'strategy',
                    'neg_to_liquidate',
                    'pos_to_liquidate',
                    'not_dare_to_buy',
                    'not_dare_to_sell'
                ])

                code_to_add = code_to_add.append({
                    'trade_env': ft.TrdEnv.SIMULATE,
                    'code': favourables_max['stock'],
                    'name': favourables_max['name'],
                    'lot_size': favourables_max['lot_size'],
                    'start': 'today',
                    'end': 'today',
                    'qty_to_buy': lot_for_trade * favourables_max['lot_size'],
                    'enable': 'yes',
                    'short_sell_enable': 'no',
                    'qty_to_sell': lot_for_trade * favourables_max['lot_size'],
                    'force_to_liquidate': 'no',
                    'strategy': 'G',
                    'neg_to_liquidate': leverage,
                    'pos_to_liquidate': leverage,
                    'not_dare_to_buy': leverage,
                    'not_dare_to_sell': leverage,
                }, ignore_index=True)

                code_to_add.to_csv('C:/temp/code.csv'.format(code, time.strftime("%Y%m%d%H%M%S")), float_format='%f', header=False, index=False, mode='a', line_terminator='')

            time.sleep(3)

        # self.codes = pd.read_csv('C:/temp/code.csv')
        self.code_length = len(self.codes['code'])

        print(self.codes)

    def roll_code(self):
        self.code_index = self.code_index + 1

        if self.code_index == self.code_length:
            self.code_index = 0

        self.trade_env = self.codes['trade_env'][self.code_index]

        self.code = self.codes['code'][self.code_index]
        self.name = self.codes['name'][self.code_index]
        self.lot_size = self.codes['lot_size'][self.code_index]

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

        if self.codes['force_to_liquidate'][self.code_index] == 'yes':
            self.force_to_liquidate = True
        else:
            self.force_to_liquidate = False

        self.strategy = self.codes['strategy'][self.code_index]

        self.neg_to_liquidate = self.codes['neg_to_liquidate'][self.code_index]
        self.pos_to_liquidate = self.codes['pos_to_liquidate'][self.code_index]

        self.not_dare_to_buy = self.codes['not_dare_to_buy'][self.code_index]
        self.not_dare_to_sell = self.codes['not_dare_to_sell'][self.code_index]

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

            if self.code_index == 0:
                self.update_codes()

            if self.enable:
                try:
                    if self.force_to_liquidate:
                        algo.Program.force_to_liquidate(self.quote_ctx, self.trade_ctx, self.trade_env, self.code)
                    else:
                        ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

                        if ret_code == ft.RET_OK:
                            time_key = np.array(klines['time_key'])
                            close = np.array(klines['close'])
                            prev_close_price = klines['last_close'].iloc[0]

                            sma_1 = talib.SMA(close, self.sma_parameters[0])
                            sma_2 = talib.SMA(close, self.sma_parameters[1])
                            sma_3 = talib.SMA(close, self.sma_parameters[2])

                            macd, signal, hist = talib.MACD(close,
                                                            self.macd_parameters[0],
                                                            self.macd_parameters[1],
                                                            self.macd_parameters[2])
                            algo.Program.trade(self.quote_ctx,
                                               self.trade_ctx,
                                               self.trade_env,
                                               self.code,
                                               self.qty_to_buy,
                                               self.short_sell_enable,
                                               self.qty_to_sell,
                                               self.strategy,
                                               self.neg_to_liquidate,
                                               self.pos_to_liquidate,
                                               self.not_dare_to_buy,
                                               self.not_dare_to_sell,
                                               time_key,
                                               close,
                                               prev_close_price,
                                               macd,
                                               signal,
                                               sma_1,
                                               sma_2)
                except TypeError as error:
                    print('get_kline failed ({})'.format(error))

                time.sleep(3)

            self.roll_code()

            code_index = code_index + 1

    def test(self):
        code_index = 0

        # while code_index < self.code_length:
        while True:
            # self.update_codes()

            print('Test: {}'.format(code_index))

            if self.enable:
                try:
                    ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

                    if ret_code == ft.RET_OK:
                        algo.Program.test(self.quote_ctx,
                                          self.trade_ctx,
                                          self.trade_env,
                                          self.code,
                                          self.short_sell_enable,
                                          self.strategy,
                                          self.neg_to_liquidate,
                                          self.pos_to_liquidate,
                                          self.not_dare_to_buy,
                                          self.not_dare_to_sell,
                                          klines,
                                          self.macd_parameters[0],
                                          self.macd_parameters[1],
                                          self.macd_parameters[2],
                                          self.sma_parameters[0],
                                          self.sma_parameters[1],
                                          self.sma_parameters[2])
                except TypeError:
                    print('get_kline failed')

                time.sleep(3)

            self.roll_code()

            code_index = code_index + 1

    def test_year(self):
        start = '2019-05-31'
        # start = 'today'

        if start == 'today':
            start = time.strftime("%Y-%m-%d")

        end = 'today'

        if end == 'today':
            end = time.strftime("%Y-%m-%d")

        trade_days = self.quote_ctx.get_trading_days(ft.Market.HK, start=start, end=end)

        time_column = pd.DataFrame(columns=['time_key'])

        for trade_day in trade_days[1]:
            time_column.loc[len(time_column)] = [trade_day['time']]

        year_result = pd.concat([time_column], axis=1)

        code_index = 0

        while code_index < self.code_length:
            print('Test: {}'.format(code_index))

            if self.enable:
                code_column = pd.DataFrame(columns=['{} ({})'.format(self.code, self.name)])

                for trade_day in trade_days[1]:
                    try:
                        ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, trade_day['time'], trade_day['time'])

                        if ret_code == ft.RET_OK:
                            test_result = algo.Program.test(self.quote_ctx,
                                                            self.trade_ctx,
                                                            self.trade_env,
                                                            self.code,
                                                            self.short_sell_enable,
                                                            self.strategy,
                                                            self.neg_to_liquidate,
                                                            self.pos_to_liquidate,
                                                            self.not_dare_to_buy,
                                                            self.not_dare_to_sell,
                                                            klines,
                                                            self.macd_parameters[0],
                                                            self.macd_parameters[1],
                                                            self.macd_parameters[2],
                                                            self.sma_parameters[0],
                                                            self.sma_parameters[1],
                                                            self.sma_parameters[2])

                            realized_p_l = test_result['realized p&l'].iloc[-1]
                            code_column.loc[len(code_column)] = [realized_p_l]
                    except TypeError:
                        print('get_kline failed')

                    time.sleep(3)

                year_result = pd.concat([year_result, code_column], axis=1)
                print(year_result)

            self.roll_code()

            code_index = code_index + 1

        year_result.to_csv('C:/temp/result/year_result_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')


