import base64
import hashlib
import hmac
import os
import queue
import re
import time
import urllib.parse

import requests

from jellyfish import jaro_winkler
from lxml import etree


def signed_parameters(method, url, params, secret):
    """Returns a new list of query parameters including a signature for the AWS requests."""
    query = [(k, v) for k, v in params.items()]
    query.sort(key=lambda tup: tup[0])
    parsed = urllib.parse.urlparse(url)
    text = '{method}\n{host}\n{path}\n{query}'.format(
        method=method.upper(),
        host=parsed.netloc,
        path=parsed.path,
        query=urllib.parse.urlencode(query, safe='~', quote_via=urllib.parse.quote))
    signature = base64.b64encode(
        hmac.new(secret.encode('utf-8'), text.encode('utf-8'), digestmod=hashlib.sha256).digest())
    query.append(('Signature', signature.decode('utf-8')))
    return query


def parse_search_response(response_body):
    """Parse item info from the search response.

    Returns the ASIN and detail URL for each item."""
    results = []
    items = etree.fromstring(response_body).xpath('//*[local-name() = "Item"]')
    for index, item in enumerate(items):
        url = item.xpath('//*[local-name() = "DetailPageURL"]/text()')[index]
        asin = item.xpath('//*[local-name() = "ASIN"]/text()')[index]
        title = item.xpath('//*[local-name() = "Title"]/text()')[index]
        results.append({'url': url, 'asin': asin, 'title': title})
    return results


def prioritize_results(name, results):
    """Prioritize regular cards over holo/reverse holos and remove oversized results."""
    q = queue.PriorityQueue()
    for order, item in enumerate(results):
        title = item.get('title', '')
        priority = 1 - jaro_winkler(name, title)
        if 'REVERSE HOLO' in title.upper():
            priority += 0.5
        elif 'HOLO' in title.upper():
            priority += 1
        elif 'FULL ART' in title.upper():
            priority += 1.5
        elif title.endswith('Jumbo') or title.endswith('Oversized'):
            # Don't consider these cards as matches
            continue
        q.put((priority, order, item))
    return q


def get_amazon_info(card, session=None):
    """Search for card ASIN and link from Amazon's product API."""

    AWS_ASSOCIATE_ID = os.environ.get('AWS_ASSOCIATE_ID', '')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY', '')

    url = 'http://webservices.amazon.com/onca/xml'

    info = {}

    session = session or requests

    if AWS_ASSOCIATE_ID and AWS_ACCESS_KEY_ID and AWS_SECRET_KEY:
        title_formats = {
            'Black & White': 'Pokemon - {name} ({number}) - {set}',
            'XY': 'Pokemon - {name} ({setNumber}) - {set}',
            'Sun & Moon': 'Pokemon - {name} ({setNumber}) - {set}',
        }
        title_formats['BW'] = title_formats['Black & White']
        title = title_formats[card['series']].format(**card)
        # Adjust the names of Mega pokemon
        title = re.sub(r'^(M\s)(.*(-|\s)EX)', 'Mega \g<2>', title)
        params = {
            'Service': 'AWSECommerceService',
            'AWSAccessKeyId': AWS_ACCESS_KEY_ID,
            'AssociateTag': AWS_ASSOCIATE_ID,
            'Operation': 'ItemSearch',
            'Keywords': title,
            'SearchIndex': 'Toys',
            'ResponseGroup': 'Small',
            'Condition': 'New',
            'Timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'Version': '2013-08-01',
        }
        params = signed_parameters('get', url, params, AWS_SECRET_KEY)
        response = session.get(url, params=params)
        matches = parse_search_response(response.text)
        print('{} match(es) for {}'.format(len(matches), title))
        if matches:
            _priority, _order, info = prioritize_results(title, matches).get()
            print(info)
    return info


def parse_price_response(response_body):
    """Parse price response into mapping by ASIN."""

    results = {}
    batch = etree.fromstring(response_body).findall('{*}Items')
    for items in batch:
        for item in items.findall('{*}Item'):
            asin = item.find('{*}ASIN').text
            availability = int(item.find('{*}OfferSummary').find('{*}TotalNew').text)
            price = int(
                item.find('{*}Offers')
                .find('{*}Offer')
                .find('{*}OfferListing')
                .find('{*}Price')
                .find('{*}Amount').text) / 100.0
            results[asin] = {'price': price, 'available': availability}
    return results


async def get_amazon_prices(cards, session=None):
    """Get prices for all of the cards in the list."""

    AWS_ASSOCIATE_ID = os.environ.get('AWS_ASSOCIATE_ID', '')
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY', '')

    url = 'http://webservices.amazon.com/onca/xml'

    asins = [card['asin'] for card in cards if card.get('asin')]
    results = {}

    if AWS_ASSOCIATE_ID and AWS_ACCESS_KEY_ID and AWS_SECRET_KEY:
        while asins:
            current, asins = asins[:20], asins[20:]
            head, tail = current[:10], current[10:]
            params = {
                'Service': 'AWSECommerceService',
                'AWSAccessKeyId': AWS_ACCESS_KEY_ID,
                'AssociateTag': AWS_ASSOCIATE_ID,
                'Operation': 'ItemLookup',
                'ItemLookup.Shared.ItemType': 'ASIN',
                'ItemLookup.Shared.ResponseGroup': 'Offers',
                'ItemLookup.1.ItemId': ','.join(head),
                'ItemLookup.2.ItemId': ','.join(tail),
                'Timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'Version': '2013-08-01',
            }
            params = signed_parameters('get', url, params, AWS_SECRET_KEY)
            async with session.get(url, params=params) as response:
                text = await response.text()
                results.update(parse_price_response(text))
    return results
