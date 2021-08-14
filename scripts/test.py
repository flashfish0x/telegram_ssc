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

def main():
    SSC_BOT_KEY = os.getenv("SSC_BOT_KEY")
    sscs = lookup_sscs()

    bot = telebot.TeleBot(SSC_BOT_KEY)

    #@bot.message_handler(commands=['hi'])
    #def greet(message):
    strin = "SSCs:"
    for s in sscs:
        strat = interface.GenericStrategy(s)
        vault = assess_vault_version(strat.vault())
        gov = accounts.at(vault.governance(), force=True)
        params = vault.strategies(strat)
        lastTime = params.dict()["lastReport"]
        since_last =  int(time.time()) - lastTime

        beforeRatio = params.dict()["debtRatio"]
        beforeDebt = params.dict()["totalDebt"]
        beforeGain = params.dict()["totalGain"]
        beforeLoss = params.dict()["totalLoss"]
        
        assets = vault.totalAssets()
        realRatio = beforeDebt/(assets+1)

        if beforeRatio == 0 and realRatio < 0.01:
            continue

        try:
            strat.harvest({'from': gov})

            params = vault.strategies(strat)
            profit = params.dict()["totalGain"] - beforeGain
            loss = params.dict()["totalLoss"] - beforeLoss
            percent = 0
            if beforeDebt > 0:
                if loss > profit:
                    percent = -1 * loss / beforeDebt 
                else:
                    percent = profit / beforeDebt
            over_year = percent * 3.154e+7 / (params.dict()["lastReport"] - lastTime)
            strin = strin + "\n\n[" + strat.name() + "](https://etherscan.io/address/" + s + ") Last Harvest (h): " + "{:.1f}".format((since_last)/60/60) + ' Desired Ratio: ' + "{:.2%}".format(params.dict()["debtRatio"]/10000) + ' Real Ratio: ' + "{:.2%}".format(realRatio) + " - Basic APR: " + "{:.1%}".format(over_year)
        except:
            strin = strin + "\n\n" + strat.name() + " Failed Harvest! " + s + " Last Harvest (h): " + "{:.1f}".format((since_last)/60/60)

    bot.send_message(-1001485969849, strin, parse_mode ="markdown", disable_web_page_preview = True)

def lookup_sscs():
    # Query on naming convention
    query = [
        ["KEY", "name", "STRING"],
        ["VALUE", "ssc", "STRING"],
        ["OPERATOR", "LIKE"]
    ]
    addresses_provider = Contract("0x9be19Ee7Bc4099D62737a7255f5c227fBcd6dB93")
    strategies_helper = Contract(addresses_provider.addressById("HELPER_STRATEGIES"))
    v2_strategies = strategies_helper.assetsStrategiesAddresses()
    filtered_list = list(strategies_helper.assetsStrategiesAddressesByFilter(v2_strategies, query))

    # Query again on old naming convention
    query = [
        ["KEY", "name", "STRING"],
        ["VALUE", "SingleSided", "STRING"],
        ["OPERATOR", "LIKE"]
    ]
    filtered_list_2 = list(strategies_helper.assetsStrategiesAddressesByFilter(v2_strategies, query))
    
    ssc_strats = filtered_list + filtered_list_2 # combine results from two queries
    
    # Here we print out the strategies that were found by the strategy
    print(str(len(ssc_strats))+" strategies found!")
    for s in ssc_strats:
        strat = interface.GenericStrategy(s)
        vault = assess_vault_version(strat.vault())
        print(strat.address, vault.name(), strat.name())
    
    return ssc_strats

def assess_vault_version(vault):
    if int(interface.Vault032(vault).apiVersion().replace(".", "")) > 31:
        return interface.Vault032(vault)
    else:
        return interface.Vault031(vault)