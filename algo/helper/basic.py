import futu as ft
import algo
import datetime
import logging.config
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from sqlalchemy import create_engine


class Helper(object):
    logging.config.fileConfig('C:/temp/log/logging.config')
    logger = logging.getLogger('algoTrade')

    firebase_admin.initialize_app(credentials.Certificate('firebase-adminsdk.json'))

    engine = create_engine('mysql://algotrade:12345678@127.0.0.1:3306/algotrade?charset=utf8')

    @staticmethod
    def log_info(text, to_notify=False, priority=None):
        algo.Helper.logger.info(text)

        if to_notify:
            algo.Helper.send_to_topic('algoTrade', text, priority)

    @staticmethod
    def send_to_topic(topic, message, priority=None):
        if priority is None:
            response = messaging.send(messaging.Message(
                data={
                    'landing_page': 'second',
                    'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': message
                },
                topic=topic
            ))
        else:
            response = messaging.send(messaging.Message(
                data={
                    'landing_page': 'second',
                    'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': message
                },
                topic=topic
            ))
            response = messaging.send(messaging.Message(
                data={
                    'landing_page': 'second',
                    'time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': message
                },
                notification=messaging.Notification(
                    title='Notification',
                    body=message
                ),
                android=messaging.AndroidConfig(
                    priority=priority,
                    restricted_package_name='',
                    notification=messaging.AndroidNotification(
                        icon='fcm_push_icon',
                        sound='default',
                        click_action='FCM_PLUGIN_ACTIVITY'
                    )
                ),
                topic=topic
            ))

        # print('Successfully sent message:', response)

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
