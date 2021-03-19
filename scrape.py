import os
from bs4 import BeautifulSoup
from multiprocessing import Process
import timeit
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from feynman import mathjax2svg
import re

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
    print(len(elements))
    for element in elements:
        src = element.get_attribute('src')
        name = img_name(src)
        png_path = f'{path}/{name}.png'
        if os.path.exists(png_path):
            continue
        element.screenshot(png_path)

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15'

def scrape(driver, chapter_str):
    url = f'https://www.feynmanlectures.caltech.edu/I_{chapter_str}.html' 
    driver.get(url)
    page_source = driver.page_source        
    chapter_path_s = chapter_path(chapter_str)
    
    Path(chapter_path_s).mkdir(parents=True, exist_ok=True)    
    print(f'scraping {url}')
    print(page_source)
        
    WebDriverWait(driver, 10).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'h3.section-title'))
    )
        
    download_images(driver, chapter_str)
    print('download_images')
    
    convert(page_source, chapter_str)
    print('convert')
    
    return page_source

def chapter_string(chapter):
    chapter_str = '{:02d}'.format(chapter)    
    return chapter_str

def convert(page_source, chapter_str):    
    chapter_path_s = chapter_path(chapter_str)
    soup = BeautifulSoup(page_source, features='html.parser')        
    imgs = soup.find_all('img')
    print(len(imgs))
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
    
    div = soup.find('div', {'class': 'floating-menu'})
    div.decompose()
    
    title = soup.find('title') 
    title.string = title.string.replace('The Feynman Lectures on Physics Vol. I ', '')
    
    result = mathjax2svg(soup.encode(), f'{chapter_path_s}/svgs')
    
    f = open(f'{chapter_path_s}/I_{chapter_str}.html', 'w')
    f.write(result)
    f.close()
    
def change_title():
    for i in range(52):
        chs = chapter_string(i+1)
        path = chapter_path(chs)
        f = open(f'{path}/I_{chs}.html', 'w+')
        html = f.read()
        html = re.sub(r'<title>\s*The Feynman Lectures on Physics Vol. I ([\s\S]*)</title>', 
               r'<title>\1</title>', html)
        f.write(html)
        f.close()

def main():
    start = timeit.default_timer()
    driver = webdriver.Chrome()    
    chapter_n = 1
    for i in range(chapter_n):
        scrape(driver, chapter_string(i+28))
    driver.quit()
    stop = timeit.default_timer()    
    print('Time: ', stop - start) 

if __name__ == "__main__":    
    main()
    # change_title()