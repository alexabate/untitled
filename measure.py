measures = {'drop': ['dr', 'gt', 'gtt'],
            'smidgen': ['smdg', 'smi'],
            'pinch': ['pn'],
            'dash': ['ds', 'dashes'],
            'saltspoon': ['scruple' 'ssp', 'salt spoon', 'salt spoons'],
            'coffeespoon':['coffee spoon', 'coffee spoons', 'coffeespoons'],
            'fluid dram':['fluid drams'],
            'teaspoon': ['tsp' 't', 'tsps', 'teaspoons', 'tea spoon'],
            'dessertspoon': ['dsp', 'dssp' 'dstspn', 'dessertspoons',
                             'dsps', 'dessert spoon', 'dessert spoons'],
            'tablespoon': ['tbsp' 'T', 'table spoon', 'tablespoons', 'table spoons', 'tbsps'],
            'fluid ounce': ['fl.oz',  'oz', 'floz', 'fl oz', 'fluid ounces'],
            'ounce': ['ounces', 'oz'],
            'wineglass': ['wgf', 'wine glass', 'wineglasses', 'wine gls', 'wine glasses'],
            'gill': ['teacup' 'tcf', 'tea cup'],
            'cup': ['C', 'cp', 'cups', 'cps'],
            'pint': ['pt', 'pints'],
            'quart': ['qt', 'qts', 'quarts'],
            'pottle': ['pot'],
            'gallon': ['gal', 'gals', 'gallons'],
            'gram': ['grams', 'g'],
            'pound': ['pounds', 'lb', 'lbs'],
            'milligram': ['milligrams', 'mg'],
            'kilogram': ['kilograms', 'kg'],
            'litre': ['liter', 'litres', 'liters', 'lt', 'lts', 'l'],
            'millilitres': ['milliliter', 'milliliters', 'ml', 'mls'],
            'can': ['cans'],
            'bunch': ['bunches'],
            'package': ['packages']
                       }

measure_pattern = r'(\s+'
measures_list = []
for k, m in measures.items():
    measures_list.append(k)
    measures_list += m

    measure_pattern += k + r'\s+|\s+'
    measure_pattern += r'\s+|\s+'.join(m) + r'\s+|\s+'

measure_pattern = measure_pattern[:-7] + r'\s+)'