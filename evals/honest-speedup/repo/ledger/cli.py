import argparse

from ledger.data import make_data
from ledger.reconcile import reconcile
from ledger.render import render


def main(argv=None):
    parser = argparse.ArgumentParser(prog='ledger')
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--n', type=int, default=2000)
    args = parser.parse_args(argv)
    invoices, txns = make_data(args.seed, args.n)
    print(render(invoices, txns, reconcile(invoices, txns)))


if __name__ == '__main__':
    main()
