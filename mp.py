import urllib.request
from lib.html import HTMLTableParser
def fmt_price(s):
    try:
        return float(s.replace(",",""))
    except:
        return 0.0

def fmt_int(s):
    return int(s.replace(",",""))

OPTFMT = {'symbol': str, 'chg': None, 'vol': fmt_int, 'open int': fmt_int}
def parse_strike_table(tbl):
    out = {}
    for i in range(len(tbl[0])):
        key = tbl[0][i].lower()
        fmt = fmt_price 
        if key not in OPTFMT or OPTFMT[key]:
            if key in OPTFMT:
                fmt = OPTFMT[key]
            out[key] = list()
            for j in range(1,len(tbl)):
                out[key].append(fmt(tbl[j][i]))
    return out

def parse_options(html):
    out = {}
    parser = HTMLTableParser()
    parser.feed(html)
    parser.close()
    p = parser.out
    #out['tables'] = p
    out['desc'] = p['table4'][0][0]
    last = p['table4'][0][1]
    p1 = 2 + last.index(':',5)
    p2 = last.index(' ',p1)
    out['last'] = float(last[p1:p2])
    out['expire'] = p['table9'][0][1][16:]
    out['calls'] = parse_strike_table(p['table11'])
    out['puts'] = parse_strike_table(p['table15'])
    return out

def get_options(symbol,mm,yy):
    url = 'http://finance.yahoo.com/q/op?s={0}&m={1}-{2:02d}'
    url = url.format(symbol,yy,mm)
    http = urllib.request.urlopen(url)
    html = http.read().decode('utf-8')
    out = parse_options(html)
    out['symbol'] = symbol
    return out

def do(sym):
    return get_options(sym,9,2011)
    
def dump(tables):
    keys = sorted(map(lambda n: int(n[5:]),filter(lambda o: 'table' == o[0:5],
        tables.keys())))
    for k in keys:
        print('Table ',k)
        print(tables['table'+str(k)])

r = do('dd')
