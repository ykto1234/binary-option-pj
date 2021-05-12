import os
import threading
import sys
import time
import traceback
import http.server
import socketserver
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs

import setting_read
import scraip_highlow
import spread_sheet

import datetime
from time import sleep
import random

# ログの定義
import mylogger
logger = mylogger.setup_logger(__name__)
logger.info('プログラム起動開始')

price_dict = {}

currency_map = {
    'USDJPY': 'USD/JPY',
    'EURUSD': 'EUR/USD',
    'EURJPY': 'EUR/JPY',
    'GBPJPY': 'GBP/JPY',
    'AUDJPY': 'AUD/JPY',
    'AUDUSD': 'AUD/USD',
    'NZDJPY': 'NZD/JPY',
    'EURGBP': 'EUR/GBP',
    'EURAUD': 'EUR/AUD',
    'GBPUSD': 'GBP/USD',
    'CHFJPY': 'CHF/JPY',
    'CADJPY': 'CAD/JPY',
    'NZDUSD': 'NZD/USD',
    'USDCHF': 'USD/CHF',
    'AUDNZD': 'AUD/NZD',
    'USDCAD': 'USD/CAD',
    'GBPAUD': 'GBP/AUD',
    'GOLD': 'GOLD',
    'BITCOIN': 'BITCOIN',
}


def request_main(currency, trade_type):

    now = datetime.datetime.now()
    target_time = now.strftime('%Y/%m/%d_%H:%M:%S')
    # scraip_worker(currency, trade_type, target_time, 1)
    # time.sleep(27)
    # scraip_worker(currency, trade_type, target_time, 2)
    # time.sleep(27)
    # scraip_worker(currency, trade_type, target_time, 3)
    # time.sleep(117)
    # scraip_worker(currency, trade_type, target_time, 4)
    # time.sleep(117)
    # scraip_worker(currency, trade_type, target_time, 5)

    logger.debug('初回取得開始')
    t1 = threading.Thread(target=scraip_worker, args=(
        currency, trade_type, target_time, 1))
    t1.setDaemon(True)
    t1.start()

    time.sleep(30)
    logger.debug('30秒後取得開始')
    t2 = threading.Thread(target=scraip_worker, args=(
        currency, trade_type, target_time, 2))
    t2.setDaemon(True)
    t2.start()

    time.sleep(30)
    logger.debug('1分後取得開始')
    t3 = threading.Thread(target=scraip_worker, args=(
        currency, trade_type, target_time, 3))
    t3.setDaemon(True)
    t3.start()

    time.sleep(120)
    logger.debug('3分後取得開始')
    t4 = threading.Thread(target=scraip_worker, args=(
        currency, trade_type, target_time, 4))
    t4.setDaemon(True)
    t4.start()

    time.sleep(120)
    logger.debug('5分後取得開始')
    t5 = threading.Thread(target=scraip_worker, args=(
        currency, trade_type, target_time, 5))
    t5.setDaemon(True)
    t5.start()

    return


