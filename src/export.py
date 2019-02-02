import os

import redis
import requests


def main():
    client = redis.from_url(url=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))

    with requests.Session() as session:
        params = {'expandedLegal': 'true'}
        sets = session.get(url='https://api.pokemontcg.io/v1/sets', params=params).json()
        codes = [s['code'] for s in sets['sets']]

    with open('redis.txt', 'w') as r:
        with open('missing.txt', 'w') as missing:
            for result in client.scan_iter(count=1000):
                key = result.decode('utf-8')
                code = key.split('-')[0]
                if code in codes:
                    asin, url = client.hmget(key, ['asin', 'url'])
                    if asin:
                        asin, url = asin.decode('utf-8'), url.decode('utf-8')
                        r.write('HMSET {} asin "{}" url "{}"\n'.format(key, asin, url))
                    else:
                        missing.write(key + '\n')

if __name__ == '__main__':
    main()
