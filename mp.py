import numpy as np
import urllib.request
from lib.html import HTMLTableParser
from datetime import date

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
           calls.append(sum([ (p-v)*oc['open int'][i] 
                    for i,v in enumerate(ocs) if p > v]))
           puts.append(sum([ (v-p)*op['open int'][i]
                    for i,v in enumerate(ops) if p < v]))
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
        # print('mmult',C)
        maxgain = -C[1]/(2*C[2])
        out['max pain'] = maxgain
        return out

    def get(self,symbol,mm,yy):
        url = 'http://finance.yahoo.com/q/op?s={0}&m={1}-{2:02d}'
        url = url.format(symbol,yy,mm)
        out = {}
        try:
            http = urllib.request.urlopen(url)
            html = http.read().decode('utf-8')
            out = self._parse_html(html)
            self._value_options(out)
            self._max_gain(out)
        except:   
            out['max pain'] = None

        out['symbol'] = symbol 
        return out

def dumphtml(self,tables):
    keys = sorted(map(lambda n: int(n[5:]),
        filter(lambda o: 'table' == o[0:5], tables.keys())))
    for k in keys:
        print('Table ',k)
        print(tables['table'+str(k)])

def fmt_ptable(v):
    return str(v)

def ptable(table,keys=None):
    if keys == None:
        keys = table.keys()
    print('\t'.join(keys))
    for i in range(len(list(table.values())[0])):
        print('\t'.join(map(lambda n: fmt_ptable(table[n][i]),keys)))

def dump(x):
    print('CALLS')
    ptable(x['calls'],sorted(filter(lambda n: n != 'symbol',x['calls'].keys())))
    print('\nPUTS')
    ptable(x['puts'],sorted(filter(lambda n: n != 'symbol',x['puts'].keys())))
    print('\nVALUATION')
    ptable(x['value'])
    print('\nSUMMARY\n{1}\tLast: ${2:5.2f}\tExpire: {3}\n{0}\t Max Pain ${4:5.2f}'.format(
        x['symbol'],x['desc'],x['last'],x['expire'],x['max pain']))

def do(sym,mm=11,yy=2011):
    return YahooOptions().get(sym,mm,yy)

def getDateRange(months):
    today = date.today()
    out = []
    for dm in range(months + 1):
        mm = (today.month + dm) % 12
        yy = today.year + (today.month + dm) // 12
        if mm == 0:
            mm = 12
            yy -=1
        out.append( tuple([mm,yy]) )
    return out


def do3(sym,months):
    out = []
    sym = sym.upper()
    for dm in getDateRange(months):
        mm = dm[0]
        yy = dm[1]
        x = YahooOptions().get(sym,mm,yy)
        mp = x['max pain']
        mps = "N/A"
        volc = 1
        volp = -1
        if mp != None:
            mps = '${0:5.2f}'.format(mp)
            volc = sum(x['calls']['open int'])
            volp = sum(x['puts']['open int'])
        url = 'http://finance.yahoo.com/q/op?s={0}&m={1}-{2:02d}'
        print('\t'.join(map(str,[sym, '{0:02d}/{1}'.format(mm,yy),
                        mps,
                        volp+volc,
                        '{0:5.2f}'.format(volp/volc)])))
        if mp != None:
            out.append( x['max pain'] )
        else:
            out.append( 0.0 )
    return out

def do4(symbols="XLK,XLB,XLE,XLI,XLF,XHB,XLV,XLU,XLP,SPY",months=12):
    syms = list(map(lambda s: s.strip(),symbols.split(",")))
    dates = getDateRange(months)
    mptable = []
    for sym in syms:
        mps = []
        for date in dates:
            x = YahooOptions().get(sym,date[0],date[1])
            mp = x['max pain']
            if mp == None:
                mp = 0.0
            print("- {0}\t{1}/{2}\t{3:2.2f}".format(sym,date[0],date[1],mp))
            mps.append(mp)
        mptable.append(mps)
    print("\t","\t".join(map(lambda d: "{0}/{1}".format(d[0],d[1]),dates)))
    for i in range(len(syms)):
        print("\t".join([ syms[i].upper() ] +
                        list(map(lambda mp: '{0:2.2f}'.format(mp), mptable[i]))))

def do5(symbols='vnq,t,nly,agnc,cb,cop,dvn,dd,f,fcx,hd,ews,line,nat,tbt,vz,wy,upl,hp,jjc',months=12):
    syms = list(map(lambda s: s.strip(),symbols.split(",")))
    dates = getDateRange(months)
    mptable = []
    for sym in syms:
        mps = []
        for date in dates:
            x = YahooOptions().get(sym,date[0],date[1])
            mp = x['max pain']
            if mp == None:
                mp = 0.0
            print("- {0}\t{1}/{2}\t{3:2.2f}".format(sym,date[0],date[1],mp))
            mps.append(mp)
        mptable.append(mps)
    print("\t","\t".join(map(lambda d: "{0}/{1}".format(d[0],d[1]),dates)))
    for i in range(len(syms)):
        print("\t".join([ syms[i].upper() ] +
                        list(map(lambda mp: '{0:2.2f}'.format(mp), mptable[i]))))
