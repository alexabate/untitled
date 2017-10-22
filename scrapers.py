import pickle
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import json
import re
import sys
import time
import requests
import logging
from bs4 import BeautifulSoup
import numpy as np

from measure import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_recipes(common_ingredients, recipes=None, save_to_file='puppy.p',
                max_page=1000, recipe_puppy_url='http://www.recipepuppy.com/api/'):
    """
    Get recipe urls from recipe puppy

    Parameters
    ----------
    common_ingredients: list of str
        list of common ingredients to search recipes as widely as possible
    recipes: dict or None
        dict of existing recipes
    save_to_file: str
        filename to save results to
    max_page: int
        maximum page of API search results to go through
    recipe_puppy_url: str
        url of the recipe puppy API

    Returns
    -------

    """
    if recipes is None:
        recipes = {}
    ii = 0
    cnt_repeat = 0
    cnt_failed = 0

    for ingredient in common_ingredients:
        logger.info('On ingredient', ingredient, '\n')

        for p in np.arange(1, max_page + 1):

            logger.info('On page', p)
            params = {'i': ingredient, 'p': p}

            try:
                req = requests.get(recipe_puppy_url, params=params)
                logger.info('status code =', req.status_code)

                #                 if req.status_code == 500:
                #                     time.sleep(10)
                #                     print('trying again')
                #                     req = requests.get(recipe_puppy_url, params=params)
                #                     print('status code now =', req.status_code)

                if req.status_code >= 400:
                    logger.info('... continuing\n')
                    cnt_failed += 1
                    continue

                results = req.json()['results']
                logger.info(len(results), 'recipes on this page')

                if len(results) == 0:
                    break

                for result in results:

                    if result['title'] in recipes:
                        if result['href'] == recipes[result['title']]['href']:
                            logger.info(result['title'], 'already in recipes')
                            cnt_repeat += 1
                        else:
                            recipes[result['title'] + str(ii)] = {'href': result['href']}
                            ii += 1
                    else:
                        recipes[result['title']] = {'href': result['href']}
                        #     except 'json.decoder.JSONDecodeError':
                        #         print('json')
                        #     except TypeError
            except Exception as e:
                logger.info(e.__doc__)
                logger.info("Error:", sys.exc_info()[0])
                logger.info(req.status_code, 'page failed')
                cnt_failed += 1

            logger.info()
            time.sleep(1)

    logger.info('\n{} recipes'.format(len(recipes)))
    logger.info('Pages failed = {}, repeated recipes = {}, repeated titles = {}'.format(cnt_failed,
                                                                                  cnt_repeat,
                                                                                  ii))

    info = {'recipes': recipes}
    pickle.dump(info, open(save_to_file, 'wb'))
    return recipes


def get_unique_sites(recipes):
    """
    Return number of recipe urls in each domain

    Parameters
    ----------
    recipes: dict

    Returns
    -------
    unique_sites: dict
        keyed by site domain, with values = number of recipes
    """
    unique_sites = {}
    for k in recipes.keys():
        site = recipes[k]['href'].split('/')[2]
        if site in unique_sites:
            unique_sites[site] += 1
        else:
            unique_sites[site] = 1
    return unique_sites


def get_bbc_recipe_urls(filename='bbc_sitemap.txt',
                        url_domain='http://www.bbc.co.uk/food/recipes/',
                        sitemap='http://www.bbc.co.uk/food/sitemap.xml'):
    """
        Save list of recipe urls to a file

        Parameters
        ----------
        filename: str
            filename to save list of urls to
        url_domain: str
            url stem of recipe urls
        sitemap: str
            url fo sitemap location

        Returns
        -------
        urls: list of str
            list of recipe urls
    """
    page = requests.get(sitemap)
    sitemap = BeautifulSoup(page.text, 'lxml')

    urls = []
    with open(filename, 'w') as f:
        for line in sitemap.find_all('loc'):
            for string in line.stripped_strings:
                if string.startswith(url_domain):
                    f.write(string + '\n')
                    urls.append(string)
    return urls


