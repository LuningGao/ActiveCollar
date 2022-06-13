# Active Collar Strategy
# 
# The investor holds 100% position in a Nasdaq index (via QQQ ETF as an example). Each month investor writes a call option (1-month to expiration). 
# Premiums from call options are used to buy a put options (6-months to expiration). A series of three market signals determines the choice of the 
# initial call and put moneyness, as well as the ratio of the number of calls written to the number of puts and QQQ shares purchased. The three 
# signals are based on momentum, volatility and a compound macroeconomic indicator (unemployment claims and business cycle). The momentum signal
# is a simple moving average cross-over of the NASDAQ-100 index. Investor compares a short-term moving average (SMA) and a long-term moving average
# (LMA) to determine whether an upward or downward trend exists. Three different MA combinations are used – 1/50, 5/150 and 1/200. Investor performs
# calculation during each option roll – if calculation results in a buy signal, the collar would widen, the collar would be tightened in response 
# to sell signal. The daily VIX close is used as an indicator of implied volatility levels. On roll dates investor sells 0.75 (1.25) calls per index
# position when the previous day’s VIX close is more than one standard deviation above (below) its current moving average level. Three different MA 
# combinations are used – 50,150 and 250. The third indicator is based on the trend of initial unemployment claims and the state of the economy with
# respect to the business cycle. The announcements from the NBER’s Business Cycle Dating Committee are used to identify the state of the business cycle.
# Three MA length (10,30,40) are used on weekly data about initial unemployment claims. Rising unemployment claims (over its MA) in an expansionary 
# economy are a bullish signal and investor shifts the collar towards the ATM put and OTM call (increasing both strike prices). In contractionary 
# periods, rising unemployment claims cause the investor to shift the strike prices in the opposite direction. The momentum, volatility and macroeconomic
# signals are combined. The target initial percentage moneyness of the options is an integer which falls between ATM and 5% OTM.
#
# Implementation changes:
#   - 1 month to expiration put options are traded instead of 6 months.

import numpy as np

