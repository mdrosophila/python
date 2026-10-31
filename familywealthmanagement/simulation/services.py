import numpy as np

from benchmark.services.return_by_year import ASSET_COLUMNS, _load_returns, asset_returns

ASSETS = [c.strip() for c in ASSET_COLUMNS]
BENCHMARK = 'S&P 500 (includes dividends)'
REBALANCED = 'Portfolio (rebalanced yearly)'


def data_year_range(lookback: int = None) -> tuple:
    """First and last year of the data, limited to the most recent `lookback` years if given."""
    years = _load_returns()['Year'].astype(int)
    last = int(years.max())
    return (last - lookback + 1 if lookback else int(years.min())), last


def simulate(weights: dict, start_year: int, years: int, initial: float, real: bool = False) -> dict:
    """
    Backtest `initial` dollars over `years` calendar years starting in `start_year`, using the
    historical annual returns. The portfolio (`weights`: asset -> fraction summing to 1) is rebalanced
    back to its target weights every year. Each chosen asset is also run on its own (100% allocation) for comparison.

    With `real=True` the returns are adjusted for inflation, so values are in start-year dollars.
    The summary always reports the compound annual return both nominal and real.

    Returns {'labels': [...], 'series': {name: [value at start, value after each year, ...]},
             'summary': [{'name', 'end_value', 'cagr', 'cagr_nominal', 'cagr_real', 'worst_year', 'sigma', 'beta'}]}.
    """
    frames = {basis: asset_returns(basis == 'real').loc[start_year:start_year + years - 1]
              for basis in ('nominal', 'real')}
    window = frames['real' if real else 'nominal']

    def run(w: dict, frame) -> tuple:
        values = [initial]
        yearly = []
        for _, row in frame.iterrows():
            r = sum(frac * row[a] for a, frac in w.items())
            yearly.append(r)
            values.append(values[-1] * (1 + r))
        return values, yearly

    def cagr(yearly) -> float:
        return round((float(np.prod(1 + np.array(yearly))) ** (1 / years) - 1) * 100, 2)

    portfolios = {REBALANCED: weights, **{asset: {asset: 1.0} for asset in weights}}
    runs = {name: run(w, window) for name, w in portfolios.items()}
    compound = {name: {basis: cagr(run(w, frame)[1]) for basis, frame in frames.items()}
                for name, w in portfolios.items()}

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
            'cagr_nominal': compound[name]['nominal'],
            'cagr_real': compound[name]['real'],
            'worst_year': round(min(yearly) * 100, 2),
            'sigma': round(float(r.std()) * 100, 2),
            'beta': beta,
        })
    return {
        'labels': [f'Start ({start_year - 1})'] + [str(y) for y in window.index],
        'series': {name: [round(v, 2) for v in values] for name, (values, _) in runs.items()},
        'summary': summary,
    }
