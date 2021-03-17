from bs4 import BeautifulSoup
from multiprocessing import Process
import timeit
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from feynman import mathjax2svg

def chapter_path(chapter):
    return f'./chapters/{chapter}'

def img_path(chapter):
    return f'{chapter_path(chapter)}/img'

def img_name(url):
    splits = url.split('/')
    last = splits[len(splits) - 1]
    parts = last.split('.')
    name = parts[0]
    return name

def download_images(driver: webdriver.Chrome, chapter):        
    path = img_path(chapter)
    Path(path).mkdir(parents=True, exist_ok=True)    
        
    elements = driver.find_elements(By.TAG_NAME, "img")    
    for element in elements:
        src = element.get_attribute('src')
        name = img_name(src)
        element.screenshot(f'{path}/{name}.png')

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'

def scrape(chapter):
    if chapter < 1 or chapter > 52:
        raise Exception(f'chapter {chapter}')
    chapter_str = '{:02d}'.format(chapter)
    url = f'https://www.feynmanlectures.caltech.edu/I_{chapter_str}.html'
    driver = webdriver.Chrome()
    driver.get(url)
    page_source = driver.page_source        
    chapter_path_s = chapter_path(chapter_str)
    
    Path(chapter_path_s).mkdir(parents=True, exist_ok=True)    
    print(f'scraping {url}')
            
    download_images(driver, chapter_str)
        
    soup = BeautifulSoup(page_source, features='lxml')        
    imgs = soup.find_all('img')
    for img in imgs:
        if 'src' in img.attrs or 'data-src' in img.attrs:
            src = ''
            if 'src' in img.attrs:
                src = img.attrs['src']
            elif 'data-src' in img.attrs:
                src = img.attrs['data-src']
                del img.attrs['data-src']
            name = img_name(src)
            img.attrs['src'] = f'img/{name}.png'                
    
    result = mathjax2svg(soup.prettify(), f'{chapter_path_s}/svgs')
    
    f = open(f'{chapter_path_s}/I_{chapter_str}.html', 'w')
    f.write(result)
    f.close()
        
    driver.close()
        

def main():
    start = timeit.default_timer()
    ps = [Process(target=scrape, args=(i+1,)) for i in range(1)]
    for p in ps:
        p.start()
    for p in ps:
        p.join()
    stop = timeit.default_timer()
    print('Time: ', stop - start) 

if __name__ == "__main__":    
    main()