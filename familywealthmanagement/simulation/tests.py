from django.test import TestCase

from .services import simulate


class RealSimulationTests(TestCase):
    weights = {'S&P 500 (includes dividends)': 0.6, 'US T. Bond (10-year)': 0.4}

    def test_real_values_are_lower_and_summary_has_both_rates(self):
        nominal = simulate(self.weights, 2000, 20, 10000)
        real = simulate(self.weights, 2000, 20, 10000, real=True)
        n, r = nominal['summary'][0], real['summary'][0]
        self.assertLess(r['end_value'], n['end_value'])
        # Both runs report the same two compound rates; the selected basis only changes the values.
        self.assertEqual((n['cagr_nominal'], n['cagr_real']), (r['cagr_nominal'], r['cagr_real']))
        self.assertLess(n['cagr_real'], n['cagr_nominal'])
        self.assertAlmostEqual((n['end_value'] / 10000) ** (1 / 20) * 100 - 100, n['cagr_nominal'], places=1)

    def test_page_renders_real_basis(self):
        r = self.client.get('/simulation/', {'initial': 10000, 'start': 2000, 'years': 20, 'basis': 'real',
                                             'alloc_0': 60, 'alloc_3': 40})
        self.assertContains(r, 'after inflation')
        self.assertContains(r, 'Annualized return, real')

    def test_lookback_limits_start_year(self):
        params = {'initial': 10000, 'years': 10, 'alloc_0': 100}
        ok = self.client.get('/simulation/', {**params, 'start': 2016, 'lookback': 10})
        self.assertNotContains(ok, 'Historical data covers')
        early = self.client.get('/simulation/', {**params, 'start': 2000, 'lookback': 10})
        self.assertContains(early, 'Historical data covers 2016-2025')
