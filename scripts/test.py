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
import time

load_dotenv()

SSC_BOT_KEY = os.getenv("SSC_BOT_KEY")
sscs = ['0xf840d061E83025F4cD6610AE5DDebCcA43327f9f', # -usdt
    '0x80af28cb1e44C44662F144475d7667C9C0aaB3C3', #- usdc
    '0xb85413f6d07454828eAc7E62df7d847316475178', #- ssc hbtc
    '0x4b254EbBbb8FDb9D3E848501784692b2726b310c', #- ssc bbtc
    '0x29367915508e47c631d220caEbA855901c13a3dE', #- ssc pbtc
    '0x64B2a32f030D9210E51ed8884C0D58b89137Ca81', #- ssc obtc
    '0xa6D1C610B3000F143c18c75D84BaA0eC22681185', #- saave
    '0x74b3E5408B1c29E571BbFCd94B09D516A4d81f36', #- saave
    '0x8784889b0d48a223c3F48312651643Edd8526bbD', #- ssc dai
    '0x8c44Cc5c0f5CD2f7f17B9Aca85d456df25a61Ae8', # ecrv
    '0xCdC3d3A18c9d83Ee6E10E91B48b1fcb5268C97B5'] # steth

bot = telebot.TeleBot(SSC_BOT_KEY)

@bot.message_handler(commands=['hi'])
def greet(message):
  bot.send_message(message.chat.id, "hey!")
  for s in sscs:
      strat = interface.GenericStrategy(s)
      vault = interface.Vault032(strat.vault())
      params = vault.strategies(strat)
      lastTime = params.dict()["lastReport"]
      since_last =  int(time.time()) - lastTime
      strin = str("Strat: " + strat.name() + s + "Last Harvest (h):" + "{:.1f}".format((since_last)/60/60))
      bot.send_message(message.chat.id, strin)


bot.polling()