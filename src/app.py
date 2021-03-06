import asyncio
import base64
import binascii
import datetime
import json
import os
import random
import time
import urllib.parse

import aiohttp_jinja2
import jinja2
import redis

from aiohttp import web, ClientSession

from amazon import get_amazon_prices
from parser import parse_deck_list


@aiohttp_jinja2.template('home.html')
async def home(request):
    return {}


@aiohttp_jinja2.template('help.html')
async def site_help(request):
    return {}


async def card_guide(request):
    context = {}
    name = request.match_info.get('name', 'overview')
    if name not in ('overview', 'attacking-pokemon', 'supporting-pokemon', 'deck-search',
                    'draw-support', 'energy-acceleration', 'healing', 'recycle',
                    'disruption', 'switching', 'stadiums'):
        raise web.HTTPNotFound()
    template_name = 'guides/{}.html'.format(name)
    return aiohttp_jinja2.render_template(template_name, request, context)


async def get_card_price(client, card, redis):
    price = card.get('price') or None
    timestamp = card.get('timestamp') or (time.time() - 60 * 60 * 24)
    if not price or float(timestamp) < (time.time() - 60 * 60 * 12):
        url = 'http://pokeprices.doeiqts.com/api/getcard'
        params = {'cardset': card['set'].lower(), 'cardnumber': card['number']}
        price = 'N/A'
        async with client.get(url, params=params) as response:
            result = await response.text()
            try:
                result = json.loads(result)
            except:
                result = {}
            if result.get('status', '').lower() == 'success':
                try:
                    price = float(result['cards'][0]['price'])
                except (ValueError, IndexError, KeyError):
                    price = 'N/A'
        timestamp = time.time()
        if price != 'N/A':
            redis.hmset(card['id'], {'price': price, 'timestamp': timestamp})
    return {
        'price': float(price) if price != 'N/A' else price,
        'available': 60,
        'timestamp': datetime.datetime.fromtimestamp(float(timestamp)).strftime('%I:%M %p EST'),
    }


@aiohttp_jinja2.template('deck.html')
async def deck(request):
    compressed = request.rel_url.query.get('list', '')
    try:
        decklist = base64.urlsafe_b64decode(compressed).decode('utf-8')
    except (binascii.Error, binascii.Incomplete):
        # Strip off the invalid list
        raise web.HTTPFound('/deckbuilder/')

    if decklist:
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
                    card['quantity'] = int(card['quantity'])
                    results.append(card)
                else:
                    errors.append(card['name'])
            if request.app['AWS_ACCESS_KEY_ID'] and request.app['AWS_SECRET_KEY']:
                prices = await get_amazon_prices(results, client)
                for card in results:
                    card.update(prices.get(card.get('asin', ''), {'price': 'N/A', 'available': 0}))
                    if card['price'] != 'N/A':
                        card['subtotal'] = card['price'] * int(card['quantity'])
                        total_cost += card['subtotal']
                        total_cards += card['quantity']
                    card['timestamp'] = datetime.datetime.utcnow().strftime('%I:%M %p UTC')
            else:
                for card in results:
                    price = await get_card_price(client, card, request.app['redis'])
                    card.update(price)
                    if card['price'] != 'N/A':
                        card['subtotal'] = card['price'] * int(card['quantity'])
                        total_cost += card['subtotal']
                        total_cards += card['quantity']
        return {
            'results': results,
            'errors': errors,
            'total_cards': total_cards,
            'total_cost': total_cost,
            'share_url': request.url,
        }
    else:
        return {}


async def decksubmit(request):
    post = await request.post()
    decklist = post.get('decklist', '')
    compressed = base64.urlsafe_b64encode(decklist.encode('utf-8'))
    location = '/deckbuilder/?' + urllib.parse.urlencode({'list': compressed.decode('utf-8')})
    raise web.HTTPFound(location)


def setup_routes(app):
    app.router.add_get('/', home)
    app.router.add_get('/help/', site_help)
    app.router.add_get('/guides/', card_guide)
    app.router.add_get('/guides/{name}/', card_guide)
    app.router.add_get('/deckbuilder/', deck)
    app.router.add_post('/deckbuilder/', decksubmit)
    app.router.add_static('/static/', path=os.path.join(app['base_dir'], 'static'), name='static')
    app.router.add_static('/', path=os.path.join(app['base_dir'], 'public'), name='public')


def format_currency(value):
    return "{:,.2f}".format(value)


@jinja2.environmentfilter
def format_affiliate_url(environ, asin, page='offer'):
    """Get the affiliate URL for an item offer or detail page."""

    url = {
        'offer': 'https://www.amazon.com/gp/offer-listing/{}/',
        'detail': 'https://www.amazon.com/dp/{}/'
    }[page].format(asin)
    tag = environ.globals.get('AWS_ASSOCIATE_ID', '')
    return '{}?{}'.format(url, urllib.parse.urlencode({'tag': tag}))


@jinja2.environmentfilter
def format_affiliate_link(environ, asin, text='', page='offer'):
    """Build an affiliate link as text or with an image."""

    tag = environ.globals.get('AWS_ASSOCIATE_ID', '')
    url = format_affiliate_url(environ, asin, page=page)
    classes = ['affiliate', ]
    if not text:
        src = '//ws-na.amazon-adsystem.com/widgets/q?' + urllib.parse.urlencode({
            '_encoding': 'UTF8',
            'MarketPlace': 'US',
            'ASIN': asin,
            'ServiceVersion': '20070822',
            'ID': 'AsinImage',
            'WS': '1',
            'Format': '_SL160_',
            'tag': tag,
        })
        text = '<img border="0" src="{src}" >'.format(src=src)
        classes.append('image')
    pixel_src = '//ir-na.amazon-adsystem.com/e/ir?' + urllib.parse.urlencode({
        't': tag,
        'l': 'am2',
        'o': '1',
        'a': asin
    })
    pixel = ('<img src="{src}" width="1" height="1" border="0" alt=""' +
             'style="border:none !important; margin:0px !important;" />').format(src=pixel_src)
    return jinja2.Markup('<a class="{classes}" target="_blank" rel="noopener" href="{href}">{text}</a>{pixel}'.format(
        href=url, text=text, pixel=pixel, classes=' '.join(classes)))


async def error_middleware(app, handler):
    async def middleware_handler(request):
        try:
            return await handler(request)
        except web.HTTPException as ex:
            if ex.status == 404:
                response = aiohttp_jinja2.render_template('404.html', request, {})
                response.set_status(404)
                return response
            raise
    return middleware_handler


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = web.Application(loop=loop, middlewares=[error_middleware])
    app['base_dir'] = os.path.dirname(os.path.abspath(__file__))
    app['redis'] = redis.from_url(url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
    app['AWS_ASSOCIATE_ID'] = os.environ.get('AWS_ASSOCIATE_ID', '')
    app['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID', '')
    app['AWS_SECRET_KEY'] = os.environ.get('AWS_SECRET_KEY', '')
    setup_routes(app)
    env = aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(os.path.join(app['base_dir'], 'templates')))
    env.globals['GA_TRACKING_ID'] = os.environ.get('GA_TRACKING_ID', '')
    env.globals['AWS_ASSOCIATE_ID'] = app['AWS_ASSOCIATE_ID']
    env.globals['AWS_ACCESS_KEY_ID'] = app['AWS_ACCESS_KEY_ID']
    env.filters['currency'] = format_currency
    env.filters['affiliate_link'] = format_affiliate_link
    env.filters['affiliate_url'] = format_affiliate_url
    web.run_app(app, port=int(os.environ.get('PORT', '8080')))
