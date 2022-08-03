import requests
from requests.exceptions import RequestException
import urllib.error
from contextlib import closing
from bs4 import BeautifulSoup
import subprocess
from time import sleep
from pathlib import Path

import re
### SCRAPING FUNCTIONS ####################################

class NoResponseError(Exception):
    pass

class NotFoundError(Exception):
    pass

REQUEST_ARGS = dict(
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'},
    # proxies = {'https': PROXY},
    # auth = requests.auth.HTTPProxyAuth(SECRETS["username"],SECRETS["password"]) # Your username and password for proxy authentication
)

def simple_get(url,args = REQUEST_ARGS):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(requests.get(url,**args)) as resp: #stream=True
            if is_good_response(resp):
                return resp
            elif resp.status_code == 404:
                print('404')
                raise NotFoundError()
            else:
                print('no response')
                return NoResponseError(f'HTTP status code: {resp.status_code}')

    except RequestException as e:
        log_error('Error during requests to {0} : {1}'.format(url, str(e)))
        return None



def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)


def log_error(e):
    """
    It is always a good idea to log errors. 
    This function just prints them, but you can
    make it do anything.
    """
    print(e)

class TagFetcher():
    
    ROOT_URL = 'https://imslp.org/'
    LOOKUP_URL = 'wiki/Special:ReverseLookup/'

    @classmethod
    def _get_html(cls,id):
        #beer_key = 1353
        #beer_key = 1471174 # 2509888
        response = simple_get(cls.ROOT_URL+cls.LOOKUP_URL+str(id))
        raw_html = response.content#.read()#.content

        print(response.url)

        if raw_html is None:
            return None
        #print(len(raw_html))
        html = BeautifulSoup(raw_html, 'html.parser')
        return(html)

    @classmethod
    def get_tags(cls,id):
        my_html = cls._get_html(id)

        tags = dict()
        my_text = my_html.find('h1',{'id':'firstHeading'}).text.strip().replace(')','').split('(')
        
        tags['Title'] = ' '.join(my_text[0:-1]).strip()
        tags['Author'] = my_text[-1].strip()

        return tags



class ScoreTagger():

    def __init__(self,path):
        self.path = Path(path)
        # self.tag_subfolders = tag_subfolders
        if not self.path.exists():
            raise FileNotFoundError()
        
    @staticmethod
    def tag_score(path):
        path = Path()/path
        if path.suffix != '.pdf':
            print("Non pdf path")
            return
        
        name = path.name
        pat = r"IMSLP[\d]+"

        id = int(re.search(pat,name).group(0).replace('IMSLP',''))
        tags = TagFetcher.get_tags(id)

        my_args = ['exiftool']

        for k,v in tags.items():
            my_args.append("-"+k+"="+v)

        my_args.append(str(path))
        my_args.append('-overwrite_original')

        print(tags)

        subprocess.check_call(my_args)
        
        ###exiftool -Author="Grieg, Edvard" IMSLP36764-PMLP02533-Grieg_Peer_Gynt_Suite_I_Op.46_Peters_7190.pdf

    def walk_folder(self):
        file_paths = sorted(Path(self.path).glob('**/*.pdf'))

        first_file = True
        for fp in file_paths:
            if not first_file:
                sleep(3)
            ScoreTagger.tag_score(fp)
            first_file = False

    def run(self):
        if self.path.is_dir():
            self.walk_folder()
        elif self.path.is_file():
            ScoreTagger.tag_score(self.path)