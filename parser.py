import re


PTCGO_MAPPING = {
    'HS': 'hgss1',
    'UL': 'hgss2',
    'UD': 'hgss3',
    'TM': 'hgss4',
    'CL': 'col1',
    'PR-BLW': 'bwp',
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
}


LINE_RE = re.compile(
    '(?P<quantity>\d{1,2})\s'
    '(?P<name>.*)\s'
    '(?P<set>[-A-Z]{2,6})\s'
    '(?P<number>\d{1,3})')


def parse_deck_list(deck):
    """Parse string which looks like a decklist into a list of dicts."""
    results = []
    for line in deck.split('\n'):
        match = LINE_RE.search(line)
        if match is not None:
            result = match.groupdict()
            result['id'] = '{}-{}'.format(
                PTCGO_MAPPING.get(result['set'], ''), result['number'])
            results.append(result)
    return results

# total = 0
# unique = 0
# with open('decklist.txt', 'r') as f:
#     for line in f.readlines():
#         match = LINE_RE.search(line)
#         if match is not None:
#             result = match.groupdict()
#             print(result)
#             total += int(result['quantity'])
#             unique += 1

# print(total)
# print(unique)
