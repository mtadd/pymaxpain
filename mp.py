import numpy                           #matrix / linear algebra operations
import urllib.request                  #http / network
import json
import sys
import itertools
import operator
from lib.html import HTMLTableParser   #see lib\html.py
from datetime import date              #calendar arithmetic
import threading

def fmt_price(s):
    try:
        return float(s.replace(",",""))
    except:
        return 0.0

def fmt_int(s):
    try:
        return int(s.replace(",",""))
    except:
        return 0

def fmt_volume(v):
    if v >= 10**9:
        return '{0}B'.format(v//10**9)
    elif v >= 10**6:
        return '{0}M'.format(v//10**6)
    elif v >= 10**3:
        return '{0}k'.format(v//10**3)
    else:
        return str(v)

OPTFMT = { 
        'symbol': str, 
        'chg': None, 
        'vol': fmt_int, 
        'open int': fmt_int
        }

YQLKEYMAP = { 
    'strikePrice': 'strike', 
    'lastPrice': 'last',
    'symbol': 'symbol', 
    'bid': 'bid', 
    'ask': 'ask',
    'openInt': 'open int', 
    'vol': 'vol'
    }
 

class YahooOptions():
    """Library for getting stock options from Yahoo. 
    """
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

    def _parse_json_option_chain(self,chain):
        out = {}
        out['desc'] = chain['symbol']
        out['symbol'] = chain['symbol']
        out['last'] = 0
        out['expire'] = chain['expiration']
        out['calls'] = {} 
        out['puts'] = {} 
        for key in YQLKEYMAP.values():
            out['calls'][key] = list()
            out['puts'][key] = list()
        for opt in chain['option']:
            t = ('calls','puts')[ opt["type"] == "P" ]
            for key,val in YQLKEYMAP.items():
                fmt = fmt_price
                if val in OPTFMT:
                    fmt = OPTFMT[val]
                out[t][val].append(fmt(opt[key]))
        return out
 
    def _parse_json(self,jsin):
        count = jsin['query']['count']
        chain = jsin['query']['results']['optionsChain']
        if count == 1:
            return self._parse_json_option_chain(chain)
        else:
            return list(map(lambda c: self._parse_json_option_chain(c),chain))
   
    def _get_data_from_html(self):
        url = 'http://finance.yahoo.com/q/op?s={0}&m={1}-{2:02d}'
        url = url.format(self.symbol,self.yyyy,self.mm)
        http = urllib.request.urlopen(url)
        html = http.read().decode('utf-8')
        return self._parse_html(html)

    def _get_data_from_yql(self):
        if type(self.symbol) == list:
            url = "http://query.yahooapis.com/v1/public/yql?q=SELECT%20*%20FROM%20yahoo.finance.options%20WHERE%20symbol%20in%20({0})%20AND%20expiration%3D'{1}-{2:02d}'&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys"
            url = url.format(','.join(map(lambda s: "'"+s+"'",self.symbol)),
                             self.yyyy,self.mm)
        else:
            url = "http://query.yahooapis.com/v1/public/yql?q=SELECT%20*%20FROM%20yahoo.finance.options%20WHERE%20symbol%3D'{0}'%20AND%20expiration%3D'{1}-{2:02d}'&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys"
            url = url.format(self.symbol,self.yyyy,self.mm)
        print(url)
        http = urllib.request.urlopen(url)
        resp = http.read().decode('utf-8')
        return self._parse_json(json.loads(resp))
 
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
        mA = numpy.matrix([P[0:3],P[1:4],P[2:5]]) 
        mB = numpy.matrix([bs]).transpose()
        C = list((mA.getI()*mB).getA1())
        # print('mmult',C)
        maxgain = -C[1]/(2*C[2])
        out['max pain'] = maxgain
        return out

    def get_contracts(self,symbol):
        if type(symbol) is list:
            url = "http://query.yahooapis.com/v1/public/yql?q=SELECT%20*%20FROM%20yahoo.finance.option_contracts%20WHERE%20symbol%20in%20({0})&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys"
            url = url.format(','.join(map(lambda s: "'"+s+"'",symbol)))
        else:
            url = "http://query.yahooapis.com/v1/public/yql?q=SELECT%20*%20FROM%20yahoo.finance.option_contracts%20WHERE%20symbol%3D'{0}'&format=json&env=store%3A%2F%2Fdatatables.org%2Falltableswithkeys"
            url = url.format(symbol)

        print(url)
        http = urllib.request.urlopen(url)
        resp = http.read().decode('utf-8')
        obj = json.loads(resp)['query']['results']['option']

        def fmt_date(s):
            return tuple(map(int,reversed(s.split('-'))))

        if type(symbol) is list:
            out = {}
            for opt in obj:
                out[opt['symbol']] = list(map(fmt_date, opt['contract']))
            return out
        else:
            return list(map( fmt_date, obj['contract']))
        
    def get(self,symbol,mm,yyyy):
        """
        """
        self.mm = mm
        self.yyyy = yyyy
        self.symbol = symbol
        out = {}
        try:
            if type(symbol) == list:
                out = self._get_data_from_yql()
                for o in out:
                    self._value_options(o)
                    try:
                        self._max_gain(o)
                    except numpy.linalg.linalg.LinAlgError:
                        o['max pain'] = None
            else:
                out = self._get_data_from_html()
                self._value_options(out)
                try:
                    self._max_gain(out)
                except numpy.linalg.linalg.LinAlgError:
                    out['max pain'] = None
                    
        except KeyboardInterrupt:
            raise 
        except:   
            print('YahooOptions.get error ',sys.exc_info()[0])
            #raise

        if type(symbol) != list:        
            out['symbol'] = symbol 
            if 'max pain' not in out:
                out['max pain'] = None

        self.out = out
        return out

    @staticmethod
    def _async_get_thread(self,symbol,mm,yyyy,limiter):
        if limiter: 
            limiter.acquire()
        self.out = {}
        try:
           self.out = self.get(symbol,mm,yyyy)
           print('YahooOptions.async_get ',symbol,mm,yyyy)
        finally:
            if limiter: 
                limiter.release()

    def async_get(self,symbol,mm,yyyy,limiter):
        self.thread = threading.Thread(
                        target=self._async_get_thread,
                        args=(self,symbol,mm,yyyy,limiter))
        self.thread.start()
        return self 



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

def do(sym='GOOG',mm=12,yy=2011):
    return YahooOptions().get(sym,mm,yy)

def do2(sym='GOOG'):
    return YahooOptions().get_contracts(sym)

def do2a(sym=["GOOG","YHOO"]):
    return YahooOptions().get_contracts(sym)

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


def do3_dump(sym,xs):
    print('\t'.join(["SYM","DATE","MP","VOL","PUTS/CALLS"]))
    for x in xs:
        mm = x.mm 
        yy = x.yyyy 
        mp = x.out['max pain']
        mps = ""
        vols = ""
        volr = ""
        volc = 1
        volp = -1
        if mp != None:
            mps = '${0:5.2f}'.format(mp)
            volc = sum(x.out['calls']['open int'])
            volp = sum(x.out['puts']['open int'])
            vols = volc+volp
            volr = '{0:5.2f}'.format(volp/volc)

        url = 'http://finance.yahoo.com/q/op?s={0}&m={1}-{2:02d}'
        print('\t'.join(map(str,[sym, '{0:02d}/{1}'.format(mm,yy),
                        mps, vols, volr])))

def do3(sym,months=12):
    sym = sym.upper()
    limiter = threading.BoundedSemaphore(4)
    xs = []
    for dm in getDateRange(months):
        xs.append(YahooOptions().async_get(sym,dm[0],dm[1],limiter))
    for x in xs:
        x.thread.join()
    do3_dump(sym,xs)

def do3a(sym='GOOG'):
    sym = sym.upper()
    limiter = threading.BoundedSemaphore(4)
    xs = []
    for dm in do2a(sym):
        xs.append(YahooOptions().async_get(sym,dm[0],dm[1],limiter))
    for x in xs:
        x.thread.join()
    do3_dump(sym,xs)

def do4(symbols="XLK,XLB,XLE,XLI,XLF,XHB,XLV,XLU,XLP,SPY",months=12):
    syms = list(map(lambda s: s.strip(),symbols.split(",")))
    dates = getDateRange(months)
    limiter = threading.BoundedSemaphore(4)
    threads = []
    mptable = []
    for sym in syms:
        mps = [] 
        for date in dates:
            t = YahooOptions().async_get(sym,date[0],date[1],limiter)
            mps.append(t)
            threads.append(t.thread)
        mptable.append(mps) 

    for t in threads:
        t.join()

    for xsyms in mptable:
        for x in xsyms:
            x.mp = x.out['max pain']
            if x.mp == None:
                x.mp = 0.0

    print(" \t" + "\t".join(map(lambda d: "{0}/{1:02d}".format(d[0],d[1] % 100),dates)))
    for i in range(len(syms)):
        print("\t".join([ syms[i].upper() ] +
                        list(map(lambda x: '{0:2.2f}'.format(x.mp), mptable[i]))))

def do4a(symbols="XLK,XLB,XLE,XLI,XLF,XHB,XLV,XLU,XLP,SPY",months=6):
    syms = list(map(lambda s: s.strip(),symbols.split(",")))
    contracts = YahooOptions().get_contracts(syms)
    dtmap = {}
    for sym,sym_dates in contracts.items():
        for dt in sym_dates:
            if dt not in dtmap:
                dtmap[dt] = [] 
            dtmap[dt].append(sym)
    limiter = threading.BoundedSemaphore(4)
    dates = list(filter(lambda dt: dt in dtmap,getDateRange(months)))
    threads = [ YahooOptions().async_get(dtmap[dt],dt[0],dt[1],limiter)
                for dt in dates ]
    [t.thread.join() for t in threads]
    
    mptable = []
    for sym in syms:
        mps = []
        for t in threads:
            out = None
            for tout in t.out:
                if sym == tout['symbol']:
                    out = tout
                    break
            mps.append(out)
        mptable.append(mps)

    print(" \t" + "\t".join(map(lambda d: "{0}/{1:02d} P/C".format(d[0],d[1] % 100),dates)))
    for i in range(len(syms)):
        s = syms[i].upper() + "\t"
        for x in mptable[i]:
            if x != None and 'max pain' in x and x['max pain'] != None:
                    s += '{0:2.2f}'.format(x['max pain'])
                    s += " "
                    s += fmt_volume( sum(x['puts']['open int']) )
                    s += "/"
                    s += fmt_volume( sum(x['calls']['open int']) )
            else:
                s += 10*" " 
            s += "\t"
        print(s)


def do5(symbols='vnq,t,nly,agnc,cb,cop,dvn,dd,f,fcx,hd,ews,line,nat,tbt,vz,wy,upl,hp,jjc',months=3):
    do4a(symbols,months)

