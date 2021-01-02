#!/usr/bin/python

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

def update_product_details(href_properties, return_new_href_values = False):
    """ Save the details of any new products that hasn't been found before.

        Notes
        -----
        It is not assumed that all of href_properties are new products, and a search will
        be performed to find the new products

        Parameters
        ----------
        href_properties : dict - str : dict
            href_properties is a dictionary with keys being the href. The associated values are dictionaries
            which lists the attributes of the product associated with the href.
            This dictionary should be given from `pinboard_attributes`

        return_new_href_values : :obj:`bool`, optional
            If set to `True` then this will return the href of any new products

        Returns
        -------
        None or list of str
            If return_new_href_values = False - Returns None
            If return_new_href_values = True  - Returns list of the href values
    """

    href_values = list(href_properties.keys())

    # Load old product details
    product_details = pd.read_csv('the_iconic_product_details.csv').set_index('href')
    product_details.index = product_details.index.astype(str)

    # Find any new href
    existing_href = product_details.index
    new_href = [href for href in href_values if href not in existing_href]

    # Update and store results
    for href in new_href:
        for detail in ['href_url', 'Item', 'Brand']:
            product_details.loc[href, detail] =  href_properties[href][detail]

    product_details.fillna(-1, inplace = True)
    product_details.to_csv('the_iconic_product_details.csv')

    if return_new_href_values:
        return new_href

def update_product_prices(href_properties):
    """ Save the prices of the scalped items

        Parameters
        ----------
        href_properties : dict - str : dict
            href_properties is a dictionary with keys being the href. The associated values are dictionaries
            which lists the attributes of the product associated with the href.
            This dictionary should be given from `pinboard_attributes`
    """
    today = datetime.date.today()

    # Load Data
    product_prices = pd.read_csv('the_iconic_product_prices.csv').set_index('href')
    product_prices.index = product_prices.index.astype(str)

    product_prices[today] = -1

    # Update and save results
    href_values = list(href_properties.keys())
    for href in href_values:
        product_prices.loc[href, today] = href_properties[href]['Price']

    product_prices.fillna(-1, inplace = True)

    product_prices.to_csv('the_iconic_product_prices.csv')

def update_product_gender(href_is_men, new_href):
    """ Update the gender of any new products

        Notes
        -----
        To get `new_href`, run `update_product_details` first with `return_new_href_values = False`

        Parameters
        ----------
        href_is_men : dict - str : bool
            A dictionary with keys being href, and the associated values determine if the
            associated product was listed as men

        new_href : list of str
            List of new href
    """
    href_values = list(href_is_men.keys())

    product_details = pd.read_csv('the_iconic_product_details.csv').set_index('href')
    product_details.index = product_details.index.astype(str)

    for href in new_href:
        product_details.loc[href, 'is_men'] =  href_is_men[href]

    product_details.to_csv('the_iconic_product_details.csv')


if __name__ == '__main__':
    today = datetime.date.today()

    # Back up data
    back_up_files = ['the_iconic_product_details', 'the_iconic_product_prices']
    for file in back_up_files:
        new_path = f'data_backup/{str(today)}_{file}.csv'
        temp_df = pd.read_csv(f'{file}.csv').set_index('href')
        temp_df.index = temp_df.index.astype(str)
        temp_df.to_csv(new_path)


    # Number of pages per category to scrap
    num_pages = 15
    categories = get_categories()
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
    new_href_values = update_product_details(href_properties, return_new_href_values = True)
    update_product_prices(href_properties)
    update_product_gender(href_is_men, new_href_values)
    print('FINISHED')
