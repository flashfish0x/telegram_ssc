import os
from dotenv import load_dotenv
# import telebot
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
USE_DYNAMIC_LOOKUP = os.getenv("USE_DYNAMIC_LOOKUP")
ENV = os.getenv("ENV")

def main():
    # bot = telebot.TeleBot(SSC_BOT_KEY)
    sscs = lookup_sscs()
    addresses_provider = interface.AddressProvider("0x9be19Ee7Bc4099D62737a7255f5c227fBcd6dB93")
    oracle = interface.Oracle(addresses_provider.addressById("ORACLE"))
    
    strin = "SSCs:"
    for s in sscs:
        strat = interface.GenericStrategy(s)
        vault = assess_vault_version(strat.vault())
        token = interface.IERC20(vault.token())
        token_price = get_price(oracle, token.address)
        usd_tendable = token_price * token.balanceOf(s) / 10**token.decimals()
        gov = accounts.at(vault.governance(), force=True)
        params = vault.strategies(strat)
        lastTime = params.dict()["lastReport"]
        since_last =  int(time.time()) - lastTime

        desiredRatio = params.dict()["debtRatio"]
        beforeDebt = params.dict()["totalDebt"]
        beforeGain = params.dict()["totalGain"]
        beforeLoss = params.dict()["totalLoss"]
        
        assets = vault.totalAssets()
        realRatio = beforeDebt/(assets+1) 

        if desiredRatio == 0 and realRatio < 0.01:
            continue

        try:
            strat.harvest({'from': gov})
            params = vault.strategies(strat)
            profit = params.dict()["totalGain"] - beforeGain
            loss = params.dict()["totalLoss"] - beforeLoss
            debt_delta = params.dict()["totalDebt"] - beforeDebt
            debt_delta_usd = token_price * debt_delta / 10**token.decimals()
            percent = 0
            if beforeDebt > 0:
                if loss > profit:
                    percent = -1 * loss / beforeDebt 
                else:
                    percent = profit / beforeDebt
            over_year = percent * 3.154e+7 / (params.dict()["lastReport"] - lastTime)
            strin = strin + "\n\n[" + strat.name() + "](https://etherscan.io/address/" + s + ") \nLast Harvest (h): " + "{:.1f}".format((since_last)/60/60) + '\nDesired Ratio: ' + "{:.2%}".format(desiredRatio/10000) + ' (delta: $'+ "{:,.2f}".format(debt_delta_usd)+')\nReal Ratio: ' + "{:.2%}".format(realRatio) + "\nBasic APR: " + "{:.1%}".format(over_year) + "\nTendable Amount in USD: $"+ "{:,.2f}".format(usd_tendable)
        except:
            strin = strin + "\n\n" + strat.name() + " Failed Harvest! " + s + " Last Harvest (h): " + "{:.1f}".format((since_last)/60/60)

    # bot.send_message(-1001485969849, strin, parse_mode ="markdown", disable_web_page_preview = True)
    print(strin)

def lookup_sscs():
    if USE_DYNAMIC_LOOKUP == "False":
        f = open("ssc_list.json", "r", errors="ignore")
        data = json.load(f)
        ssc_strats = data['sscs']
    else:
        # Fetch all v2 strategies and query by name
        addresses_provider = Contract("0x9be19Ee7Bc4099D62737a7255f5c227fBcd6dB93")
        strategies_helper = Contract(addresses_provider.addressById("HELPER_STRATEGIES"))
        v2_strategies = strategies_helper.assetsStrategiesAddresses()
        ssc_strats = []
        for s in v2_strategies:
            strat = interface.GenericStrategy(s)
            name = strat.name().lower()
            style1 = re.search("singlesided", name)
            style2 = re.search("ssc", name)
            if style1 or style2:
                ssc_strats.append(s)
                vault = interface.Vault032(strat.vault())
                print(strat.address, vault.name(), strat.name())

    return ssc_strats

def assess_vault_version(vault):
    if int(interface.Vault032(vault).apiVersion().replace(".", "")) > 31:
        return interface.Vault032(vault)
    else:
        return interface.Vault031(vault)

def get_price(oracle, token):
    return oracle.getPriceUsdcRecommended(token) / 10**6