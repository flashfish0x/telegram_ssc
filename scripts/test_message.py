import os
from dotenv import load_dotenv
import telebot
from brownie import (
    Contract,
    accounts,
    chain,
    rpc,
    web3,
    history,
    interface,
    Wei,
    ZERO_ADDRESS,
)
import time, re, json

load_dotenv()
SSC_BOT_KEY = os.getenv("SSC_BOT_KEY")
test_group = os.getenv("TEST_GROUP")
prod_group = os.getenv("PROD_GROUP")
ENV = os.getenv("ENV")

def main():
    bot = telebot.TeleBot(SSC_BOT_KEY)
    chat_id = test_group
    print("Chat ID:",chat_id)
    strin = "test"
    bot.send_message(chat_id, strin, parse_mode ="MarkdownV2", disable_web_page_preview = True)
