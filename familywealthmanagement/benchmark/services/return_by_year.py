from functools import lru_cache
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

ASSET_COLUMNS = ['S&P 500 (includes dividends)', 'US Small cap (bottom decile)', '3-month T.Bill', 'US T. Bond (10-year)', ' Baa Corporate Bond', 'Real Estate', 'Gold*']
PERIODS = [1, 3, 5, 10, 20, 30]
BENCHMARK = 'S&P 500 (includes dividends)'
INFLATION = 'Inflation Rate'
# Number of most recent years in each row of the compound-return table (None = all the data).
COMPOUND_WINDOWS = [None, 50, 10]

#define setup function to calculate return by year
def get_return_by_year() -> pd.DataFrame:
    """
    Calculate the return for a given year from the provided data.

    Parameters:
    data (pd.DataFrame): A DataFrame containing financial data with 'date' and 'return' columns.
    year (int): The year for which to calculate the return.

    Returns:
    float: The calculated return for the specified year.
    """
    #define setup
    file_path = Path(__file__).resolve().parent.parent / 'data' / 'histretSP.xls'
    target_sheet = 'Returns by year'
    target_column = ['Year', 'S&P 500 (includes dividends)', 'US Small cap (bottom decile)', '3-month T.Bill', 'US T. Bond (10-year)', ' Baa Corporate Bond', 'Real Estate', 'Gold*', INFLATION]
    header_row = 19
    nrows = 98

    # Read the data from the excel file
    df = pd.read_excel(file_path,
                     sheet_name=target_sheet,
                     header=header_row, 
                     nrows=nrows, 
                     usecols=target_column)
    
    return df
def calculate_return_by_year(years: int, type: str, df: pd.DataFrame):
    x = df['Year']
    y = df[type] * 100  # Convert to percentage
    newx = []
    newy = []
    for idx in range(len(x) - 1, years - 2, -1):
        newx.append(x[idx])
        return_value = 1
        for idx2 in range(idx, idx - years, -1):
            return_value *= (1 + y[idx2] / 100)
        newy.append((return_value ** (1 / years) - 1) * 100)
    
    plt.bar(newx, newy) 
    plt.title(f'Return by Year for {type} over {years} years')
    plt.xlabel('Year')
    plt.ylabel('Annualized Return')
    plt.show()

def calculate_sigma_over_years(years: int, type: str, df: pd.DataFrame) -> list:
    x = df['Year']
    y = df[type] * 100  # Convert to percentage
    newx = []
    newy = []
    for idx in range(len(x) - 1, years - 2, -1):
        newx.append(x[idx])
        return_value = 1
        for idx2 in range(idx, idx - years, -1):
            return_value *= (1 + y[idx2] / 100)
        newy.append((return_value ** (1 / years) - 1) * 100)
    return [years, np.mean(newy), np.std(newy)]

def calculate_relationship_sigma( type: str, df: pd.DataFrame):
    year = []
    annualized_return = []
    std = []
    for years in range(1, 30):
        result = calculate_sigma_over_years(years, type, df)
        year.append(result[0])
        annualized_return.append(result[1])
        std.append(result[2])
    # Create a 1-row, 2-column subplot grid
    fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(10, 4))
    ax1.scatter(year, std) 
    ax1.set_title(f'{type} market risk')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Market Risk (Standard Deviation)')

    ax2.bar(year, annualized_return)
    ax2.set_title(f'{type} annualized return')
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Annualized Return')

    # Adjust layout to prevent overlap
    fig.tight_layout()

    # Display
    plt.show()

@lru_cache(maxsize=1)
def _load_returns() -> pd.DataFrame:
    return get_return_by_year()


def parse_lookback(raw):
    """Number of most recent years to use, or None (all the data) if blank, invalid or longer than the data."""
    try:
        years = int(raw)
    except (TypeError, ValueError):
        return None
    return None if years < 1 or years >= len(_load_returns()) else years


def asset_returns(real: bool = False, lookback: int = None) -> pd.DataFrame:
    """
    Yearly return of every asset class as a fraction, indexed by year, with stripped column names.
    With `real=True` the returns are adjusted for inflation: (1 + nominal) / (1 + inflation) - 1.
    With `lookback` only that many of the most recent years are kept.
    """
    df = _load_returns()
    frame = df[ASSET_COLUMNS].copy()
    if real:
        frame = (1 + frame).div(1 + df[INFLATION], axis=0) - 1
    frame.index = df['Year'].astype(int)
    frame.columns = [c.strip() for c in ASSET_COLUMNS]
    return frame.iloc[-lookback:] if lookback else frame


def _annualized_frame(years: int, real: bool = False, lookback: int = None) -> pd.DataFrame:
    """Rolling annualized (compound) return per asset in %, indexed by the window's end year."""
    growth = (1 + asset_returns(real, lookback)).rolling(years).apply(np.prod, raw=True)
    return ((growth ** (1 / years) - 1) * 100).iloc[years - 1:]


def get_compound_returns(real: bool = False, lookback: int = None) -> list:
    """
    Compound annual return (%) of each asset over all the data, the last 50 years and the last 10 years:
    [{'label': '1928-2025', 'values': [pct per asset, in ASSET_COLUMNS order]}, ...].
    """
    frame = asset_returns(real, lookback)
    rows = []
    for last_n in COMPOUND_WINDOWS:
        window = frame if last_n is None else frame.iloc[-last_n:]
        compound = (np.exp(np.log1p(window).mean()) - 1) * 100
        rows.append({'label': f'{window.index[0]}-{window.index[-1]}',
                     'values': [round(float(compound[a]), 2) for a in frame.columns]})
    return rows


def get_annualized_returns(years: int, real: bool = False, lookback: int = None) -> dict:
    """
    Rolling annualized return (in %) over `years` for every asset class.

    Returns {'years': [...], 'series': {asset_name: [value or None, ...]}}, where
    each value is the annualized return of the `years` window ending in that year.
    """
    annualized = _annualized_frame(years, real, lookback)
    return {
        'years': annualized.index.tolist(),
        'series': {
            col: [None if pd.isna(v) else round(float(v), 2) for v in annualized[col]]
            for col in annualized.columns
        },
    }


def get_statistics(years: int, assets: list, real: bool = False, lookback: int = None) -> dict:
    """
    Beta, sigma (population std dev, in %) of each asset's rolling annualized returns
    and the correlation matrix between the given assets, over the `years` rolling window.
    Correlations use the years where both assets have data.
    """
    full = _annualized_frame(years, real, lookback)
    annualized = full[assets]
    market = full[BENCHMARK]
    beta = {a: round(float(annualized[a].cov(market, ddof=0) / market.var(ddof=0)), 2) for a in assets}
    sigma = annualized.std(ddof=0)
    corr = annualized.corr()
    return {
        'beta': beta,
        'sigma': {a: round(float(sigma[a]), 2) for a in assets},
        'correlation': [
            {'asset': a, 'values': [round(float(corr.loc[a, b]), 2) for b in assets]}
            for a in assets
        ],
    }


if __name__ == '__main__':
    df = get_return_by_year()
    for years in PERIODS:
        for asset in ['S&P 500 (includes dividends)', 'US T. Bond (10-year)', ' Baa Corporate Bond', 'Gold*']:
            calculate_return_by_year(years, asset, df)
    for asset in ['S&P 500 (includes dividends)', 'US T. Bond (10-year)', ' Baa Corporate Bond', 'Gold*']:
        calculate_relationship_sigma(asset, df)