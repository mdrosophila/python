from django.test import TestCase

from .services.return_by_year import asset_returns, get_annualized_returns, get_compound_returns, get_statistics, _load_returns


class RealReturnTests(TestCase):
    def test_real_return_is_nominal_deflated_by_inflation(self):
        df = _load_returns()
        nominal, real = asset_returns(False), asset_returns(True)
        year = 1930
        inflation = float(df.loc[df['Year'] == year, 'Inflation Rate'].iloc[0])
        expected = (1 + nominal.loc[year, 'S&P 500 (includes dividends)']) / (1 + inflation) - 1
        self.assertAlmostEqual(real.loc[year, 'S&P 500 (includes dividends)'], expected)

    def test_compound_rows_cover_full_50_and_10_years(self):
        for real in (False, True):
            rows = get_compound_returns(real)
            self.assertEqual([r['label'] for r in rows], ['1928-2025', '1976-2025', '2016-2025'])
            self.assertTrue(all(len(r['values']) == 7 for r in rows))
        # Compounding is below the arithmetic mean for a volatile asset, and real is below nominal.
        nominal, real = get_compound_returns(False)[0]['values'], get_compound_returns(True)[0]['values']
        self.assertLess(nominal[0], asset_returns(False)['S&P 500 (includes dividends)'].mean() * 100)
        self.assertTrue(all(r < n for r, n in zip(real, nominal)))

    def test_real_basis_changes_series_and_statistics(self):
        self.assertNotEqual(get_annualized_returns(1, False)['series'], get_annualized_returns(1, True)['series'])
        assets = ['S&P 500 (includes dividends)']
        self.assertEqual(get_statistics(1, assets, True)['beta'][assets[0]], 1.0)

    def test_page_basis_toggle(self):
        r = self.client.get('/benchmark/annualized-return/', {'years': 1, 'basis': 'real'})
        self.assertContains(r, 'Real annualized')
        self.assertContains(r, 'Compound annual return')
        self.assertContains(self.client.get('/benchmark/annualized-return/'), 'Nominal annualized')

    def test_risk_table_has_nominal_and_real_return_columns(self):
        r = self.client.get('/benchmark/annualized-return/', {'years': 1, 'asset': ['S&P 500 (includes dividends)']})
        self.assertContains(r, 'Annualized nominal return (%)')
        self.assertContains(r, 'Annualized real return (%)')
        self.assertContains(r, '<td>10.02</td><td>6.78</td>', html=False)

    def test_lookback_limits_the_data(self):
        from .services.return_by_year import parse_lookback
        self.assertEqual((parse_lookback('20'), parse_lookback(''), parse_lookback('abc'), parse_lookback('500')),
                         (20, None, None, None))
        data = get_annualized_returns(1, False, 20)
        self.assertEqual((data['years'][0], data['years'][-1]), (2006, 2025))
        row = get_compound_returns(False, 20)[0]
        self.assertEqual(row['label'], '2006-2025')
        self.assertNotEqual(row['values'], get_compound_returns(False)[0]['values'])

    def test_page_lookback_and_too_short_error(self):
        r = self.client.get('/benchmark/annualized-return/', {'years': 5, 'lookback': 20, 'asset': ['Gold*']})
        self.assertContains(r, '2006-2025')
        r = self.client.get('/benchmark/annualized-return/', {'years': 10, 'lookback': 5})
        self.assertContains(r, 'must be at least the rolling period')