class RecipeScraper(object):
    """
    Abstract base class for scraping recipes from websites
    Based on https://github.com/cookbrite/Recipe-to-Markdown
    """
    def __init__(self, parser="html5lib", use_selenium=False, **kwargs):

        if 'url' in kwargs:
            setattr(self, 'url', kwargs['url'])

            if use_selenium:
                c = self.selenium(self.url)
            else:
                result = requests.get(self.url)
                try:
                    result.raise_for_status()
                    self.html = result.content
                except requests.RequestException:
                    logger.info('failed to scrape {}'.format(self.url))
                    logger.info("Failed request, status code = {}".format(result.status_code))
                    self.html = result.content

        elif 'html' in kwargs:
            setattr(self, 'html', kwargs['html'])
            setattr(self, 'url', '')

        try:
            self.soup = BeautifulSoup(self.html, parser)
        except:
            logger.info("Failed to soup, c = {}".format(self.html))
            logger.info("parser = {}".format(parser))

    def selenium(self, url):
        """get HTML using selenium instead of requests
        """
        binary = FirefoxBinary('/usr/lib/firefox/firefox')
        browser = webdriver.Firefox(firefox_binary=binary)  # open firefox
        agent = browser.execute_script("return navigator.userAgent")
        logger.info(agent)
        browser.get(url)
        c = browser.page_source
        browser.close()
        return c

    def parse_ingredients_list(self):
        """
        Turn list of ingredients (list of str) into
        list of dict with key-values:
        - name: str (name of ingredient)
        - amount: str (numerical amount of ingredient)
        - unit: str (unit of measure)
        """
        ingredient_list = self.ingredients()
        amount_pattern = '.+?(?=([a-zA-Z]|\())'  # r'(\d+)?'

        ingredient_dicts = []
        for ingredients in ingredient_list:

            for ingredient in ingredients:

                match_amount = re.search(amount_pattern, ingredient)
                try:
                    amount = match_amount.group(0).strip()
                    if re.search('[a-zA-Z]', amount) or len(amount) == 0:
                        amount = None
                except:
                    amount = None

                match_unit = re.search(measure_pattern, ingredient)
                if match_unit is None:
                    unit = None
                    ingr = ingredient[match_amount.end() - 1:].strip()
                else:
                    unit = match_unit.group(0).strip()
                    ingr = ingredient[match_unit.end():].strip()
                logger.info('{}\namount = {}, unit = {}, ingredient = {}\n\n'.format(ingredient,
                                                                                     amount,
                                                                                     unit,
                                                                                     ingr))
                ingredient_dicts.append({'name': ingr,
                                         'amount': amount,
                                         'unit':unit})
        return ingredient_dicts

    def parse_instructions(self):
        """
        Turn str containing recipe instructions into list
        of str containing each recipe step
        """
        return NotImplemented

    def recipe_name(self):
        raise NotImplementedError

    def ingredients(self):
        """Return list of ingredients
        """
        raise NotImplementedError

    def instructions(self):
        """Return of instructions"""
        raise NotImplementedError

    def total_time(self):
        raise NotImplementedError

    def cook_time(self):
        raise NotImplementedError

    def prep_time(self):
        raise NotImplementedError

    def num_servings(self):
        raise NotImplementedError

    def rating(self):
        """Return rating of recipe"""
        raise NotImplementedError

    def num_ratings(self):
        """Return number of times recipe was rated"""
        raise NotImplementedError

    def date_published(self):
        raise NotImplementedError

    def description(self):
        """Return str of recipe description"""
        raise NotImplementedError


