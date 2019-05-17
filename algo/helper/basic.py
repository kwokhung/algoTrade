import futu as ft


class Helper(object):

    @staticmethod
    def context_setting(api_svr_ip, api_svr_port, unlock_password):
        quote_ctx = ft.OpenQuoteContext(host=api_svr_ip, port=api_svr_port)

        hk_trade_ctx = ft.OpenHKTradeContext(host=api_svr_ip, port=api_svr_port)

        ret_code, ret_data = hk_trade_ctx.unlock_trade(unlock_password)

        if ret_code != ft.RET_OK:
            hk_trade_ctx = None

        hkcc_trade_ctx = ft.OpenHKCCTradeContext(host=api_svr_ip, port=api_svr_port)

        ret_code, ret_data = hkcc_trade_ctx.unlock_trade(unlock_password)

        if ret_code != ft.RET_OK:
            hkcc_trade_ctx = None

        us_trade_ctx = ft.OpenUSTradeContext(host=api_svr_ip, port=api_svr_port)

        ret_code, ret_data = us_trade_ctx.unlock_trade(unlock_password)

        if ret_code != ft.RET_OK:
            us_trade_ctx = None

        return quote_ctx, hk_trade_ctx, hkcc_trade_ctx, us_trade_ctx

    @staticmethod
    def trade_context_setting(hk_trade_ctx, hkcc_trade_ctx, us_trade_ctx, code):
        if 'HK.' in code:
            trade_ctx = hk_trade_ctx
        elif 'SH.' in code:
            trade_ctx = hkcc_trade_ctx
        elif 'SZ.' in code:
            trade_ctx = hkcc_trade_ctx
        elif 'US.' in code:
            trade_ctx = us_trade_ctx

        return trade_ctx

    @staticmethod
    def get_market(code):
        if 'HK.' in code:
            market = ft.Market.HK
        elif 'SH.' in code:
            market = ft.Market.SH
        elif 'SZ.' in code:
            market = ft.Market.SZ
        elif 'US.' in code:
            market = ft.Market.US
        else:
            market = ft.Market.NONE

        return market
