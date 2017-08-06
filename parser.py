import re


PTCGO_MAPPING = {
    'HS': 'hgss1',
    'UL': 'hgss2',
    'UD': 'hgss3',
    'TM': 'hgss4',
    'CL': 'col1',
    'PR-BLW': 'bwp',
    'BWP': 'bwp',
    'BLW': 'bw1',
    'EPO': 'bw2',
    'NVI': 'bw3',
    'NXD': 'bw4',
    'DEX': 'bw5',
    'DRX': 'bw6',
    'DRV': 'dv1',
    'BCR': 'bw7',
    'PLS': 'bw8',
    'PLF': 'bw9',
    'PLB': 'bw10',
    'PR-XY': 'xyp',
    'XYP': 'xyp',
    'LTR': 'bw11',
    'KSS': 'xy0',
    'XY': 'xy1',
    'FLF': 'xy2',
    'FFI': 'xy3',
    'PHF': 'xy4',
    'PRC': 'xy5',
    'DCR': 'dc1',
    'ROS': 'xy6',
    'AOR': 'xy7',
    'BKT': 'xy8',
    'BKP': 'xy9',
    'GEN': 'g1',
    'FAC': 'xy10',
    'STS': 'xy11',
    'EVO': 'xy12',
    'SUM': 'sm1',
    'SM': 'sm1',
    'GRI': 'sm2',
    'GUR': 'sm2',
    'PR-SM': 'smp',
    'SMP': 'smp',
    'BUS': 'sm3',
}


PROMO_MAPPING = {
    'XY': 'xyp',
    'BW': 'bwp',
    'SM': 'smp',
}


LINE_RE = re.compile(
    '(?P<quantity>\d{1,2})\s'
    '(?P<name>.*)\s'
    '((?P<set>[-a-zA-Z]{2,6})\s(?P<number>\d{1,3})|'
    '(?P<promo>(?P<series>[a-zA-Z]{2})\d{1,3}))')

PARTIAL_RE = re.compile(
    '(?P<quantity>\d{1,2})\s'
    '(?P<name>\S+.*)')


def parse_deck_list(deck):
    """Parse string which looks like a decklist into a list of dicts."""
    results = []
    for line in deck.split('\n'):
        match = LINE_RE.search(line)
        if match is not None:
            result = match.groupdict()
            if result.get('set') is not None:
                result['id'] = '{}-{}'.format(
                    PTCGO_MAPPING.get(result['set'].upper(), ''), result['number'])
            else:
                result['id'] = '{}-{}'.format(
                    PROMO_MAPPING.get(result['series'].upper(), ''), result['promo'].upper())
            results.append(result)
        else:
            partial = PARTIAL_RE.match(line)
            if partial is not None:
                results.append(partial.groupdict())
    return results
