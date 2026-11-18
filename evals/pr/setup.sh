set -e
git switch -q -c fix-tax-rounding
cat >> tests/test_money.py <<'EOF'


def test_with_tax_rounds_to_cents():
    from invoices.money import with_tax
    assert with_tax(Decimal("10.00"), 0.075) == Decimal("10.75")
EOF
git commit -qam "test: tax on 10.00 at 7.5% should be 10.75"
python3 - <<'EOF'
from pathlib import Path
p = Path('invoices/money.py')
p.write_text(p.read_text().replace(
    '    return amount * (1 + Decimal(str(rate)))',
    '    return (amount * (1 + Decimal(str(rate)))).quantize(Decimal("0.01"))',
))
EOF
git commit -qam "fix: round taxed amounts to cents"
