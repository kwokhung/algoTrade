import algo
import futu as ft


class Trade(object):

    @staticmethod
    def get_positions(trade_ctx, trade_env, code):
        ret_code, position_list = trade_ctx.position_list_query(trd_env=trade_env)

        if ret_code != ft.RET_OK:
            raise Exception('Failed to get positions')

        try:
            positions = position_list.set_index('code').loc[[code]]
        except KeyError:
            positions = None

        return positions

    @staticmethod
    def get_position(trade_ctx, trade_env, code):
        positions = algo.Trade.get_positions(trade_ctx, trade_env, code)

        try:
            position = int(positions['qty'])
        except TypeError:
            position = 0
        except KeyError:
            position = 0

        return position

    @staticmethod
    def buy(trade_ctx, trade_env, code, qty, price):
        """
        ret_code, acc_info = trade_ctx.accinfo_query(trd_env=trade_env)

        if ret_code != ft.RET_OK:
            raise Exception('Failed to get accinfo')

        ret_code, market_snapshot = quote_ctx.get_market_snapshot([code])

        if ret_code != ft.RET_OK:
            raise Exception('Failed to get snapshot')

        lot_size = market_snapshot['lot_size'][0]
        last_price = market_snapshot['last_price'][0]
        power = acc_info['Power'][0]
        qty = int(math.floor(power / last_price))
        qty = qty // lot_size * lot_size
        """
        print('Buy {} {}@{}'.format(code, qty, price))

        ret_code, order = trade_ctx.place_order(
            qty=qty,
            price=price,
            code=code,
            trd_side=ft.TrdSide.BUY,
            order_type=ft.OrderType.NORMAL,
            trd_env=trade_env)

        if ret_code != ft.RET_OK:
            print(order)

        return ret_code, order

    @staticmethod
    def sell(trade_ctx, trade_env, code, qty, price):
        print('Sell {} {}@{}'.format(code, qty, price))

        ret_code, order = trade_ctx.place_order(
            qty=qty,
            price=price,
            code=code,
            trd_side=ft.TrdSide.SELL,
            order_type=ft.OrderType.NORMAL,
            trd_env=trade_env)

        if ret_code != ft.RET_OK:
            print(order)

        return ret_code, order

    @staticmethod
    def clear_order(trade_ctx, trade_env, code):
        ret_code, order_list = trade_ctx.order_list_query(trd_env=trade_env)

        for i, row in order_list.iterrows():
            # print('{}. order_id = {}'.format(i, row['order_id']))
            # print('{}. order_status = {}'.format(i, row['order_status']))
            # print('{}. code = {}'.format(i, row['code']))
            if row['code'] == code and (row['order_status'] == ft.OrderStatus.SUBMITTED or row['order_status'] == ft.OrderStatus.FILLED_PART):
                ret_code, modify_order = trade_ctx.modify_order(
                    modify_order_op=ft.ModifyOrderOp.CANCEL,
                    order_id=row['order_id'],
                    qty=row['qty'],
                    price=row['price'],
                    trd_env=trade_env)

        return ret_code

    @staticmethod
    def check_tradable(quote_ctx, trade_ctx, trade_env, code):
        if trade_env == ft.TrdEnv.REAL:
            return False

        ret_code, global_states = quote_ctx.get_global_state()

        if ret_code != ft.RET_OK:
            return False

        try:
            if 'HK.' in code:
                if global_states['market_hk'] == ft.MarketState.MORNING or global_states['market_hk'] == ft.MarketState.AFTERNOON:
                    return True
            elif 'SH.' in code:
                if global_states['market_sh'] == ft.MarketState.MORNING or global_states['market_sh'] == ft.MarketState.AFTERNOON:
                    return True
            elif 'SZ.' in code:
                if global_states['market_sz'] == ft.MarketState.MORNING or global_states['market_sz'] == ft.MarketState.AFTERNOON:
                    return True
            elif 'US.' in code:
                if global_states['market_us'] == ft.MarketState.MORNING or global_states['market_us'] == ft.MarketState.AFTERNOON:
                    return True
        except KeyError:
            return False

        return False