class ActiveCollarStrategy(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2015, 1, 1)
        self.SetCash(100000)
        
        # collar settings
        self.targets = np.array([0.95, 1.05])   # initial target
        self.vix_signal = 0
        self.sma_signal_set = False
        self.vix_signal_set = False 
        self.macro_signal_set = False        
        
        option = self.AddOption("QQQ", Resolution.Minute)
        option.SetFilter(-60, +60, timedelta(0), timedelta(35))
        
        # index and sma
        data = self.AddEquity("QQQ", Resolution.Minute)
        data.SetLeverage(10)
        self.symbol = data.Symbol
        
        self.sma_5 = self.SMA(self.symbol, 5, Resolution.Daily)
        self.sma_50 = self.SMA(self.symbol, 50, Resolution.Daily)
        self.sma_150 = self.SMA(self.symbol, 150, Resolution.Daily)
        self.sma_200 = self.SMA(self.symbol, 200, Resolution.Daily)
        
        self.index_smas = [
            (None, self.sma_50),
            (self.sma_5, self.sma_150),
            (None, self.sma_200)
            ]
            
        # vix and SMAs
        self.vix = self.AddData(QuandlVix, "CBOE/VIX", Resolution.Daily).Symbol # Starts in 2004
        self.vix_sma_5 = self.SMA(self.vix, 5, Resolution.Daily)
        self.vix_std_5 = self.STD(self.vix, 5, Resolution.Daily)
        self.vix_sma_150 = self.SMA(self.vix, 150, Resolution.Daily)
        self.vix_std_150 = self.STD(self.vix, 150, Resolution.Daily)
        self.vix_sma_250 = self.SMA(self.vix, 250, Resolution.Daily)
        self.vix_std_250 = self.STD(self.vix, 250, Resolution.Daily)
        
        self.vix_sma_std = [
            (self.vix_sma_5, self.vix_std_5),
            (self.vix_sma_150, self.vix_std_150),
            (self.vix_sma_250, self.vix_std_250)
            ]

        # recession indicator, claims data and SMAs
        self.us_recession = self.AddData(QuandlValue, 'FRED/USREC').Symbol     # monthly data  
        self.initial_claims = self.AddData(QuandlValue, 'FRED/ICSA').Symbol    # weekly data
        self.claims_sma_10 = self.SMA(self.initial_claims, 10, Resolution.Daily)
        self.claims_sma_30 = self.SMA(self.initial_claims, 30, Resolution.Daily)
        self.claims_sma_40 = self.SMA(self.initial_claims, 40, Resolution.Daily)

        self.claims_smas = [
            self.claims_sma_10,
            self.claims_sma_30,
            self.claims_sma_40
            ]        
        
        self.SetWarmUp(250)
        
        # Next expiry date.
        self.expiry_date = None
        self.recession_signal_lagged = RollingWindow[float](2)
        self.recession_signal_lagged.Add(-1)
        
        self.last_day = -1
        
    def OnData(self, slice):
        # Open new trades only on market close.
        if not (self.Time.hour == 15 and self.Time.minute == 59):
            return
        
        # on option roll date
        if self.expiry_date:
            if self.Time.date() < self.expiry_date.date():
                return
            else:
                # update lagged recession signal
                if self.Securities.ContainsKey(self.us_recession):
                    recession_signal = self.Securities[self.us_recession].Price
                    self.recession_signal_lagged.Add(recession_signal)
        
                # SMA signal calculation - widened or tightened collar
                for sma_pair in self.index_smas:
                    if sma_pair[1].IsReady:
                        self.sma_signal_set = True
                        
                        long_sma = sma_pair[1].Current.Value
                        
                        if sma_pair[0] is not None:
                            if sma_pair[0].IsReady:
                                short_sma = sma_pair[0].Current.Value
                                
                                if short_sma > long_sma:
                                    self.targets += np.array([-0.01, 0.01])
                                    # sma_signal += 1
                                else:
                                    self.targets += np.array([+0.01, -0.01])
                                    # sma_signal -= 1
                        else:
                            price = self.Securities[self.symbol].Price
                            if price > long_sma:
                                self.targets += np.array([-0.01, 0.01])
                                # sma_signal += 1
                            else:
                                # sma_signal -= 1
                                self.targets += np.array([+0.01, -0.01])
        
                # VIX signal calculation - quantity
                for sma_std in self.vix_sma_std:
                    if sma_std[0].IsReady and sma_std[1].IsReady:
                        sma = sma_std[0].Current.Value
                        std = sma_std[1].Current.Value
                        current_vix = self.Securities[self.vix].Price
                        self.vix_signal_set = True
                        if current_vix > sma + 1*std:
                            self.vix_signal += 0.75
                        elif current_vix < sma - 1*std:
                            self.vix_signal += 1.25
                        
                # macroeconomic signal - colar shift
                if self.Securities.ContainsKey(self.initial_claims) and self.recession_signal_lagged.IsReady:
                    recession_signal = self.recession_signal_lagged[1]
                    if recession_signal != -1:
                        claims_value = self.Securities[self.initial_claims].Price
                        for claims_sma in self.claims_smas:
                            if claims_sma.IsReady:
                                self.macro_signal_set = True
                                if claims_value > claims_sma.Current.Value:
                                    if recession_signal == 1:
                                        self.targets += np.array([0.01])
                                    else:
                                        self.targets -= np.array([0.01])                
        
        for i in slice.OptionChains:
            chains = i.Value

            if not self.Portfolio.Invested:
                calls = list(filter(lambda x: x.Right == OptionRight.Call, chains))
                puts = list(filter(lambda x: x.Right == OptionRight.Put, chains))
                if not calls or not puts: return
            
                underlying_price = self.Securities[self.symbol].Price

                call_expiries = [i.Expiry for i in calls]
                call_strikes = [i.Strike for i in calls]
                # 1-month to expiration call
                call_expiry = min(call_expiries, key=lambda x: abs((x.date()-self.Time.date()).days-30))

                put_expiries = [i.Expiry for i in puts]
                put_strikes = [i.Strike for i in puts]
                # 6-months to expiration put
                # put_expiry = min(put_expiries, key=lambda x: abs((x.date()-self.Time.date()).days-180))
                put_expiry = min(put_expiries, key=lambda x: abs((x.date()-self.Time.date()).days-30))  # one month expiration is used instead of 6 months

                # determine strikes
                put_strike = min(put_strikes, key = lambda x:abs(x - float(self.targets[0]) * underlying_price))    # changed by macro
                call_strike = min(call_strikes, key = lambda x:abs(x - float(self.targets[1]) * underlying_price))    # changed by macro
                
                put = [i for i in puts if i.Expiry == put_expiry and i.Strike == put_strike]
                call = [i for i in calls if i.Expiry == call_expiry and i.Strike == call_strike]
                
                if call_expiry:
                    self.expiry_date = call_expiry   # store shorter expiry date
                
                if put and call:
                    # All three signals were set to trade.
                    if self.sma_signal_set and self.vix_signal_set and self.macro_signal_set:
                        options_q = int(self.Portfolio.TotalPortfolioValue / (underlying_price * 100))  # changed by vix
                        # self.Securities[call[0].Symbol].MarginModel = BuyingPowerModel(5)
                        # self.Securities[put[0].Symbol].MarginModel = BuyingPowerModel(5)
                        
                        # buy index.
                        self.SetHoldings(self.symbol, 1)
                        
                        # sell call
                        self.Sell(call[0].Symbol, self.vix_signal)
                        
                        # buy put
                        self.Buy(put[0].Symbol, options_q)
                        
                        # monthly signal reset
                        self.vix_signal = 0
                        self.sma_signal_set = False
                        self.vix_signal_set = False 
                        self.macro_signal_set = False
                        self.targets = np.array([0.95, 1.05])
                else:
                    pass
                    # self.Log(self.targets)
                    # self.Log(self.Time.date())
                    # self.Log(put_strike)
                    # self.Log(call_strike)
                        
        invested = [x.Key for x in self.Portfolio if x.Value.Invested]
        if len(invested) == 1:
            self.Liquidate(self.symbol)
        
# Quandl "value" data
class QuandlValue(PythonQuandl):
    def __init__(self):
        self.ValueColumnName = 'value'

class QuandlVix(PythonQuandl):
    def __init__(self):
        self.ValueColumnName = "close"