class FoodDotCom(RecipeScraper):
    def __init__(self, url, use_selenium=False):

        url = self.check_url(url)
        super(FoodDotCom, self).__init__(url, use_selenium)
        self.meta = json.loads(self.soup.find_all("div", {'class': "fd-page-feed"})[0] \
                               .find("script", {"type": "application/ld+json"}).contents[0])

    def check_url(self, url):
        if url.startswith('http://www.recipezaar.com'):
            logger.info('changing url to food.com domain')
            return 'http://www.food.com/recipe/' + url.split('.com')[-1].lower()
        else:
            return url

    def recipe_name(self):
        return self.meta['name']

    def ingredients(self):
        return self.meta['recipeIngredient']

    def instructions(self):
        return self.meta['recipeInstructions']

    def total_time(self):
        return self.parse_time(self.meta['totalTime'])

    def cook_time(self):
        return self.parse_time(self.meta['cookTime'])

    def prep_time(self):
        return self.parse_time(self.meta['prepTime'])

    def num_servings(self):
        return int(re.search('[0-9]+', self.meta['recipeYield']).group(0))

    def rating(self):
        return float(self.meta['aggregateRating']['ratingValue'])

    def num_ratings(self):
        return int(self.meta['aggregateRating']['reviewCount'])

    def date_published(self):
        return self.meta['datePublished']

    def description(self):
        return self.meta['description']

    def parse_time(self, t):
        m = re.search('PT[0-9]+?H', t)
        try:
            num_hours = int(
                [y for y in [x for x in m.group(0).split('PT') if len(x) > 0][0].split('H') if len(y) > 0][0])
        except:
            num_hours = 0
        m = re.search('[0-9]+M', t)
        try:
            num_mins = int(
                [y for y in [x for x in m.group(0).split('PT') if len(x) > 0][0].split('M') if len(y) > 0][0])
        except:
            num_mins = 0
        return {'hours': num_hours, 'mins': num_mins}


class BBCFood(RecipeScraper):
    def __init__(self, parser='lxml', use_selenium=False, **kwargs):
        super(BBCFood, self).__init__(parser=parser, use_selenium=use_selenium, **kwargs)

    def recipe_name(self):
        name = ''
        try:
            name = self.soup.find('h1', class_='content-title__text').text.replace('\n', '')
        except:
            logger.info('Failed to retrieve recipe name')
        return name

    def ingredients(self):
        ingredients = []
        try:
            ingredients = [x for x in self.soup.find('div', class_='recipe-ingredients').text.split('\n')
                           if x != '' and not x.startswith('For the') and not x.startswith('Ingredients')]
        except:
            logger.info('Failed to retrieve ingredients')
        return ingredients

    def instructions(self):
        instructions = []
        try:
            instructions = [x for x in self.soup.find('div', class_='recipe-method').text.split('\n')
                            if x != '' and not x.startswith('Method')]
        except:
            logger.info('Failed to retrieve instructions')
        return instructions

    def total_time(self):
        total_time = {'hours': 0, 'mins': 0}
        try:
            for time_unit in total_time.keys():
                total_time[time_unit] += self.cook_time()[time_unit] + self.prep_time()[time_unit]
        except:
            logger.info('Failed to retrieve total time')
        return total_time

    def cook_time(self):
        return self.parse_time(self.soup.find('p', class_='recipe-metadata__cook-time').text)

    def prep_time(self):
        return self.parse_time(self.soup.find('p', class_='recipe-metadata__prep-time').text)

    def num_servings(self):
        try:
            s = self.soup.find('p', class_='recipe-metadata__serving').text
            num_served = s.split(' ')[-1]
        except:
            num_served = ''
        return num_served

    def rating(self):
        raise NotImplementedError

    def num_ratings(self):
        raise NotImplementedError

    def date_published(self):
        raise NotImplementedError

    def description(self):
        d = ''
        try:
            d = self.soup.find('p', class_='recipe-description__text')
            if d is not None:
                d = d.text.strip()
            else:
                d = ''
        except:
            logger.info('Failed to retrieve description')
        return d

    def parse_time(self, t):
        # take upper time limit
        # {'hours': num_hours, 'mins': num_mins}
        times = {'hours': 0, 'mins': 0}
        try:
            m = re.search('[0-9]+ (hours?|mins?)$', t).group(0).split(' ')
            if m[-1].startswith('min'):
                times['mins'] = m[0]
            if m[-1].startswith('hour'):
                times['hours'] = m[0]
        except:
            logger.info('Failed to retrieve time from {}'.format(t))
        return times

