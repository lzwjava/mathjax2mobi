import subprocess
from bs4 import BeautifulSoup
from bs4.element import PageElement
from latex2svg import latex2svg
from pathlib import Path

def clean_mathjax(soup, name, cls):
    previews = soup.find_all(name, {'class': cls})
    for preview in previews:
        preview.decompose()
        
def clean_script(soup):
    scripts = soup.find_all('script')
    for s in scripts:
        s.decompose()    

def wrap_latex(mathjax, equation = False):
    wrap = ''
    if equation:
        wrap = mathjax.string
    else:
        wrap = '$' + mathjax.string + '$'
    wrap = wrap.replace('label', 'tag')
    return wrap
 
def wrap_svg(svg, equation):
    if equation:
        p = BeautifulSoup(f'<div style="text-align:center;"></div>', features="lxml")
        p.div.append(svg)
        return p.div
    else:
        return svg
    
def svg_last_dir(svg_path):
    splits = svg_path.split('/')
    return splits[len(splits) - 1]        

def to_svg(mathjaxs: [PageElement], svg_path: str, equation=False):
    if equation:
        svg_prefix = 'eq_'
    else:
        svg_prefix = 'in_'
    svg_i = 0
    for mathjax in mathjaxs:     
        print(mathjax.string)
        wrap = wrap_latex(mathjax, equation=equation)
        out = {}
        try:
            out = latex2svg(wrap)   
        except subprocess.CalledProcessError as err:
            raise err      
            
        f = open(f'{svg_path}/{svg_prefix}{svg_i}.svg', 'w')
        f.write(out['svg'])
        f.close()
        
        node = BeautifulSoup('<img>', features="lxml")
        img = node.find('img')
        img.attrs['src'] = f'{svg_last_dir(svg_path)}/{svg_prefix}{svg_i}.svg'
        img.attrs['style'] = 'vertical-align: middle; margin: 0.5em 0;'
        
        p = wrap_svg(img, equation)
        mathjax.insert_after(p)
        
        svg_i +=1
        
def mathjax2svg(source: str, svg_path: str) -> str:
    Path(svg_path).mkdir(parents=True, exist_ok=True)    
    
    soup = BeautifulSoup(source, features="lxml")
    clean_mathjax(soup, 'span', 'MathJax')
    clean_mathjax(soup, 'div', 'MathJax_Display')
    clean_mathjax(soup, 'span', 'MathJax_Preview')
    
    mathjaxs = soup.find_all('script', {'type': 'math/tex'})
    to_svg(mathjaxs, svg_path, equation=False)
    
    mathjaxs = soup.find_all('script', {'type': 'math/tex; mode=display'})   
    to_svg(mathjaxs, svg_path, equation=True)
    
    clean_script(soup)  
    return soup.prettify()      
        
def main():    
    file = open('The Feynman Lectures on Physics Vol. I Ch. 13_ Work and Potential Energy (A).html')
    content = file.read()
    
    html = mathjax2svg(content, 'svgs')
    
    output_file = open('out.html', 'w')
    output_file.write(html)
    output_file.close()    

if __name__ == "__main__":
    main()
