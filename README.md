# ActiveCollar

The collar is a popular option strategy that limits the range of positive and negative returns on the underlying security. Resultant equity curve has statistical properties which are attractive for ordinary investors (smoother curve, less extreme return periods, more periods with average return). The collar could be implemented as a passive (call and put options with a fixed distance from the price of underlying are rolled) or active (strike prices for calls and puts are actively managed). We present an active collar strategy which uses momentum, volatility and macroeconomic factors for the management of put/call options with better results than passive collar strategy or simple investment in underlying Nasdaq index ETF.

## Fundamental reason
The collar strategy trades upside participation for downside protection – strategy transforms return distribution of underlying to new distribution with more favourable characteristics to investors. Use of systematic factors (momentum, volatility and macroeconomic situation) enhances strategy’s risk/return profile.

## Simple trading strategy
The complete trading methodology is in a source academic paper on pages 8-16. Simple description:

The investor holds 100% position in a Nasdaq index (via QQQ ETF as an example). Each month investor writes a call option (1-month to expiration). Premiums from call options are used to buy a put options (6-months to expiration). A series of three market signals determines the choice of the initial call and put moneyness, as well as the ratio of the number of calls written to the number of puts and QQQ shares purchased. The three signals are based on momentum, volatility and a compound macroeconomic indicator (unemployment claims and business cycle).

The momentum signal is a simple moving average cross-over of the NASDAQ-100 index. Investor compares a short-term moving average (SMA) and a long-term moving average (LMA) to determine whether an upward or downward trend exists. Three different MA combinations are used – 1/50, 5/150 and 1/200. Investor performs calculation during each option roll – if calculation results in a buy signal, the collar would widen, the collar would be tightened in response to sell signal.

The daily VIX close is used as an indicator of implied volatility levels. On roll dates investor sells 0.75 (1.25) calls per index position when the previous day’s VIX close is more than one standard deviation above (below) its current moving average level. Three different MA combinations are used – 50,150 and 250.

The third indicator is based on the trend of initial unemployment claims and the state of the economy with respect to the business cycle. The announcements from the NBER’s Business Cycle Dating Committee are used to identify the state of the business cycle. Three MA length (10,30,40) are used on weekly data about initial unemployment claims. Rising unemployment claims (over its MA) in an expansionary economy are a bullish signal and investor shifts the collar towards the ATM put and OTM call (increasing both strike prices). In contractionary periods, rising unemployment claims cause the investor to shift the strike prices in the opposite direction.

The momentum, volatility and macroeconomic signals are combined. The target initial percentage moneyness of the options is an integer which falls between ATM and 5% OTM.

## Reference Paper

http://papers.ssrn.com/sol3/papers.cfm?abstract_id=1507991
