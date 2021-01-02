from urllib.request import urlopen
from bs4 import BeautifulSoup
import re
from functools import reduce
import numpy as np
import datetime
import pandas as pd

""" Todo
    ----
    In pinboard_price: Write error if price_obj is still not length 1 after checking for price final, aka sale
    or if the length is less than 1

    In get_unique_products : fix the error code
"""

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

def pinboard_brand(single_item_obj):
    """ Given a single item of a pinboard, return the barnd of the item

        Parameters
        ----------
        single_item_obj : BeautifulSoup
            A BeautifulSoup object of a single item of the pinboard

        Returns
        -------
        str
            The brand of the item
    """
    brand_obj = single_item_obj.find('span', {'class': 'brand'})
    return re.sub('<[^>]*>', '', str(brand_obj))

def pinboard_title(single_item_obj):
    """ Given a single item of a pinboard, return the title (name) of the item

        Parameters
        ----------
        single_item_obj : BeautifulSoup
            A BeautifulSoup object of a single item of the pinboard

        Returns
        -------
        str
            The title of the item
    """
    title_obj = single_item_obj.find('span', {'class': 'name'})
    return re.sub('<[^>]*>', '', str(title_obj))

def pinboard_price(single_item_obj):
    """ Given a single item of a pinboard, return the price of the item

        Parameters
        ----------
        single_item_obj : BeautifulSoup
            A BeautifulSoup object of a single item of the pinboard

        Returns
        -------
        float
            The price of the item
    """

    price_obj = single_item_obj.findAll('span', {'class': 'price'})
    if len(price_obj) > 1:
        price_obj = [x for x in price_obj if 'price final' in str(x)]

    if len(price_obj) != 1:
        error_str = f'Error in pinboard_price, `price_obj` length is not equal to 1'
        print(error_str)

        write_to_debug(error_str)
        write_to_debug(f'price_obj: {price_obj}')

    price_obj = price_obj[0]
    return float(re.sub('<[^>]+>|(\ \$)|,', '', str(price_obj)))

def pinboard_href(single_item_obj):
    """ Given a single item of a pinboard, return the href of the item
        The href is a sub-directory of the root url: https://www.theiconic.com.au/

        Parameters
        ----------
        single_item_obj : BeautifulSoup
            A BeautifulSoup object of a single item of the pinboard

        Returns
        -------
        str
            The href of the item
    """
    href_obj = single_item_obj.find('a', {"data-ng-click" : "tracking.click()"})
    href_str = re.findall('href=\"[^\"]*\"', str(href_obj))[0]
    return re.sub('(href=)|(\")', '', href_str)

def pinboard_attributes(bsObj):
    """ Given a single item of a pinboard, return the attributes of that item.
        Attributes are: href, Item (name), Brand, Price

        Parameters
        ----------
        bsObj : BeautifulSoup
            A BeautifulSoup object of a single item of the pinboard

        Returns
        -------
        dict : str - str/float
            A dictionary that uses the item's attributes as keys, with their corresponding values
    """

    attributes = {}

    attributes['href_url'] = pinboard_href(bsObj)
    attributes['href']     = re.findall('([0-9]+)\.html', attributes['href_url'])[0]

    attributes['Item']     = pinboard_title(bsObj)
    attributes['Brand']    = pinboard_brand(bsObj)
    attributes['Price']    = pinboard_price(bsObj)

    return attributes

def scrap_pinboard(pinboard_url):
    """ Given the url to a pinboard on the Iconic, returns the list of products
        and their prices/properties

        Parameters
        ----------
        pinboard_url : str
            The url of a pinboard

        Returns
        -------
        list of dict
            Returns a list of all the products on the scrapped page.
    """

    # Open url
    html = urlopen(f'{pinboard_url}')
    bsObj = BeautifulSoup(html, features = 'lxml')

    pinboard_products = bsObj.findAll("figure", {"class" : "pinboard"})

    # Scrap url
    try:
        new_products = [pinboard_attributes(single_item_obj) for single_item_obj in pinboard_products]
    except:
        error_str = f'Error occured when accesing page {html}'
        print(error_str)
        write_to_debug(f'{str(datetime.date.today())}: {error_str}')
        return []
    else:
        return new_products

def get_categories(gender = None):
    """ Returns the website subdirectories of a given gender

        Parameters
        ----------
        gender : :obj:str, optional
            If set as None, then both women and men categories will be returns
            If gender == `men` then only men will be returned, otherwise only women will be returned

        Returns
        -------
        list - str
            Returns a list of the website-directores
    """
    if gender is not None:
        if (gender != 'men') or (gender != 'women'):
            error_str = 'If gender is not None, then it must either take the value `men` or `women`. Otherwise it is assumed to be `women`.'

            print(error_str)
            write_to_debug(f'{str(datetime.date.today())}: WARNING : {error_str}')
            write_to_debug(f'gender : {gender}')

    # Open the home url
    html = urlopen('https://www.theiconic.com.au/')
    bsObj = BeautifulSoup(html, features = 'lxml')

    navbar_object = bsObj.findAll('div', {'class' : 'ti-tab-panel ti-tab-panel--1 ti-navbar__item__panel ti-navbar__item__panel--clothing'})

    # Get the categories
    if gender is None:
        women_categories = re.findall('tiNavEntry\.sendHoverTracking\([^,]*,', str(navbar_object[0]))
        men_categories = re.findall('tiNavEntry\.sendHoverTracking\([^,]*,', str(navbar_object[1]))
        categories =  women_categories + men_categories
    else:
        category_type = int(gender == 'men')
        categories = re.findall('tiNavEntry\.sendHoverTracking\([^,]*,', str(navbar_object[category_type]))

    # Remove dupilicate categories and sort
    filtered_categories = []
    for category in categories:
        new_category = re.findall('\\/[womens|mens]+\-clothing[^\\/]*/', category)
        if len(new_category) == 1:
            filtered_categories += new_category
    filtered_categories = sorted(list(set(filtered_categories)))

    return filtered_categories

def get_unique_products(products):
    """ When scalping from different sub-directories, there is bound to be duplicate products.
        This will remove any duplicate products.

        Parameters
        ----------
        products - list of dict
            This should be a list of dictionaries, where the dictionary keys are the attributes of the different products.
            This dictionary should be given from `pinboard_attributes`

        Returns
        -------
        list of dict
            A list similar to `products`, but with duplicate href removed
    """

    href_properties = {}

    for item in products:
        href = item['href']
        try:
            old_item_properties = href_properties[href]
        except:
            href_properties[href] = item
        else:
            # If the href already exists, check it is the same as the incoming item

            # Products may have a different default display.
            # This delets the display

            item_url = re.sub('display_.+', '', item['href_url'])
            old_item_url = re.sub('display_.+', '', old_item_properties['href_url'])

            is_equal = item_url == old_item_url
            if not is_equal:
                error_str = f'Error occured with {href}. See debug.log for more info.'
                print(error_str)

                write_to_debug(f'{str(datetime.date.today())}: {error_str}')
                write_to_debug(f"item['href_url'] : {item['href_url']}")
                write_to_debug(f"old_item_properties['href_url'] : {old_item_properties['href_url']}")

    return href_properties
