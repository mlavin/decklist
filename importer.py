"""Import data from pokemontcg.io and Amazon API."""

import argparse
import os
import time

import redis
import requests

from amazon import get_amazon_info


parser = argparse.ArgumentParser(description='Import Pokemon Set/Card Info.')
parser.add_argument('--standard', action='store_true', dest='standard', help='Only standard sets.')
parser.add_argument('--set-name', action='append', dest='sets', help='One or more set names.')
parser.add_argument('--card', action='append', dest='cards', help='One or more card numbers.')

def main():
    args = parser.parse_args()
    client = redis.from_url(url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    with requests.Session() as session:
        # Fetch all expanded legal sets
        names = args.sets
        if names:
            params = {'name': ','.join(names)}
        elif args.standard:
            params = {'standardLegal': 'true'}
        else:
            params = {'expandedLegal': 'true'}
        sets = session.get(url='https://api.pokemontcg.io/v1/sets', params=params).json()
        for info in sets['sets']:
            print('Fetching set: {name}'.format(**info))
            if info['name'] == 'Generations':
                # Account for the Radiant collection in the total count
                info['totalCards'] -= 32
            # Get all cards for this set
            params = {'set': info['name'], 'pageSize': '200'}
            if args.cards:
                params['number'] = '|'.join(args.cards)
            cards = session.get(
                url='https://api.pokemontcg.io/v1/cards',
                params=params).json()
            for card in cards['cards']:
                details = {}
                try:
                    int(card['number'])
                    set_number = '{}/{}'.format(card['number'], info['totalCards'])
                except ValueError:
                    set_number = card['number']
                card['setNumber'] = set_number
                # Lookup ASIN from Amazon
                details.update(get_amazon_info(card, session=session))
                # Copy info from card dict
                for name in ('id', 'name', 'imageUrl', 'subtype', 'supertype', 'setNumber',
                             'number', 'rarity', 'series', 'set', 'setCode'):
                    details[name] = card[name]
                client.hmset(card['id'], details)
                # Sleep to prevent rate limits on the API
                time.sleep(0.5)

if __name__ == '__main__':
    main()
