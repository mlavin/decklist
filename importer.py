"""Import data from pokemontcg.io and Amazon API."""

import os
import time

import redis
import requests

from amazon import get_amazon_info


def main():
    client = redis.from_url(url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    # Fetch all expanded legal sets
    sets = requests.get(
        url='https://api.pokemontcg.io/v1/sets',
        params={'expandedLegal': 'true'}).json()
    for info in sets['sets']:
        print('Fetching set: {name}'.format(**info))
        # Get all cards for this set
        cards = requests.get(
            url='https://api.pokemontcg.io/v1/cards',
            params={'set': info['name'], 'pageSize': '200'}).json()
        for card in cards['cards']:
            details = {}
            try:
                int(card['number'])
                set_number = '{}/{}'.format(card['number'], info['totalCards'])
            except ValueError:
                set_number = card['number']
            card['setNumber'] = set_number
            # Lookup ASIN from Amazon
            details.update(get_amazon_info(card))
            # Copy info from card dict
            for name in ('id', 'name', 'imageUrl', 'subtype', 'supertype', 'setNumber',
                         'number', 'rarity', 'series', 'set', 'setCode'):
                details[name] = card[name]
            client.hmset(card['id'], details)
            # Sleep to prevent rate limits on the API
            time.sleep(1)

if __name__ == '__main__':
    main()
