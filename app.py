import asyncio
import datetime
import os
import random
import time

import aiohttp_jinja2
import jinja2
import redis

from aiohttp import web, ClientSession

from parser import parse_deck_list


@aiohttp_jinja2.template('home.html')
async def home(request):
    return {}


@aiohttp_jinja2.template('deck-form.html')
async def deckform(request):
    return {}


async def get_card_price(client, card):
    url = 'http://pokeprices.doeiqts.com/api/getcard'
    params = {'cardset': card['set'].lower(), 'cardnumber': card['number']}
    price = 'N/A'
    async with client.get(url, params=params) as response:
        result = await response.json()
        if result.get('status', '').lower() == 'success':
            try:
                price = float(result['cards'][0]['price'])
            except (ValueError, IndexError, KeyError):
                price = 'N/A'
    return price


@aiohttp_jinja2.template('deck-result.html')
async def deckresult(request):
    data = await request.post()
    decklist = data.get('decklist', '')
    results = []
    errors = []
    parsed = parse_deck_list(decklist)
    total_cards = 0
    total_cost = 0
    async with ClientSession(loop=loop) as client:
        for card in parsed:
            if 'id' in card:
                info = request.app['redis'].hgetall(card['id']) or {}
                # Need to convert keys from bytes
                for key, value in info.items():
                    card[key.decode('utf-8')] = value.decode('utf-8')
                price = card.get('price') or None
                timestamp = card.get('timestamp') or (time.time() - 60 * 60 * 24)
                if not price or float(timestamp) < (time.time() - 60 * 60 * 12):
                    price = await get_card_price(client, card)
                    timestamp = time.time()
                    request.app['redis'].hmset(card['id'], {'price': price, 'timestamp': timestamp})
                    card['price'] = price
                    card['timestamp'] = timestamp
                card['timestamp'] = datetime.datetime.fromtimestamp(float(card['timestamp'])).strftime('%I:%M %p EST')
                if card['price'] != 'N/A':
                    card['price'] = float(card['price'])
                    card['subtotal'] = card['price'] * int(card['quantity'])
                    total_cost += card['subtotal']
                total_cards += int(card['quantity'])
                results.append(card)
            else:
                errors.append(card['name'])
    return {
        'results': results,
        'errors': errors,
        'total_cards': total_cards,
        'total_cost': total_cost,
        'timestamp': datetime.datetime.now().strftime('%I:%M %p EST'),
        'amazon_associate_id': request.app['AWS_ASSOCIATE_ID'],
        'amazon_access_key': request.app['AWS_ACCESS_KEY_ID'],
    }


def setup_routes(app):
    app.router.add_get('/', home)
    app.router.add_get('/deckbuilder/', deckform)
    app.router.add_post('/deckbuilder/', deckresult)
    app.router.add_static('/static/', path=os.path.join(app['base_dir'], 'static'), name='static')


def format_currency(value):
    return "{:,.2f}".format(value)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = web.Application(loop=loop)
    app['base_dir'] = os.path.dirname(os.path.abspath(__file__))
    app['redis'] = redis.from_url(url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    app['AWS_ASSOCIATE_ID'] = os.environ.get('AWS_ASSOCIATE_ID', '')
    app['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID', '')
    app['AWS_SECRET_KEY'] = os.environ.get('AWS_SECRET_KEY', '')
    setup_routes(app)
    env = aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(os.path.join(app['base_dir'], 'templates')))
    env.globals['GA_TRACKING_ID'] = os.environ.get('GA_TRACKING_ID', '')
    env.filters['currency'] = format_currency
    web.run_app(app, host='127.0.0.1', port=int(os.environ.get('PORT', '8080')))
