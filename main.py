

import numpy as np
import pandas as pd
import requests
import xlsxwriter
import math
from secrets import IEX_CLOUD_API_TOKEN
from tabulate import tabulate


def get_stock_data(symbol):
    sandbox_api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote/?token={IEX_CLOUD_API_TOKEN}'
    # print(sandbox_api_url)
    data = requests.get(sandbox_api_url).json()
    return data


# breaking batch to lists of 100 (or less) stock symbols
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def main():
    stocks = pd.read_csv('sp_500_stocks.csv')
    my_columns = ['Ticker', 'Stock Price', 'Market Capitalization', 'Number of Shares to Buy']

    # preparing batches
    stock_groups = list(chunks(stocks['Ticker'], 100))
    stock_strings = []
    for i in range(0, len(stock_groups)):
        stock_strings.append(','.join(stock_groups[i]))

    final_dataframe = pd.DataFrame(columns=my_columns)

    # batches and dataframe loop
    for stock_string in stock_strings:
        batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?' \
                             f'symbols={stock_string}&types=quote&token={IEX_CLOUD_API_TOKEN}'
        data = requests.get(batch_api_call_url).json()
        for stock in stock_string.split(','):
            final_dataframe = final_dataframe.append(
                pd.Series([
                    stock,
                    data[stock]['quote']['latestPrice'],
                    data[stock]['quote']['marketCap'],
                    'N/A'
                ], index=my_columns),
                ignore_index=True
            )

    # getting the number of shares per security with regard to portfolio size input
    portfolio_size = input('Enter the value of your portfolio:')
    try:
        val = float(portfolio_size)
        print(val)
    except ValueError:
        print("That's not a number! \nPlease try again:")
        portfolio_size = input('Enter the value of your portfolio:')
        val = float(portfolio_size)

    for i in range(0, len(final_dataframe.index)):
        final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(val/final_dataframe.loc[i, 'Stock Price'])

    # display dataframe with final calculations
    print(tabulate(final_dataframe, headers=my_columns))

    """Setting up the XLSX Writer for data export"""

    writer = pd.ExcelWriter('recommended_trades.xlsx', engine='xlsxwriter')
    final_dataframe.to_excel(writer, 'Recommended Trades', index=False)

    """Formatting Export File"""
    background_color = '#0a0a23'
    font_color = '#ffffff'

    string_format = writer.book.add_format(
        {
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

    dollar_format = writer.book.add_format(
        {
            'num_format': '$0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

    integer_format = writer.book.add_format(
        {
            'num_format': '0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

    """This is ugly.... can be a loop instead"""
    """
    writer.sheets['Recommended Trades'].set_column('A:A', 18, string_format)
    writer.sheets['Recommended Trades'].set_column('B:B', 18, string_format)
    writer.sheets['Recommended Trades'].set_column('C:C', 18, string_format)
    writer.sheets['Recommended Trades'].set_column('D:D', 18, string_format)
    """

    column_formats = {
        'A': ['Ticker', string_format],
        'B': ['Stock Price', dollar_format],
        'C': ['Market Capitalization', dollar_format],
        'D': ['Number of Shares to Buy', integer_format]
    }

    for column in column_formats.keys():
        writer.sheets['Recommended Trades'].set_column(f'{column}:{column}', 18, column_formats[column][1])
        writer.sheets['Recommended Trades'].write(f'{column}1', column_formats[column][0], column_formats[column][1])
    writer.save()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()


# TODO: add secrets to gitignore