def scraip_worker(currency, trade_type, target_time, mode):

    try:
        # INIファイル読み込み
        logger.debug('INIファイル読み込み開始')
        gspread_info_dic = setting_read.read_config('GSPREAD_SHEET')
        AUTH_KEY_PATH = gspread_info_dic['AUTH_KEY_PATH']
        SPREAD_SHEET_KEY = gspread_info_dic['SPREAD_SHEET_KEY']
        OUTPUT_SHEETNAME = gspread_info_dic['OUTPUT_SHEETNAME']
        ORIGIN_SHEETNAME = '一覧'

        # HIGH/LOWデータ取得
        logger.debug('HIGH/LOWデータ取得開始')
        TARGET_URL = 'https://trade.highlow.com/'
        price_text = ''
        price_text = scraip_highlow.check_price(TARGET_URL, currency)
        if not price_text:
            print('現在価格が取得できないため、終了')
            logger.error('現在価格が取得できないため、終了')
            return
        if mode == 1:
            price_dict['start_price'] = float(price_text)
        logger.debug('HIGH/LOWデータ取得完了')

        logger.debug('通貨：' + currency)
        logger.debug('価格：' + price_text)

        logger.debug('スプレッドシートに検索結果書き込み開始')

        ROW_NUM = 2
        DATE_COL = 1
        CURRENCY_COL = 2
        TRADE_TYPE_COL = 3
        PRICE_COL = 4
        S30_PRICE_COL = 5
        S30_WIN_COL = 6
        M1_PRICE_COL = 7
        M1_WIN_COL = 8
        M3_PRICE_COL = 9
        M3_WIN_COL = 10
        M5_PRICE_COL = 11
        M5_WIN_COL = 12

        searchinfo_workbook = None
        searchinfo_workbook = spread_sheet.connect_gspread_workbook(
            AUTH_KEY_PATH, SPREAD_SHEET_KEY)

        # シート名存在チェック
        now = datetime.datetime.now()
        this_month_str = now.strftime('%Y/%m')
        TARGET_SHEET_NAME = OUTPUT_SHEETNAME + "_" + this_month_str
        if not spread_sheet.is_exist_worksheet(searchinfo_workbook, TARGET_SHEET_NAME):
            # シートが存在しない場合、新規作成
            logger.debug('月のワークシートが存在しないため、コピーして作成')
            spread_sheet.copy_worksheet(
                workbook=searchinfo_workbook, src_title=ORIGIN_SHEETNAME, dist_title=TARGET_SHEET_NAME)

        item_list = []
        item_list = spread_sheet.read_gspread_sheet_from_workbook(
            searchinfo_workbook, TARGET_SHEET_NAME)
        item_list = item_list[1:]

        exist_flg = False
        for data_row in item_list:
            if data_row[0] in target_time:
                exist_flg = True
                break

            ROW_NUM += 1
            continue

        output_worskheet = searchinfo_workbook.worksheet(TARGET_SHEET_NAME)

        if not exist_flg:
            # 日付の記入
            spread_sheet.update_gspread_sheet(
                worksheet=output_worskheet, cell_row=ROW_NUM, cell_col=DATE_COL, update_value=target_time)

        if mode == 1:
            # 初回の価格記入
            # 通貨
            spread_sheet.update_gspread_sheet(
                worksheet=output_worskheet, cell_row=ROW_NUM, cell_col=CURRENCY_COL, update_value=currency)
            # 通貨
            if trade_type == 1:
                trade_type_text = 'HIGH'
            else:
                trade_type_text = 'LOW'
            spread_sheet.update_gspread_sheet(
                worksheet=output_worskheet, cell_row=ROW_NUM, cell_col=TRADE_TYPE_COL, update_value=trade_type_text)
            # 価格
            spread_sheet.update_gspread_sheet(
                worksheet=output_worskheet, cell_row=ROW_NUM, cell_col=PRICE_COL, update_value=price_text)

        # 勝敗の判定
        else:
            result_text = ''
            if trade_type == 1:
                # HIGHの場合
                start_price = price_dict['start_price']
                if start_price < float(price_text):
                    result_text = '○'
                else:
                    result_text = '×'
            else:
                # LOWの場合
                start_price = price_dict['start_price']
                if start_price > float(price_text):
                    result_text = '○'
                else:
                    result_text = '×'

            if mode == 2:
                target_price_col = S30_PRICE_COL
                target_result_col = S30_WIN_COL
            elif mode == 3:
                target_price_col = M1_PRICE_COL
                target_result_col = M1_WIN_COL
            elif mode == 4:
                target_price_col = M3_PRICE_COL
                target_result_col = M3_WIN_COL
            elif mode == 5:
                target_price_col = M5_PRICE_COL
                target_result_col = M5_WIN_COL

            # 価格
            spread_sheet.update_gspread_sheet(
                worksheet=output_worskheet, cell_row=ROW_NUM, cell_col=target_price_col, update_value=price_text)

            # 勝敗結果
            spread_sheet.update_gspread_sheet(
                worksheet=output_worskheet, cell_row=ROW_NUM, cell_col=target_result_col, update_value=result_text)

        logger.debug('スプレッドシートに検索結果書き込み完了')

        return

    except Exception as err:
        logger.error("ERROR", err)
        logger.error("ERROR", traceback.format_exc())
    except:
        logger.error("ERROR", traceback.format_exc())


