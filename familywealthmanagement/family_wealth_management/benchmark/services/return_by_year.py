import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
    file_path = '../data/histretSP.xls'
    target_sheet = 'Returns by year'
    target_column = ['Year', 'S&P 500 (includes dividends)', 'US Small cap (bottom decile)', '3-month T.Bill', 'US T. Bond (10-year)', ' Baa Corporate Bond', 'Real Estate', 'Gold*']
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

df = get_return_by_year()

calculate_return_by_year(1, 'S&P 500 (includes dividends)', df)
calculate_return_by_year(1, 'US T. Bond (10-year)', df)
calculate_return_by_year(1, ' Baa Corporate Bond', df)
calculate_return_by_year(1, 'Gold*', df)

calculate_return_by_year(3, 'S&P 500 (includes dividends)', df)
calculate_return_by_year(3, 'US T. Bond (10-year)', df)
calculate_return_by_year(3, ' Baa Corporate Bond', df)
calculate_return_by_year(3, 'Gold*', df)

calculate_return_by_year(5, 'S&P 500 (includes dividends)', df)
calculate_return_by_year(5, 'US T. Bond (10-year)', df)
calculate_return_by_year(5, ' Baa Corporate Bond', df)
calculate_return_by_year(5, 'Gold*', df)

calculate_return_by_year(10, 'S&P 500 (includes dividends)', df)
calculate_return_by_year(10, 'US T. Bond (10-year)', df)
calculate_return_by_year(10, ' Baa Corporate Bond', df)
calculate_return_by_year(10, 'Gold*', df)

calculate_return_by_year(20, 'S&P 500 (includes dividends)', df)
calculate_return_by_year(20, 'US T. Bond (10-year)', df)
calculate_return_by_year(20, ' Baa Corporate Bond', df)
calculate_return_by_year(20, 'Gold*', df)

calculate_return_by_year(30, 'S&P 500 (includes dividends)', df)
calculate_return_by_year(30, 'US T. Bond (10-year)', df)
calculate_return_by_year(30, ' Baa Corporate Bond', df)
calculate_return_by_year(30, 'Gold*', df)

calculate_relationship_sigma('S&P 500 (includes dividends)', df)
calculate_relationship_sigma('US T. Bond (10-year)', df)
calculate_relationship_sigma(' Baa Corporate Bond', df)
calculate_relationship_sigma('Gold*', df)