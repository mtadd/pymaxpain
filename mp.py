import urllib.request
from html.parser import HTMLParser

class YahooOptionsParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self,strict=False)
        self.cTable = 0
        self.intable = False        
        self.out = {}
        self.inrow = False
        self.intd = False
        self.data = ''
        self.tkey = ''
        self.out['self'] = self
        self.out['data'] = ''
        self.out['d'] = ''
        self.out['tags'] = set() 
        self.out['steps'] = []
        
    def handle_starttag(self,tag,attrs):
        self.out['steps'].append( ('start',tag,attrs) )
        tag = tag.lower()
        self.out['tags'].add(tag)
        if tag == 'table':
            self.cTable = self.cTable + 1
            self.intable = True
            self.tkey = tag + str(self.cTable)
            self.out[self.tkey] = list()
        if tag == 'tr' or tag == 'th':
            self.inrow = True
            self.out[self.tkey].append(list())
        if tag == 'td':
            self.intd = True
            self.data = ''

    def handle_startendtag(self,tag,attrs):
        self.out['steps'].append( ('startend',tag,attrs) )

    def handle_endtag(self,tag):
        self.out['steps'].append( ('end',tag) )
        tag = tag.lower()
        if tag == 'table':
            self.intable = False
        if tag == 'tr' or tag == 'th':
            if self.intable:
                self.inrow = False
        if tag == 'td':
            #if self.inrow:
            self.out[self.tkey][-1].append(self.data)
            self.intd = False

    def handle_data(self,data):
        self.out['steps'].append( ('data',data) )
#        self.out['d'] += data
        if self.intd:
            self.out['data'] += data
            self.data += data

def get_options(symbol,mm,yy):
    url = 'http://finance.yahoo.com/q/os?s=' + symbol + '&m=' + yy + '-' + mm
    print('url ',url)
    http = urllib.request.urlopen(url)
    html = http.read().decode('utf-8')
#    print('html len ',len(html))
    print(html)
    parser = YahooOptionsParser()
    parser.feed(html)
    parser.close()
    parser.out['html'] = html
    return parser.out

def do(sym):
    return get_options(sym,'2011','08')
    
r = do('dd')
