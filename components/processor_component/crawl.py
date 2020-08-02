import requests, os
import _thread
from bs4 import BeautifulSoup

prefix_img_local = "/ffbo.neuronlp/img/flycircuit/"
prefix_img_to_frontend = "/img/flycircuit/"

def clean(s):
    return ' '.join(s.split())

def extract(s):
    js = {}
    js['Name'] = s.split('[')[0]
    s = s.split('[')[1].rstrip(']')
    for si in s.split(','):
        k, v = si.split(':')
        js[clean(k)] = clean(v)
    return js

def fetch_image(img_src):
    img_pathname = prefix_img_local + img_src.split('/')[-1]
    if os.path.isfile(img_pathname):
        return
    response = requests.get(img_src)
    if response.status_code == 200:
        with open(img_pathname, 'wb') as f:
            f.write(response.content)

class FlyCircuitDB(object):
    def __init__(self):
        self.flycircuit_cache = {}


    def parse_neuron(self, neuron):
        # check if neuron is cached
        if neuron in self.flycircuit_cache:
            return self.flycircuit_cache[neuron]

        url = 'http://flycircuit.tw/modules.php?name=clearpage&op=detail_table&neuron=' + neuron
        req = requests.get(url, timeout = 8.0)
        req.raise_for_status()
        soup = BeautifulSoup(req.text, 'html.parser')
        tds = soup.find_all('td')

        js = {}

        for i in range(2, 22, 2):
            js[clean(tds[i].text)] = clean(tds[i+1].text)

        # clean 'Soma Coordinate'
        xyz = []
        for item in js['Soma Coordinate'].split(','):
            k, v = item.split(':')
            xyz.append( str(clean(k)) + ': ' + str(int(clean(v))) )
        js['Soma Coordinate'] = ', '.join(xyz)

        # Image
        js['Images'] = {}
        for i in range(22, 22+2):
            img_src = "http://flycircuit.tw" + tds[i+3].find('a', href=True).get('href')
            _thread.start_new_thread(fetch_image, (img_src,))
            js['Images'][clean(tds[i].text)] = prefix_img_to_frontend + img_src.split('/')[-1]

        # Spatial Distribution
        js['Spatial Distribution'] = [int(x) for x in tds[29].img.get('src').split('=')[-1].split('_')]

        # Similar neurons
        js['Similar neurons'] = []
        for i in range(38, 38+4):
            meta = extract(clean(tds[i].text))
            meta['img'] = tds[i+4].find('a', href=True).get('href')
            js['Similar neurons'].append(meta)

        # Cell body neighborhood
        #js['Cell body neighborhood'] = []
        #for i in range(44, 44+4):
        #    meta = extract(clean(tds[i].text))
        #    meta['img'] = tds[i+4].find('a', href=True).get('href')
        #    js['Cell body neighborhood'].append(meta)

        self.flycircuit_cache[neuron] = js
        return js
