import urllib
import urllib.request
from lib.html import HTMLTableParser

turl = 'http://app.quotemedia.com/quotetools/optionModule.go?&webmasterId=90423&showLast=no&formInput=false&toolWidth=630&editSymbol=no&targetsym=true&chhig=152&dji=rt&action=showOption&symbol=scco&&targetURL='
turl += urllib.request.quote('http://www.nasdaq.com/aspxcontent/options2.aspx?symbol=scco&selected=scco')
qurl = 'http://app.quotemedia.com/quotetools/optionModule.go?&webmasterId=90423&showLast=no&formInput=false&toolWidth=630&editSymbol=no&targetsym=true&chhig=152&dji=rt&action=showOption&symbol=scco&&targetURL=http%3A//www.nasdaq.com/aspxcontent/options2.aspx%3Fsymbol%3Dscco%26selected%3Dscco'

theaders = {
    'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:6.0) Gecko/20100101 Firefox/6.0',
    'Accept':'*/*',
    'Accept-Language':'en-us,en;q=0.5',
    'Accept-Encoding':'gzip,deflate',
    'Accept-Charset':"'utf-8';q=0.7,*;q=0.7",
    'DNT':'1',
    'Connection':'keep-alive',
    'Referer':'http://www.nasdaq.com/aspxcontent/options.aspx?symbol=scco&selected=scco',
    'Cookie':'JSESSIONID=e00FoCfJRQP4',
    'Cache-Control':'max-age=0'
        }

def get_url(url):
    http = urllib.request.Request(url=url,headers=theaders)
    html = urllib.request.urlopen(http).read().decode('utf-8')
    print(html)
    parser = HTMLTableParser()
    parser.feed(html)
    parser.close()
    return parser

