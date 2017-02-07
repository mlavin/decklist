import asyncio
import datetime
import os
import random

import aiohttp_jinja2
import jinja2
import redis

from aiohttp import web

from parser import parse_deck_list


@aiohttp_jinja2.template('home.html')
async def home(request):
    return {}


@aiohttp_jinja2.template('deck-form.html')
async def deckform(request):
    return {}


@aiohttp_jinja2.template('deck-result.html')
async def deckresult(request):
    data = await request.post()
    decklist = data.get('decklist', '')
    results = parse_deck_list(decklist)
    total_cards = 0
    total_cost = 0
    for card in results:
        info = request.app['redis'].hgetall(card['id']) or {}
        # Need to convert keys from bytes
        for key, value in info.items():
            card[key.decode('utf-8')] = value.decode('utf-8')
        card['price'] = random.random() * 25
        card['subtotal'] = card['price'] * int(card['quantity'])
        total_cards += int(card['quantity'])
        total_cost += card['subtotal']
    return {
        'results': results,
        'total_cards': total_cards,
        'total_cost': total_cost,
        'errors': {},
        'timestamp': datetime.datetime.now().strftime('%I:%M %p EST')
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
    setup_routes(app)
    env = aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(os.path.join(app['base_dir'], 'templates')))
    env.filters['currency'] = format_currency
    web.run_app(app, host='127.0.0.1', port=int(os.environ.get('PORT', '8080')))
