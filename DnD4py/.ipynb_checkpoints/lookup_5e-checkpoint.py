#!/usr/bin/env python
from bs4 import BeautifulSoup as bs
import requests
import argparse
from textwrap import fill as wrap

__all__ = ['Roll20', 'Roll20Monster', 'Roll20Spell', 'Roll20Item']


def stringify(text):
    text = text.replace('<br>', '\n').replace('<br />', '\n')
    text = text.replace('<h2>', '*').replace('</h2>', '*\n')
    text = text.replace('<strong>', '').replace('</strong>', '')
    return wrap(text, 80, drop_whitespace=False, replace_whitespace=False)


def score_to_mod(score):
    return '{:+d}'.format((score - 10)//2)


class Roll20:
    
    def __init__(self, name, site='https://roll20.net/compendium/dnd5e/'):
        self.name = name.rstrip().title()
        formatted_name = self.name.replace(' ', '_')
        url = site + formatted_name
        page = requests.get(url)
        if page.status_code != 200:
            raise FileNotFoundError('{:s} not found at {:s}.'.format(name,
                                                                     url))
        html = page.text
        soup = bs(html, 'html.parser')
        self.attributes = ({stringify(a.text):
                            stringify(a.find_next(attrs={'class':
                                                         'value'}).text)
                            for a in soup.find_all(attrs={'class':
                                                          'col-md-3 attrName'})})
        self.desc = '\n'.join([stringify(val.text)
                               for val in soup.find_all(id='origpagecontent',
                                                        attrs={'type':
                                                               'text/html'})])
        
    def get(self, key, alt=None):
        if key == 'desc':
            return self.desc or alt
        else:
            return self.attributes.get(key, alt)
            
    @property
    def str_attributes(self):
        res = ""
        for k, v in self.attributes.items():
            res += k + ': ' + v + '\n'
        return res
        
    @property
    def str_desc(self):
        res = '\n\nDescription\n===========================\n' + self.desc
        return res
        
    def __len__(self):
        return len(self.attributes)
        
    def __str__(self):
        return self.name + '\n\n' + self.str_attributes + self.str_desc
        

class Roll20Monster(Roll20):
    
    def __init__(self, name,
                 site='https://roll20.net/compendium/dnd5e/Monsters:'):
        super().__init__(name, site=site)
                
    @property
    def str_attributes(self):
        res = ''
        for k in ['HP', 'AC', 'Speed', 'Challenge Rating']:
            res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        res += '\n'
        for k in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']:
            res += k + '\t'
        res += '\n'
        for k in ['STR', 'DEX', 'CON', 'INT', 'WIS', 'CHA']:
            s = self.get(k, None)
            res += '{:s} ({:s})\t'.format(s, score_to_mod(int(s)))
        res += '\n\n'
        for k in ['Type', 'Size', 'Alignment', 'Senses', 'Skills',
                  'Languages']:
            res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        return res


class Roll20Spell(Roll20):
    def __init__(self, name,
                 site='https://roll20.net/compendium/dnd5e/Spells:'):
        super().__init__(name, site=site)
                                        
    @property
    def str_attributes(self):
        res = ''
        for k in ['Level', 'School', 'Classes']:
            if self.get(k) is not None:
                res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        res += '\n'
        for k in ['Casting Time', 'Duration', 'Components', 'Material']:
            if self.get(k) is not None:
                res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        res += '\n'
        for k in ['Range', 'Damage', 'Damage Type', 'Save', 'Target']:
            if self.get(k) is not None:
                res += k + ': ' + self.get(k, 'EMPTY') + '\n'
        return res
                                    
                                    
class Roll20Item(Roll20):
    def __init__(self, name,
                 site='https://roll20.net/compendium/dnd5e/Items:'):
        super().__init__(name, site=site)


def monster_lookup(name):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('query', nargs='+', help='The words to search')

    args = parser.parse_args()
    text = ' '.join(args.query)
    
    item = Roll20Monster(text)
    print(item)


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--monster',
                        help='Search only monster lists', action='store_true')
    parser.add_argument('--spell',
                        help='Search only spell lists', action='store_true')
    parser.add_argument('--item',
                        help='Search only item lists', action='store_true')
    parser.add_argument('query', nargs='+', help='The words to search')

    args = parser.parse_args()
    text = ' '.join(args.query)
    
    if args.monster:
        item = Roll20Monster(text)
    elif args.spell:
        item = Roll20Spell(text)
    elif args.item:
        item = Roll20Item(text)
    else:
        for r in [Roll20Monster, Roll20Spell,
                  Roll20Item, Roll20]:
            try:
                item = r(text)
            except FileNotFoundError as e:
                continue
    if item is None or len(item) == 0:
        print('Not Found')
    else:
        print(item)

        
if __name__ == '__main__':
    main()