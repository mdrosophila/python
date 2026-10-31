from functools import lru_cache
from itertools import combinations

import numpy as np

from simulation.services import ASSETS, _load_returns

STEP = 5  # allocations are searched in 5% steps
CASH = '3-month T.Bill'

# Highest yearly standard deviation (%) of historical returns accepted for each risk tolerance.
SIGMA_CAP = {
    'conservative': 8,
    'moderately_conservative': 10,
    'moderate': 13,
    'moderately_aggressive': 16,
    'aggressive': 100,
}


@lru_cache(maxsize=8)
def _returns(lookback: int = None) -> np.ndarray:
    """Historical annual returns, years x ASSETS, limited to the most recent `lookback` years if given."""
    df = _load_returns()
    df = df.set_index(df['Year'].astype(int))
    df.columns = [c.strip() for c in df.columns]
    return df[ASSETS].to_numpy(dtype=float)[-lookback:] if lookback else df[ASSETS].to_numpy(dtype=float)


@lru_cache(maxsize=1)
def _grid() -> np.ndarray:
    """Every allocation (in STEP% increments) of the assets that adds up to 100%, as fractions."""
    units, n = 100 // STEP, len(ASSETS)
    rows = []
    for bars in combinations(range(units + n - 1), n - 1):  # stars and bars
        edges = (-1, *bars, units + n - 1)
        rows.append([edges[i + 1] - edges[i] - 1 for i in range(n)])
    return np.array(rows, dtype=np.float32) / units


@lru_cache(maxsize=8)
def _candidate_stats(lookback: int = None) -> dict:
    """Historical statistics of every candidate portfolio, rebalanced yearly."""
    weights, returns = _grid(), _returns(lookback)
    cagr, sigma, worst = [], [], []
    for start in range(0, len(weights), 20000):
        yearly = returns.astype(np.float32) @ weights[start:start + 20000].T  # years x candidates
        cagr.append((np.exp(np.log1p(yearly).mean(axis=0)) - 1) * 100)
        sigma.append(yearly.std(axis=0) * 100)
        worst.append(yearly.min(axis=0) * 100)
    return {'weights': weights, 'cagr': np.concatenate(cagr), 'sigma': np.concatenate(sigma),
            'worst': np.concatenate(worst)}


def build_portfolio(ips, lookback: int = None) -> dict:
    """
    Pick the allocation that best fits an investment policy statement, using the historical
    annual returns of the most recent `lookback` years (all the data if None; every candidate is
    rebalanced yearly):
      * the worst historical year must not lose more than the maximum acceptable loss,
      * the yearly sigma must stay within the cap for the risk tolerance,
      * the T-bill (cash) weight must cover the liquidity reserve,
      * then the lowest-risk allocation that reaches the required return is chosen. If none does,
        the highest-return allocation inside the risk limits is chosen and `meets_return` is False.

    Returns {'weights': {asset: pct} or None, 'stats': {...}, 'meets_return': bool, 'limits': {...},
             'success_rate': % of rolling time-horizon windows that reached the required return}.
    """
    stats = _candidate_stats(lookback)
    required = float(ips.required_return_pct)
    max_loss = float(ips.max_acceptable_loss_pct)
    reserve = float(ips.liquidity_reserve_pct) / 100
    sigma_cap = SIGMA_CAP[ips.risk_tolerance]
    limits = {'max_loss': max_loss, 'sigma_cap': sigma_cap, 'cash_floor': round(reserve * 100, 2)}

    cash = stats['weights'][:, ASSETS.index(CASH)]
    ok = ((stats['worst'] >= -max_loss) & (stats['sigma'] <= sigma_cap) & (cash >= reserve - 1e-6))
    if not ok.any():
        return {'weights': None, 'limits': limits, 'meets_return': False, 'stats': None, 'success_rate': None}

    idx = np.flatnonzero(ok)
    reaching = idx[stats['cagr'][idx] >= required]
    if len(reaching):
        best = reaching[np.argmin(stats['sigma'][reaching])]
    else:
        best = idx[np.argmax(stats['cagr'][idx])]

    weights = {a: round(float(w) * 100) for a, w in zip(ASSETS, stats['weights'][best]) if w > 0}
    return {
        'weights': weights,
        'cash': weights.get(CASH, 0),
        'limits': limits,
        'meets_return': bool(stats['cagr'][best] >= required),
        'stats': {k: round(float(stats[k][best]), 2) for k in ('cagr', 'sigma', 'worst')},
        'success_rate': _success_rate(stats['weights'][best], ips.time_horizon_years, required, lookback),
    }


def _success_rate(weights: np.ndarray, horizon: int, required: float, lookback: int = None):
    """
    Share (%) of historical `horizon`-year windows in which the portfolio's annualized return reached `required`;
    None when the look-back is shorter than the horizon, since there is no full window to test.
    """
    yearly = _returns(lookback) @ weights.astype(float)
    if horizon > len(yearly):
        return None
    logs = np.log1p(yearly)
    windows = np.convolve(logs, np.ones(horizon), 'valid') / horizon
    return round(float((np.expm1(windows) * 100 >= required).mean() * 100), 1)
