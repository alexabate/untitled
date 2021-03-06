import logging
import pickle
import time
import bs4

from scrapers import BBCFood

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


recipe_data = {}
html_data = {}
try:
    logger.info('Reading recipes already scraped')
    recipe_data = pickle.load(open('bbc_recipe_data.p', 'rb'))
    html_data = pickle.load(open('bbc_recipe_html.p', 'rb'))
except:
    logger.info('Starting from scratch')
    recipe_data = {}
    html_data = {}

# i = 0
with open('bbc_sitemap.txt', 'r') as f:
    for line in f.readlines():

        if len(recipe_data)%100 == 0:
            logger.info('Scraping recipe {}'.format(len(recipe_data)))

        line = line.strip('\n')
        recipe_key = line.split('/')[-1]

        # Don't get pages that have already been collected
        if recipe_key not in recipe_data:
            logger.info('scraping {}'.format(line))
            try:
                scrape_recipe = BBCFood(url=line)
                recipe_data[recipe_key] = {'url': line,
                                           'name': scrape_recipe.recipe_name(),
                                           'ingredients': scrape_recipe.ingredients(),
                                           'instructions': scrape_recipe.instructions(),
                                           'num_servings': scrape_recipe.num_servings(),
                                           'cook_time': scrape_recipe.cook_time(),
                                           'prep_time': scrape_recipe.prep_time(),
                                           'description': scrape_recipe.description()}
                html_data[recipe_key] = scrape_recipe.html
                time.sleep(10)
            except:
                logger.info('failed on url {}'.format(line))
                logger.info('{} recipes collected'.format(len(recipe_data)))
                pickle.dump(recipe_data, open("bbc_recipe_data.p", "wb"))
                pickle.dump(html_data, open("bbc_recipe_html.p", "wb"))
                soup = bs4.BeautifulSoup(scrape_recipe.html, 'html5lib')
                if soup.find('div', class_="recipe-not-found__text").text == 'Recipe not found':
                   logger.info('continuing as recipe not found') 
                   continue
                else:
                    raise Exception('Could not scrape recipe, exiting')

        # i += 1
        # if i > 3:
        #     break
        #

pickle.dump(recipe_data, open("bbc_recipe_data.p", "wb"))
pickle.dump(html_data, open("bbc_recipe_html.p", "wb"))
