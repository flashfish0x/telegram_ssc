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
USE_DYNAMIC_LOOKUP = os.getenv("USE_DYNAMIC_LOOKUP")
ENV = os.getenv("ENV")

def main():
    bot = telebot.TeleBot(SSC_BOT_KEY)
    test_group = os.getenv("TEST_GROUP")
    prod_group = os.getenv("PROD_GROUP")
    sscs = lookup_sscs()
    addresses_provider = interface.AddressProvider("0x9be19Ee7Bc4099D62737a7255f5c227fBcd6dB93")
    oracle = interface.Oracle(addresses_provider.addressById("ORACLE"))
    
    strin = ""
    count = 0
    for s in sscs:
        strat = interface.GenericStrategy(s)
        vault = assess_vault_version(strat.vault())
        token = interface.IERC20(vault.token())
        token_price = get_price(oracle, token.address)
        usd_tendable = token_price * token.balanceOf(s) / 10**token.decimals()
        if usd_tendable > 100:
            tendable_str = "\nTendable Amount in USD: $"+ "{:,.2f}".format(usd_tendable)
        else:
            tendable_str = ""
        gov = accounts.at(vault.governance(), force=True)
        params = vault.strategies(strat)
        lastTime = params.dict()["lastReport"]
        since_last =  int(time.time()) - lastTime
        hours_since_last = since_last/60/60

        desiredRatio = params.dict()["debtRatio"]
        beforeDebt = params.dict()["totalDebt"]
        beforeGain = params.dict()["totalGain"]
        beforeLoss = params.dict()["totalLoss"]
        
        assets = vault.totalAssets()
        realRatio = beforeDebt/(assets+1) 

        if desiredRatio == 0 and realRatio < 0.01:
            continue
        
        count = count + 1
        
        try:
            print("Harvesting strategy: " + s)
            tx = strat.harvest({'from': gov})
        except:
            strin = strin + "\n\n" + strat.name() + "\n\U0001F6A8 Failed Harvest!\n" + s + " Last Harvest (h): " + "{:.1f}".format((since_last)/60/60)
            continue
        
        params = vault.strategies(strat)
        profit = params.dict()["totalGain"] - beforeGain
        profit_usd = token_price * profit / 10**token.decimals()
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

        # Set harvest inidcator
        shouldHarvest = False
        if hours_since_last > 200 or profit_usd > 30_000:
            shouldHarvest = True
        harvestIndicator = ""
        if shouldHarvest:
            harvestIndicator = "\U0001F468" + "\u200D" + "\U0001F33E "
        
        # Generate display string
        strin = strin + "\n\n"+harvestIndicator+"[" + strat.name() + "](https://etherscan.io/address/" + s + ")\n"
        strin = strin + s 
        strin = strin + " \nLast Harvest (h): " + "{:.1f}".format(hours_since_last) 
        strin = strin + "\nProfit on harvest USD: $"+ "{:,.2f}".format(profit_usd) 
        strin = strin + '\nRatio (Desired | Real): ' + "{:.2%}".format(desiredRatio/10000) + ' | ' + "{:.2%}".format(realRatio) 
        strin = strin + '\nDebt delta: $'+ "{:,.2f}".format(debt_delta_usd)
        strin = strin + "\nBasic APR: " + "{:.1%}".format(over_year) 
        strin = strin + tendable_str

    strin = str(count) + " total active strategies found." + strin
    if ENV == "PROD":
        chat_id = prod_group
    else:
        chat_id = test_group

    bot.send_message(chat_id, strin, parse_mode ="markdown", disable_web_page_preview = True)
    #print(strin)

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