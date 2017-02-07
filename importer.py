"""Import data from pokemontcg.io and Amazon API."""

import os

import redis
import requests


def get_asin(card):
    """Fetch ASIN from the Amazon product API."""
    return ''


def main():
    client = redis.from_url(url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    # Fetch all expanded legal sets
    sets = requests.get(
        url='https://api.pokemontcg.io/v1/sets',
        params={'expandedLegal': 'true'}).json()
    for info in sets['sets']:
        # Get all cards for this set
        cards = requests.get(
            url='https://api.pokemontcg.io/v1/cards',
            params={'set': info['name'], 'pageSize': '200'}).json()
        for card in cards['cards']:
            details = {}
            # Lookup ASIN from Amazon
            details['asin'] = get_asin(card)
            # Copy info from card dict
            for name in ('id', 'name', 'imageUrl', 'subtype', 'supertype',
                         'number', 'rarity', 'series', 'set', 'setCode'):
                details[name] = card[name]
            client.hmset(card['id'], details)


if __name__ == '__main__':
    main()
