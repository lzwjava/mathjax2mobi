import requests
from bs4 import BeautifulSoup

def main():
    r = requests.get('https://www.feynmanlectures.caltech.edu/I_toc.html')
    if r.status_code != 200:
        return
    soup = BeautifulSoup(r.text, features='lxml')
    f = open('toc.html', 'w')
    f.write(soup.prettify())
    f.close()

main()