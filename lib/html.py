from lib.parser import HTMLParser

class HTMLTableParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self,strict=False)
        self.cTable = 0
        self.out = {}
        self.intable = False        
        self.inrow = False
        self.intd = False
        self.tkey = ''
        self.out['data'] = ''
        #self.out['steps'] = []

    def handle_starttag(self,tag,attrs):
        #self.out['steps'].append( ('start',tag,attrs) )
        tag = tag.lower()
        if tag == 'table':
            self.cTable = self.cTable + 1
            self.intable = True
            self.tkey = tag + str(self.cTable)
            self.out[self.tkey] = list()
        if tag == 'tr':
            self.inrow = True
            self.out[self.tkey].append(list())
        if tag == 'td' or tag == 'th':
            self.intd = True
            self.innerText = ''

    def handle_startendtag(self,tag,attrs):
        #self.out['steps'].append( ('startend',tag,attrs) )
        pass

    def handle_endtag(self,tag):
        #self.out['steps'].append( ('end',tag) )
        tag = tag.lower()
        if tag == 'table':
            self.intable = False
        if tag == 'tr': 
            self.inrow = False
        if tag == 'td' or tag == 'th':
            if self.inrow:
                self.out[self.tkey][-1].append(self.innerText)
                self.intd = False

    def handle_data(self,data):
        #self.out['steps'].append( ('data',data) )
        if self.intd:
            self.innerText += data 
    
    def dump(self,tables=None):
        if tables == None:
            tables = self.out
        keys = sorted( map(lambda n: int(n[5:]),
            filter(lambda o: 'table' == o[0:5], tables.keys()) ) )
        for k in keys:
            print('Table ',k)
            print(tables['table'+str(k)])

if __name__ == '__main__':
    import urllib.request
    http = urllib.request.urlopen('http://www.google.com/')
    html = http.read().decode('utf-8')
    parser = HTMLTableParser()
    parser.feed(html)
    parser.close()
    parser.dump(parser.out)
    
