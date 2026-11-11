"""Illustrative one-wire BOC pricing; Decimal avoids binary floating point."""
from decimal import Decimal as D, ROUND_HALF_UP
ASK, BID = D('6.6886'), D('6.6606')
MID = (ASK+BID)/2

def quote(amount):
    amount = D(amount)
    cny = amount*ASK
    fee = min(D(260),max(D(50),cny*D('.001'))) + D(150)
    # Hypothetical one gross USD wire, with fees paid separately in RMB.
    spread = (cny-amount*MID)/MID
    return tuple(x.quantize(D('.01'), rounding=ROUND_HALF_UP) for x in (cny, spread, fee, fee/MID, spread+fee/MID))
