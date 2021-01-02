from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from functools import reduce
import numpy as np
import datetime
import pandas as pd

from the_iconic_pinboard_scrapper import get_categories, scrap_pinboard, get_unique_products


def write_to_debug(error_str):
    """ Write error to a log file

        Parameters
        ----------
        error_str : str
            Error string
    """
    file = open('debug.log', 'a')
    file.write(f'{error_str}\n')
    file.close()

def save_product_details(href_properties):
    href_values = list(href_properties.keys())

    product_details = pd.DataFrame(index = href_values)
    product_details.index.name = 'href'

    for detail in ['href_url', 'Brand', 'Item']:
        product_details.loc[href_values, detail] = [val[detail] for val in href_properties.values()]

    product_details.to_csv('the_iconic_product_details.csv')

def save_product_prices(href_properties):
    today = datetime.date.today()

    href_values = list(href_properties.keys())

    product_prices = pd.DataFrame(index = href_values)
    product_prices.index.name = 'href'

    product_prices.loc[href_values, today] = [val['Price'] for val in href_properties.values()]

    product_prices.to_csv('the_iconic_product_prices.csv')

def save_product_gender(href_is_men):
    href_values = list(href_is_men.keys())

    product_details = pd.read_csv('the_iconic_product_details.csv').set_index('href')
    product_details.index = product_details.index.astype(str)

    product_details.loc[href_values, 'is_men'] = list(href_is_men.values())
    product_details.to_csv('the_iconic_product_details.csv')


if __name__ == '__main__':
    num_pages = 10
    categories = get_categories(gender = None)
    products = []

    href_is_men = {}

    for category in categories:
        category_type = 'men' in category

        url = f'https://www.theiconic.com.au{category}'
        print(f'Scrapping {url}')

        new_products = [scrap_pinboard(f'{url}?page={i}') for i in range(num_pages)]
        products += reduce(lambda x, y: x + y, new_products)

        product_gender = {item['href'] : category_type for item in products}
        href_is_men.update(product_gender)

    href_properties = get_unique_products(products)

    print('SAVING RESULTS')
    save_product_details(href_properties)
    save_product_prices(href_properties)
    save_product_gender(href_is_men)
    print('FINISHED')
