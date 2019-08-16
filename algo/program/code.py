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
from sqlalchemy import create_engine


class Code(object):
    config = None
    api_svr_ip = ''
    api_svr_port = 0
    unlock_password = ''
    code_limit = 0
    amt_to_trade = 0
    leverage_ratio_min = 0
    leverage_ratio_max = 0
    dare_factor = 0
    liquidate_factor = 0
    default_trade_env = ''
    default_strategy = ''
    enable_call = False
    enable_put = False
    enable_bull = False
    enable_bear = False
    price_change_val = 0
    is_time_to_stop_trade = False
    is_time_to_liquidate = False
    need_to_update_codes = True
    encourage_factor = 0

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

    engine = create_engine('mysql://algotrade:12345678@127.0.0.1:3306/algotrade?charset=utf8')

    def __init__(self):
        algo.Helper.log_info('algoTrade init', to_notify=True)

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
        # print(plate_stock)
        # plate_stock.to_csv('C:/temp/result/plate_stock_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')
        plate_stock.to_sql('plate_stock', algo.Code.engine, index=True, if_exists='replace')

        algo.Code.code_list = plate_stock['code']
        # print(algo.Code.code_list)
        # algo.Code.code_list.to_csv('C:/temp/result/code_list_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f', header=True)
        algo.Code.code_list.to_sql('code_list', algo.Code.engine, index=True, if_exists='replace')

        algo.Program.init_p_l()

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
        # self.config = pd.read_csv('C:/temp/config.csv')
        self.config = pd.read_sql('config', algo.Code.engine)
        self.api_svr_ip = self.config['api_svr_ip'][0]
        self.api_svr_port = int(self.config['api_svr_port'][0])
        self.unlock_password = self.config['unlock_password'][0]
        self.code_limit = self.config['code_limit'][0]
        self.amt_to_trade = self.config['amt_to_trade'][0]
        self.leverage_ratio_min = self.config['leverage_ratio_min'][0]
        self.leverage_ratio_max = self.config['leverage_ratio_max'][0]
        self.dare_factor = self.config['dare_factor'][0]
        self.liquidate_factor = self.config['liquidate_factor'][0]
        self.default_trade_env = self.config['default_trade_env'][0]
        self.default_strategy = self.config['default_strategy'][0]

        if self.config['enable_call'][0] == 'yes':
            self.enable_call = True
        else:
            self.enable_call = False

        if self.config['enable_put'][0] == 'yes':
            self.enable_put = True
        else:
            self.enable_put = False

        if self.config['enable_bull'][0] == 'yes':
            self.enable_bull = True
        else:
            self.enable_bull = False

        if self.config['enable_bear'][0] == 'yes':
            self.enable_bear = True
        else:
            self.enable_bear = False

        self.price_change_val = self.config['price_change_val'][0]

        if self.config['is_time_to_stop_trade'][0] == 'yes':
            self.is_time_to_stop_trade = True
        else:
            self.is_time_to_stop_trade = False

        if self.config['is_time_to_liquidate'][0] == 'yes':
            self.is_time_to_liquidate = True
        else:
            self.is_time_to_liquidate = False

        if self.config['need_to_update_codes'][0] == 'yes':
            self.need_to_update_codes = True
        else:
            self.need_to_update_codes = False

        self.encourage_factor = self.config['encourage_factor'][0]

        print(self.config)

    def on_modified(self, event):
        if False and 'code.csv' in event.src_path:
            self.get_codes()

    def get_codes(self):
        # self.codes = pd.read_csv('C:/temp/code.csv')
        self.codes = pd.read_sql('codes', algo.Code.engine)
        self.code_length = len(self.codes['code'])
        self.code_index = -1

        self.roll_code()

        print(self.codes)

    @staticmethod
    def refresh_code_list():
        # code_list = pd.Series(['HK.800000'])
        # code_list = pd.Series(['HK.800000', 'HK.02800', 'HK.02822', 'HK.02823', 'HK.03188'])
        # code_list = pd.Series(['HK.800000', 'HK.00700', 'HK.00005', 'HK.02823', 'HK.03188'])
        code_list = pd.Series(['HK.800000', 'HK.800000', 'HK.800000', 'HK.800000', 'HK.800000'])

        # code_list = pd.Series(['HK.800000', 'HK.02800', 'HK.02822', 'HK.02823', 'HK.03188'])
        # code_list = code_list.append(algo.Code.code_list.sample(n=len(algo.Code.code_list), replace=False), ignore_index=True)

        # code_list = pd.Series(['HK.800000', 'HK.02800', 'HK.02822', 'HK.02823', 'HK.03188'])
        # code_list = code_list.append(algo.Code.code_list, ignore_index=True)
        # code_list = code_list.sample(n=len(code_list), replace=False)

        # print(code_list)

        return code_list

    def refresh_existing_codes(self):
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
                # updated_codes.loc[index, 'trade_env'] = self.default_trade_env
                updated_codes.loc[index, 'enable'] = 'no'
                # updated_codes.loc[index, 'force_to_liquidate'] = 'no'
            else:
                algo.Helper.log_info('Monitor code: {} ({})'.format(row['code'], row['name']), to_notify=True)

                # updated_codes.loc[index, 'trade_env'] = self.default_trade_env
                updated_codes.loc[index, 'enable'] = 'yes'
                # updated_codes.loc[index, 'force_to_liquidate'] = 'no'
                code_enabled += 1

        updated_codes = updated_codes[updated_codes['enable'] == 'yes'].reset_index(drop=True)

        return updated_codes, code_enabled

    def get_most_favourable(self, code, updated_codes, within):
        most_favourable = None

        try:
            ret_code, warrant = algo.Quote.get_warrant(self.quote_ctx, code, self.leverage_ratio_min, self.leverage_ratio_max)
            warrants = warrant[0]
            # warrants.to_csv('C:/temp/result/warrant_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')

            favourables = warrants.loc[(((warrants['stock'].isin(updated_codes['code'])) & (within == 'yes')) |
                                        (True & (within is None)) |
                                        (~(warrants['stock'].isin(updated_codes['code'])) & (within == 'no'))) &
                                       (warrants['status'] == ft.WarrantStatus.NORMAL) &
                                       (warrants['volume'] != 0) &
                                       (((warrants['price_change_val'] > 0) & (self.price_change_val > 0)) |
                                        (True & (self.price_change_val == 0)) |
                                        ((warrants['price_change_val'] < 0) & (self.price_change_val < 0))) &
                                       (((warrants['low_price'] != 0) & ((warrants['type'] == ft.WrtType.CALL) | (warrants['type'] == ft.WrtType.PUT)) & ((((warrants['high_price'] / warrants['low_price']) - 1) * 100) >= (abs(warrants['effective_leverage']) * self.encourage_factor))) |
                                        ((warrants['low_price'] != 0) & ((warrants['type'] != ft.WrtType.CALL) & (warrants['type'] != ft.WrtType.PUT)) & ((((warrants['high_price'] / warrants['low_price']) - 1) * 100) >= (warrants['leverage'] * self.encourage_factor)))) &
                                       (((warrants['type'] == ft.WrtType.CALL) & self.enable_call) |
                                        ((warrants['type'] == ft.WrtType.PUT) & self.enable_put) |
                                        ((warrants['type'] == ft.WrtType.BULL) & self.enable_bull) |
                                        ((warrants['type'] == ft.WrtType.BEAR) & self.enable_bear)) &
                                       ((((warrants['type'] == ft.WrtType.CALL) | (warrants['type'] == ft.WrtType.PUT)) & (abs(warrants['effective_leverage']) >= self.leverage_ratio_min)) |
                                        (((warrants['type'] != ft.WrtType.CALL) & (warrants['type'] != ft.WrtType.PUT)) & (warrants['leverage'] >= self.leverage_ratio_min))) &
                                       ((((warrants['type'] == ft.WrtType.CALL) | (warrants['type'] == ft.WrtType.PUT)) & (abs(warrants['effective_leverage']) <= self.leverage_ratio_max)) |
                                        (((warrants['type'] != ft.WrtType.CALL) & (warrants['type'] != ft.WrtType.PUT)) & (warrants['leverage'] <= self.leverage_ratio_max)))]

            if len(favourables) > 0:
                # favourables.to_csv('C:/temp/result/favourables_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')

                most_favourable = favourables.loc[favourables['volume'].idxmax()]
                # most_favourable.to_csv('C:/temp/result/favourables_max_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f', header=False)
        except Exception as error:
            algo.Helper.log_info('get_most_favourable failed ({})'.format(error))
        finally:
            time.sleep(3)

        return most_favourable

    def enable_existing_code(self, updated_codes, most_favourable, code_enabled):
        existed_code_with_position = updated_codes.loc[(updated_codes['code'] == most_favourable['stock']) & (updated_codes['enable'] == 'yes')]
        existed_code_without_position = updated_codes.loc[(updated_codes['code'] == most_favourable['stock']) & (updated_codes['enable'] == 'no')]

        if len(existed_code_with_position) > 0:
            leverage = most_favourable['effective_leverage'] if most_favourable['type'] == ft.WrtType.CALL or most_favourable['type'] == ft.WrtType.PUT else most_favourable['leverage']
            leverage = abs(leverage)

            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'neg_to_liquidate'] = leverage * self.liquidate_factor
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'pos_to_liquidate'] = leverage * self.liquidate_factor
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'not_dare_to_buy'] = leverage * self.dare_factor
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'not_dare_to_sell'] = leverage * self.dare_factor
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'leverage'] = leverage

        if len(existed_code_without_position) > 0:
            algo.Helper.log_info('Enable code: {} ({})'.format(most_favourable['stock'], most_favourable['name']), to_notify=True)

            leverage = most_favourable['effective_leverage'] if most_favourable['type'] == ft.WrtType.CALL or most_favourable['type'] == ft.WrtType.PUT else most_favourable['leverage']
            leverage = abs(leverage)

            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'trade_env'] = self.default_trade_env
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'strategy'] = self.default_strategy
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'enable'] = 'yes'
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'force_to_liquidate'] = 'no'
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'neg_to_liquidate'] = leverage * self.liquidate_factor
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'pos_to_liquidate'] = leverage * self.liquidate_factor
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'not_dare_to_buy'] = leverage * self.dare_factor
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'not_dare_to_sell'] = leverage * self.dare_factor
            updated_codes.loc[updated_codes['code'] == most_favourable['stock'], 'leverage'] = leverage

            code_enabled += 1

        return updated_codes, code_enabled, existed_code_with_position, existed_code_without_position

    def add_new_code(self, updated_codes, most_favourable, code_enabled):
        algo.Helper.log_info('Add code: {} ({})'.format(most_favourable['stock'], most_favourable['name']), to_notify=True)

        amount_per_lot = most_favourable['cur_price'] * most_favourable['lot_size']
        lot_for_trade = (self.amt_to_trade // amount_per_lot) + 1
        leverage = most_favourable['effective_leverage'] if most_favourable['type'] == ft.WrtType.CALL or most_favourable['type'] == ft.WrtType.PUT else most_favourable['leverage']
        leverage = abs(leverage)

        updated_codes = updated_codes.append({
            'trade_env': self.default_trade_env,
            'code': most_favourable['stock'],
            'name': most_favourable['name'],
            'lot_size': most_favourable['lot_size'],
            'start': 'today',
            'end': 'today',
            'qty_to_buy': lot_for_trade * most_favourable['lot_size'],
            'enable': 'yes',
            'short_sell_enable': 'no',
            'qty_to_sell': lot_for_trade * most_favourable['lot_size'],
            'force_to_liquidate': 'no',
            'strategy': self.default_strategy,
            'neg_to_liquidate': leverage * self.liquidate_factor,
            'pos_to_liquidate': leverage * self.liquidate_factor,
            'not_dare_to_buy': leverage * self.dare_factor,
            'not_dare_to_sell': leverage * self.dare_factor,
            'leverage': leverage
        }, ignore_index=True)

        code_enabled += 1

        return updated_codes, code_enabled

    def update_codes(self):
        code_list = algo.Code.refresh_code_list()

        updated_codes, code_enabled = self.refresh_existing_codes()

        for code in code_list:
            if code_enabled >= self.code_limit:
                algo.Helper.log_info('Code enabled reached limits: {} >= {}'.format(code_enabled, self.code_limit))

                break

            ''''''
            most_favourable = self.get_most_favourable(code, updated_codes, 'yes')

            if most_favourable is not None:
                updated_codes, code_enabled, existed_code_with_position, existed_code_without_position = self.enable_existing_code(updated_codes, most_favourable, code_enabled)

                if len(existed_code_without_position) > 0:
                    if code_enabled >= self.code_limit:
                        algo.Helper.log_info('Code enabled reached limits: {} >= {}'.format(code_enabled, self.code_limit))

                        break
            ''''''

            most_favourable = self.get_most_favourable(code, updated_codes, 'no')

            if most_favourable is not None:
                if updated_codes['code'].str.contains(most_favourable['stock']).any():
                    updated_codes, code_enabled, existed_code_with_position, existed_code_without_position = self.enable_existing_code(updated_codes, most_favourable, code_enabled)
                else:
                    updated_codes, code_enabled = self.add_new_code(updated_codes, most_favourable, code_enabled)

        # updated_codes.to_csv('C:/temp/code.csv', float_format='%f', index=False)
        updated_codes.to_sql('codes', algo.Code.engine, index=False, if_exists='replace')

        print(updated_codes)

        self.get_codes()

    def update_us_codes(self):
        a = algo.Quote.get_option_chain(self.quote_ctx, 'US.BABA', '2019-06-28', '2019-06-28', ft.OptionType.ALL, ft.OptionCondType.ALL)
        print(a)
        a[1].to_csv('C:/temp/{}_options.csv'.format('US.BABA'), float_format='%f')
        d = algo.Quote.get_market_snapshot(self.quote_ctx, '', a[1]['code'].tolist())
        print(d)
        options_snapshot = d[1]
        options_snapshot.to_csv('C:/temp/{}_options_snapshot.csv'.format('US.BABA'), float_format='%f')

        b = algo.Quote.get_kline(self.quote_ctx, 'US.BABA190628C165000', '2019-06-21', '2019-06-21')
        print(b)
        # b[1].to_csv('C:/temp/{}_klines.csv'.format('US.BABA'), float_format='%f')

        options_snapshot = pd.DataFrame()
        for index, row in a[1].iterrows():
            try:
                print(row['code'])
                if False and row['strike_time'] != '2019-06-21':
                    continue

                c = algo.Quote.get_market_snapshot(self.quote_ctx, row['code'])
                print(c)

                if len(options_snapshot) == 0:
                    options_snapshot = c[1]
                else:
                    options_snapshot = options_snapshot.append(c[1])

                time.sleep(3)
            except Exception as error:
                algo.Helper.log_info('update_us_codes failed ({})'.format(error))

        options_snapshot.to_csv('C:/temp/{}_options_snapshot.csv'.format('US.BABA'), float_format='%f')

    def roll_code(self):
        self.code_index += 1

        if self.code_index == self.code_length:
            self.code_index = 0

        if self.code_length == 0:
            return

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
            except Exception as error:
                algo.Helper.log_info('animate failed ({})'.format(error))

        self.roll_code()

    def chart(self):
        ani = animation.FuncAnimation(self.fig, self.animate, interval=3000)
        plt.show()

    def trade(self):
        code_index = 0

        while True:
            print('Trade: {}'.format(code_index))

            if self.need_to_update_codes and self.code_index == 0:
                self.update_codes()

            if self.enable:
                try:
                    ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

                    if ret_code == ft.RET_OK:
                        time_key = np.array(klines['time_key'])
                        close = np.array(klines['close'])
                        prev_close_price = klines['last_close'].iloc[0]

                        if self.force_to_liquidate:
                            algo.Program.force_to_liquidate(self.quote_ctx, self.trade_ctx, self.trade_env, self.code, time_key[len(close) - 1], (len(close) - 1))
                        else:
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
                                               self.is_time_to_stop_trade,
                                               self.is_time_to_liquidate,
                                               self.code,
                                               self.qty_to_buy,
                                               self.short_sell_enable,
                                               self.qty_to_sell,
                                               self.strategy,
                                               self.neg_to_liquidate,
                                               self.pos_to_liquidate,
                                               self.not_dare_to_buy,
                                               self.not_dare_to_sell,
                                               self.encourage_factor,
                                               time_key,
                                               close,
                                               prev_close_price,
                                               macd,
                                               signal,
                                               sma_1,
                                               sma_2)
                except Exception as error:
                    algo.Helper.log_info('trade failed ({})'.format(error))

                time.sleep(3)

            self.roll_code()

            code_index += 1

    def test(self):
        code_index = 0

        # while code_index < self.code_length:
        while True:
            # self.update_codes()
            # self.update_us_codes()

            print('Test: {}'.format(code_index))

            if self.enable:
                try:
                    ret_code, klines = algo.Quote.get_kline(self.quote_ctx, self.code, self.start, self.end)

                    if ret_code == ft.RET_OK:
                        algo.Program.test(self.quote_ctx,
                                          self.trade_ctx,
                                          self.trade_env,
                                          self.is_time_to_stop_trade,
                                          self.is_time_to_liquidate,
                                          self.code,
                                          self.short_sell_enable,
                                          self.strategy,
                                          self.neg_to_liquidate,
                                          self.pos_to_liquidate,
                                          self.not_dare_to_buy,
                                          self.not_dare_to_sell,
                                          self.encourage_factor,
                                          klines,
                                          self.macd_parameters[0],
                                          self.macd_parameters[1],
                                          self.macd_parameters[2],
                                          self.sma_parameters[0],
                                          self.sma_parameters[1],
                                          self.sma_parameters[2])
                except Exception as error:
                    algo.Helper.log_info('test failed ({})'.format(error))

                time.sleep(3)

            self.roll_code()

            code_index += 1

    def test_year(self):
        # algo.Code.update_us_codes(self)

        # start = '2019-06-01'
        start = 'today'

        if start == 'today':
            start = time.strftime("%Y-%m-%d")

        # end = '2019-07-02'
        end = 'today'

        if end == 'today':
            end = time.strftime("%Y-%m-%d")

        trade_days = self.quote_ctx.get_trading_days(ft.Market.HK, start=start, end=end)

        time_column = pd.DataFrame(columns=['time_key'])

        for trade_day in trade_days[1]:
            time_column.loc[len(time_column)] = [trade_day['time']]

        year_result = pd.concat([time_column], axis=1)

        for code_index in range(0, self.code_length):
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
                                                            self.is_time_to_stop_trade,
                                                            self.is_time_to_liquidate,
                                                            self.code,
                                                            self.short_sell_enable,
                                                            self.strategy,
                                                            self.neg_to_liquidate,
                                                            self.pos_to_liquidate,
                                                            self.not_dare_to_buy,
                                                            self.not_dare_to_sell,
                                                            self.encourage_factor,
                                                            klines,
                                                            self.macd_parameters[0],
                                                            self.macd_parameters[1],
                                                            self.macd_parameters[2],
                                                            self.sma_parameters[0],
                                                            self.sma_parameters[1],
                                                            self.sma_parameters[2])

                            realized_p_l = test_result['realized p&l'].iloc[-1]
                            code_column.loc[len(code_column)] = [realized_p_l]
                    except Exception as error:
                        algo.Helper.log_info('test_year failed ({})'.format(error))

                    time.sleep(3)

                year_result = pd.concat([year_result, code_column], axis=1)
                print(year_result)

            self.roll_code()

        year_result.to_csv('C:/temp/result/year_result_{}.csv'.format(time.strftime("%Y%m%d%H%M%S")), float_format='%f')