def wait_randam_sec(min_sec, max_sec):
    sec = random.uniform(min_sec, max_sec)
    time.sleep(sec)


class MyHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.make_data()

    def make_data(self):
        # urlパラメータを取得
        parsed = urlparse(self.path)
        # urlパラメータを解析
        params = parse_qs(parsed.query)
        # body部を取得
        content_len = int(self.headers.get("content-length"))
        req_body = self.rfile.read(content_len).decode("utf-8")
        request_json = json.loads(req_body)

        if not 'events' in request_json:
            print('メッセージが取得できないため、終了')
            logger.error('メッセージが取得できないため、終了')
            return

        if len(request_json['events']) == 0 or not 'message' in request_json['events'][0]:
            print('メッセージが取得できないため、終了')
            logger.error('メッセージが取得できないため、終了')
            return

        if not 'text' in request_json['events'][0]['message']:
            print('メッセージが取得できないため、終了')
            logger.error('メッセージが取得できないため、終了')
            return

        # メッセージ取得
        message_text = request_json['events'][0]['message']['text']
        message_text_list = message_text.split('\n')

        logger.debug('メッセージ：' + message_text)

        if not len(message_text_list):
            print('メッセージが取得できないため、終了')
            logger.error('メッセージが取得できないため、終了')
            return

        if not '[シグナル]' in message_text_list[0]:
            print('シグナルではないため、終了')
            logger.info('シグナルではないため、終了')
            return

        if not len(message_text_list) >= 3:
            print('通貨と売買種別が取得できないため、終了')
            logger.error('通貨と売買種別が取得できないため、終了')
            return

        currency_text = message_text_list[1]
        trade_type_text = message_text_list[2]

        if not currency_text in currency_map:
            print('通貨が取得できないため、終了')
            logger.error('通貨が取得できないため、終了')
            return

        currency = currency_map[currency_text]

        if '買い' in trade_type_text:
            trade_type = 1

        elif '売り' in trade_type_text:
            trade_type = 2

        else:
            print('売買種別が取得できないため、終了')
            logger.error('売買種別が取得できないため、終了')
            return

        # レスポンス返却
        self.send_response(200)
        self.end_headers()

        # 処理呼び出し
        tw = threading.Thread(target=request_main, args=(currency, trade_type))
        tw.setDaemon(True)
        tw.start()
        # request_main(currency, trade_type)
        return


server_info_dic = setting_read.read_config('SERVER_INFO')
PORT = int(server_info_dic['PORT'])
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print('サーバを起動しました。ポート:%s' % PORT)
    httpd.serve_forever()


# プログラム実行部分
# if __name__ == "__main__":
#     logger_json("INFO", 'プログラム起動開始')

#     args = sys.argv
#     if len(args) > 1:
#         logger_json("INFO", '引数あり。引数：' + args[1])
#         if args[1] == "-s":
#             # 引数がある場合、サイレントでクローリングを実行
#             logger_json("INFO", 'バックグラウンドで実行開始')
#             handle_request(dict(
#                 message='',
#             ))
#             logger_json("INFO", 'バックグラウンドで実行完了')
#             pass
#         else:
#             logger_json("INFO", '引数が正しくありません。')
#     else:
#         # 引数なしの場合
#         handle_request(dict(
#             message='s',
#             test='aa'
#         ))
