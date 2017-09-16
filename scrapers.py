import pickle
import operator
import json
import re
import sys
import time
import requests
from bs4 import BeautifulSoup
import numpy as np


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
        print('On ingredient', ingredient, '\n')

        for p in np.arange(1, max_page + 1):

            print('On page', p)
            params = {'i': ingredient, 'p': p}

            try:
                req = requests.get(recipe_puppy_url, params=params)
                print('status code =', req.status_code)

                #                 if req.status_code == 500:
                #                     time.sleep(10)
                #                     print('trying again')
                #                     req = requests.get(recipe_puppy_url, params=params)
                #                     print('status code now =', req.status_code)

                if req.status_code >= 400:
                    print('... continuing\n')
                    cnt_failed += 1
                    continue

                results = req.json()['results']
                print(len(results), 'recipes on this page')

                if len(results) == 0:
                    break

                for result in results:

                    if result['title'] in recipes:
                        if result['href'] == recipes[result['title']]['href']:
                            print(result['title'], 'already in recipes')
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
                print(e.__doc__)
                # print (e.message)
                print("Error:", sys.exc_info()[0])
                print(req.status_code, 'page failed')
                cnt_failed += 1

            print()
            time.sleep(1)

    print('\n{} recipes'.format(len(recipes)))
    print('Pages failed = {}, repeated recipes = {}, repeated titles = {}'.format(cnt_failed,
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


class RecipeScraper(object):
    """
    Abstract base class for scraping recipes from websites
    Based on https://github.com/cookbrite/Recipe-to-Markdown
    """

    def __init__(self, url):
        self.url = url
        result = requests.get(url)
        c = result.content
        self.soup = BeautifulSoup(c, "html5lib")

    def parse_ingredients_list(self):
        """
        Turn list of ingredients (list of str) into
        a dict with key-value pairs:
        - name: str (name of ingredient)
        - amount: float (numerical amount of ingredient)
        - unit: str (unit of measure)
        """
        ingredient_list = self.ingredients()
        return NotImplemented

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
    def __init__(self, url):

        url = self.check_url(url)
        super(FoodDotCom, self).__init__(url)
        self.meta = json.loads(self.soup.find_all("div", {'class': "fd-page-feed"})[0] \
                               .find("script", {"type": "application/ld+json"}).contents[0])

    def check_url(self, url):
        if url.startswith('http://www.recipezaar.com'):
            print('changing url to food.com domain')
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

