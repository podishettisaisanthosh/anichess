from kraken.spot import Trade


import time

# initialize with your keys
trade = Trade(key="Gm7IGTzoMarDFUoIIxf0hNuJ23JvoexP630wG0TjqmLxAnCRfl5widmL", secret="T20xOWWKQqfmATwy78Na+oxeCf0Mdd2rkiKPgMXcWmFmuK+y8RanYUmRiQkfJwLUkm4P8OlQIUY800qzoWQqAg==")

def place_order(type):
    response = trade.create_order(
        pair="CHECK/USD",
        side=type,
        ordertype="market",
        volume="50"   # amount of BTC to buy
    )







"""
response = trade.create_order(
    ordertype="take-profit",  # or "take-profit-limit"
    side="buy",
    pair="CHECK/USD",
    volume="50",
    price="+1%",    # relative percentage trigger
)

"""

