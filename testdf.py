import os

from dotenv import load_dotenv
import pandas as pd
from tabulate import tabulate
import prettytable as pt
import telebot
import time, re, json



def main():
    load_dotenv()
    print('ans')
    SSC_BOT_KEY = os.getenv("SSC_BOT_KEY")
    test_group = os.getenv("TEST_GROUP")
    bot = telebot.TeleBot(SSC_BOT_KEY)
    chat_id = test_group
    report_string = ""
    df = pd.DataFrame(index=[''])
    bot = telebot.TeleBot(SSC_BOT_KEY)
    harvest_indicator = "\U0001F468" + "\u200D" + "\U0001F33E "
    tend_indicator = "\U0001F33E "
    data1 = [
        (harvest_indicator+tend_indicator+"ssc_eth_seth",""),
        ("0xc57A4D3FBEF85e675f6C3656498beEfe6F9DcB55",""),
        ("Last Harvest (h):",       "{:.1f}".format(123)),
        ("Profit on harvest USD",   "{:,.2f}".format(123123)),
        ("Ratio (Desired | Real):", "{:.1f}".format(12)),
        ("Debt delta: $",           "{:,.2f}".format(123)),
        ("Basic APR:",              "{:.1%}".format(1231231)),
    ]
    data2 = [
        ("Last Harvest (h):",       "{:.1f}".format(123)),
        ("Profit on harvest USD",   "{:,.2f}".format(123123)),
        ("Ratio (Desired | Real):", "{:.1f}".format(1231212312311323123132132123)),
        ("Debt delta: $",           "{:,.2f}".format(123)),
        ("Basic APR:",              "{:.1%}".format(1231231)),
    ]
    for name, value in data1:
        df[name] = value
    a = df.T.to_string()
    for name, value in data2:
        df[name] = value
    b = df.T.to_string()
    print(df)
    print(a+"\n\n"+b)
    message = a+"\n\n"+b
    message = f"```\n{message}\n```"
    bot.send_message(chat_id, message, parse_mode="MARKDOWN", disable_web_page_preview = True)

print("Start")
main()

