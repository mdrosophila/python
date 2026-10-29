import numpy as np

from benchmark.services.return_by_year import ASSET_COLUMNS, _load_returns

ASSETS = [c.strip() for c in ASSET_COLUMNS]
BENCHMARK = 'S&P 500 (includes dividends)'


def data_year_range() -> tuple:
    years = _load_returns()['Year'].astype(int)
    return int(years.min()), int(years.max())


def simulate(weights: dict, start_year: int, years: int, initial: float) -> dict:
    """
    Backtest `initial` dollars over `years` calendar years starting in `start_year`, using the
    historical annual returns. The portfolio (`weights`: asset -> fraction summing to 1) is
    rebalanced back to its target weights every year. Each chosen asset is also run on its own
    (100% allocation) for comparison.

    Returns {'labels': [...], 'series': {name: [value at start, value after each year, ...]},
             'summary': [{'name', 'end_value', 'cagr', 'worst_year'}]}.
    """
    df = _load_returns()
    df = df.assign(Year=df['Year'].astype(int)).set_index('Year')
    df.columns = [c.strip() for c in df.columns]
    window = df.loc[start_year:start_year + years - 1]

    def run(w: dict) -> tuple:
        values = [initial]
        yearly = []
        for _, row in window.iterrows():
            r = sum(frac * row[a] for a, frac in w.items())
            yearly.append(r)
            values.append(values[-1] * (1 + r))
        return values, yearly

    runs = {'Portfolio': run(weights)}
    for asset in weights:
        runs[asset] = run({asset: 1.0})

    market = window[BENCHMARK].to_numpy()
    market_var = market.var()

    summary = []
    for name, (values, yearly) in runs.items():
        r = np.array(yearly)
        # Beta against the S&P 500 over the same years (needs at least 2 years of data).
        beta = None
        if len(r) > 1 and market_var > 0:
            beta = round(float(((r - r.mean()) * (market - market.mean())).mean() / market_var), 2)
        summary.append({
            'name': name,
            'end_value': round(values[-1], 2),
            'cagr': round(((values[-1] / initial) ** (1 / years) - 1) * 100, 2),
            'worst_year': round(min(yearly) * 100, 2),
            'sigma': round(float(r.std()) * 100, 2),
            'beta': beta,
        })
    return {
        'labels': [f'Start ({start_year - 1})'] + [str(y) for y in window.index],
        'series': {name: [round(v, 2) for v in values] for name, (values, _) in runs.items()},
        'summary': summary,
    }
