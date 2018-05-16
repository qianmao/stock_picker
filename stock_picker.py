import os
import random
import requests

from lxml import html

SCRENNER_URL = "http://finviz.com/screener.ashx?v=111&f=cap_smallover,fa_debteq_u0.5,fa_epsqoq_o20,fa_roe_o15,fa_salesqoq_o20,sh_avgvol_o200,sh_instown_o60,sh_price_o5,sh_short_u5&ft=4&o=-sector"
INDUSTRY_URL = "http://finviz.com/groups.ashx?g=industry&v=120&o=name"

DAILY_BREAKOUT_STOCKS_NAME_XPATH = '''//td[@class='screener-body-table-nw'][2]//text()'''
DAILY_BREAKOUT_STOCKS_INDUSTRY_XPATH = '''//td[@class='screener-body-table-nw'][5]//text()'''

INDUSTRY_NAME_XPATH = '''//td[@class='body-table'][2]//text()'''
INDUSTRY_PE_XPATH = '''//td[@class='body-table'][4]//text()'''

STOCK_PRICE_FORMAT = '''https://api.iextrading.com/1.0/stock/%s/price'''
STOCK_QUARTERLY_EPS_FORMAT = '''https://api.iextrading.com/1.0/stock/%s/earnings'''

industry_info = None

# Load user agents
USER_AGENTS_FILE = os.path.join(os.path.dirname(__file__), 'user_agents.txt')
USER_AGENTS = []



def read_uas():
    with open(USER_AGENTS_FILE, 'r') as uaf:
        for ua in uaf.readlines():
            if ua:
                USER_AGENTS.append(ua.strip()[1:-1])
    random.shuffle(USER_AGENTS)

def get_headers():
    ua = random.choice(USER_AGENTS)
    headers = {
        "Connection" : "close",
        "User-Agent" : ua
    }
    return headers


def get_daily_breakout_stocks():
    session_requests = requests.session()
    response = session_requests.get(SCRENNER_URL, headers=get_headers())

    try:
        tree = html.fromstring(response.content)
        daily_breakout_stocks_name = tree.xpath(DAILY_BREAKOUT_STOCKS_NAME_XPATH)
        daily_breakout_stocks_industry = tree.xpath(DAILY_BREAKOUT_STOCKS_INDUSTRY_XPATH)

        return zip(daily_breakout_stocks_name, daily_breakout_stocks_industry)
    except Exception as e:
        print e
        return []

def get_stock_info(stock):
    try:
        price_response = requests.get(STOCK_PRICE_FORMAT % stock).json()
        quarterly_eps_response = requests.get(STOCK_QUARTERLY_EPS_FORMAT % stock).json()

        stock_price = float(price_response)
        quarterly_eps = float(quarterly_eps_response['earnings'][0]['actualEPS'])
        stock_eps = quarterly_eps * 4
        return stock_price, stock_eps
    except Exception as e:
        print e


def get_industry_pe(industry):
    if industry is None:
        return

    global industry_info

    if industry_info is None:
        session_requests = requests.session()
        response = session_requests.get(INDUSTRY_URL, headers=get_headers())

        try:
            tree = html.fromstring(response.content)
            industry_name = tree.xpath(INDUSTRY_NAME_XPATH)
            industry_pe = tree.xpath(INDUSTRY_PE_XPATH)

            industry_name_pe = dict(zip(industry_name, industry_pe))
            industry_info = industry_name_pe
        except Exception as e:
            print e

    return float(industry_info[industry])


if __name__ == '__main__':
    read_uas()

    stocks = get_daily_breakout_stocks()

    for stock_name, industry in stocks:
        try:
            industry_pe = get_industry_pe(industry)
            stock_price, stock_eps = get_stock_info(stock_name)
            fair_price = stock_eps * industry_pe
            price_room = (fair_price - stock_price) / stock_price
            print "Stock: %s\troom: %f\tIndustry: %s\tstock_eps: %f\tPrice: %f\tfair_price: %f" % (stock_name, price_room, industry, stock_eps, stock_price, fair_price)
        except Exception as e:
            print "Error fetching stock: %s due to %s" % (stock_name, e)
