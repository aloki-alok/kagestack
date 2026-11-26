from shop.money import percent_of

RATES = {'US': 0, 'UK': 20}


def tax_for(cents, region):
    return percent_of(cents, RATES[region])
