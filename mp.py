import numpy as np
import urllib.request
from lib.html import HTMLTableParser

def fmt_price(s):
    try:
        return float(s.replace(",",""))
    except:
        return 0.0

def fmt_int(s):
    return int(s.replace(",",""))

OPTFMT = { 
        'symbol': str, 
        'chg': None, 
        'vol': fmt_int, 
        'open int': fmt_int
        }
 
class YahooOptions():
    def __init__(self):
        pass

    def _parse_strike_table(self,tbl):
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

    def _parse_html(self,html):
        out = {}
        parser = HTMLTableParser()
        parser.feed(html)
        parser.close()
        p = parser.out
        #out['tables'] = p
        out['desc'] = p['table4'][0][0]
        last = p['table4'][0][1]
        p1 = 2 + last.index(':',6)
        p2 = last.index(' ',p1)
        #print(last)
        out['last'] = float(last[p1:p2])
        expire = p['table9'][0][1]
        p1 = 2 + expire.index(',',16)
        out['expire'] = expire[p1:]
        out['calls'] = self._parse_strike_table(p['table11'])
        out['puts'] = self._parse_strike_table(p['table15'])
        return out

    def _value_options(self,out):
        oc = out['calls']
        op = out['puts']
        ocs = oc['strike']
        ops = op['strike']
        prices = sorted(list(set(ocs).union(ops)))
        calls = []
        puts = []
        totals = []
        for p in prices:
           calls.append(sum([ (v-p)*oc['open int'][i] 
                    for i,v in enumerate(ocs) if v > p]))
           puts.append(sum([ (p-v)*op['open int'][i]
                    for i,v in enumerate(ops) if v < p]))
           totals.append(calls[-1]+puts[-1])
        out['value'] = {'prices': prices, 'calls': calls, 
                        'puts': puts, 'totals': totals }
        return out

    def _max_gain(self,out):
        totals = out['value']['totals']
        prices = out['value']['prices']

        imin = totals.index(min(totals))
        p1 = imin - 3
        p2 = imin + 4
        P = [sum(map(lambda n: n**p, prices[p1:p2])) for p in range(5)]
        bs = [sum([ v*(prices[i]**p)  for i,v in enumerate(totals) 
                        if p1 <= i < p2]) for p in range(3)] 
        mA = np.matrix([P[0:3],P[1:4],P[2:5]]) 
        mB = np.matrix([bs]).transpose()
        C = list((mA.getI()*mB).getA1())
        maxgain = -C[1]/(2*C[2])
        out['max pain'] = maxgain
        return out

    def get(self,symbol,mm,yy):
        url = 'http://finance.yahoo.com/q/op?s={0}&m={1}-{2:02d}'
        url = url.format(symbol,yy,mm)
        http = urllib.request.urlopen(url)
        html = http.read().decode('utf-8')
        out = self._parse_html(html)
        out['symbol'] = symbol
        self._value_options(out)
        self._max_gain(out)
        return out

    def dump(self,tables):
        keys = sorted(map(lambda n: int(n[5:]),
            filter(lambda o: 'table' == o[0:5], tables.keys())))
        for k in keys:
            print('Table ',k)
            print(tables['table'+str(k)])

def do(sym):
    return YahooOptions().get(sym,9,2011)

def do2():
    for i in range(1,13):
        t = YahooOptions().get('AAPL',i,2012)
        print(i,len(t['calls']['last']))
