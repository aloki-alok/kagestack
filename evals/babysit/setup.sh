set -e
git switch -q -c free-shipping
cat > shipping.py <<'EOF'
FREE_OVER = 50


def shipping_cost(order_total, weight_kg):
    if order_total > FREE_OVER:
        return 0
    if weight_kg <= 0:
        return 0
    return round(4 + 1.5 * weight_kg, 2)
EOF
cat >> tests/test_shipping.py <<'EOF'

    def test_free_at_exactly_50(self):
        self.assertEqual(shipping_cost(50, 3), 0)

    def test_paid_under_50(self):
        self.assertEqual(shipping_cost(49.99, 2), 7.0)
EOF
git commit -qam "feat(checkout): free shipping on orders of 50 or more"
git push -q ../origin.git free-shipping
git update-ref refs/remotes/origin/free-shipping HEAD
git branch -q --set-upstream-to=origin/free-shipping
