import futu as ft


class Helper(object):

    @staticmethod
    def context_setting(api_svr_ip, api_svr_port, trade_env, unlock_password, code):
        quote_ctx = ft.OpenQuoteContext(host=api_svr_ip, port=api_svr_port)

        if 'HK.' in code:
            trade_ctx = ft.OpenHKTradeContext(host=api_svr_ip, port=api_svr_port)
        elif 'SH.' in code:
            trade_ctx = ft.OpenHKCCTradeContext(host=api_svr_ip, port=api_svr_port)
        elif 'SZ.' in code:
            trade_ctx = ft.OpenHKCCTradeContext(host=api_svr_ip, port=api_svr_port)
        elif 'US.' in code:
            if trade_env == ft.TrdEnv.SIMULATE:
                raise Exception('US Stock Trading does not support simulation')

            trade_ctx = ft.OpenUSTradeContext(host=api_svr_ip, port=api_svr_port)

        ret_code, ret_data = trade_ctx.unlock_trade(unlock_password)

        if ret_code != ft.RET_OK:
            raise Exception('Unlock Trading failed')

        return quote_ctx, trade_ctx
