from bs4 import BeautifulSoup
import requests

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
import time


def create_driver():
    # chromeドライバーのパス
    chrome_path = "./driver/chromedriver.exe"

    # Selenium用オプション
    op = Options()
    op.add_argument(
        '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Safari/605.1.15')
    # op.add_argument('--user-data-dir=' + userdata_dir)
    # op.add_experimental_option("excludeSwitches", ["enable-automation"])
    # op.add_experimental_option('useAutomationExtension', False)
    # PROXY = '{proxy-server}:{port}'
    # PROXY_AUTH = '{userid}:{password}'
    # op.add_argument('--proxy-server=http://%s' % PROXY)
    # op.add_argument('--proxy-auth=%s' % PROXY_AUTH)

    op.add_argument("--disable-gpu")
    op.add_argument("--disable-extensions")
    op.add_argument("--proxy-server='direct://'")
    op.add_argument("--proxy-bypass-list=*")
    op.add_argument("--start-maximized")
    op.add_argument("--headless")
    #driver = webdriver.Chrome(chrome_options=op)
    driver = webdriver.Chrome(executable_path=chrome_path, chrome_options=op)
    return driver


def check_price(url, currency):
    driver = create_driver()
    driver.get(url)
    # res = requests.get(url)
    # soup = BeautifulSoup(res.text, 'html.parser')

    # レスポンスの HTML から BeautifulSoup オブジェクトを作る
    assets_item_sel = 'div.carousel_item'
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, assets_item_sel))
    )

    price_text = ''
    currency_exist_flg = False

    for i in range(0, 4):
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        item_eles = soup.select(assets_item_sel)
        for item_ele in item_eles:
            # 通貨
            currency_sel = 'div#assetName'
            currency_text = item_ele.select(currency_sel)[0].text
            if currency_text != currency:
                continue
            else:
                currency_exist_flg = True
                break

        if currency_exist_flg:
            break
        else:
            right_button_sel = 'div#rightButton > span'
            right_button_ele = driver.find_element_by_css_selector(
                right_button_sel)
            if right_button_ele:
                driver.execute_script(
                    'arguments[0].click();', right_button_ele)
                time.sleep(2.0)

    if currency_exist_flg:
        price_sel = 'span.strike'
        price_text = item_ele.select(price_sel)[0].text
        # print(currency_text)
        # print(price_text)

    driver.quit()
    return str(price_text)
