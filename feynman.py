import subprocess
from sys import prefix
from bs4 import BeautifulSoup
from bs4.element import PageElement
from latex2svg import latex2svg
from pathlib import Path
from multiprocessing import Process

def clean_mathjax(soup, name, cls):
    previews = soup.find_all(name, {'class': cls})
    for preview in previews:
        preview.decompose()
        
def clean_script(soup):
    scripts = soup.find_all('script')
    for s in scripts:
        s.decompose()    

def wrap_latex(latex, equation = False):
    wrap = ''
    if equation:
        wrap = latex.string
    else:
        wrap = '$' + latex.string + '$'
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

def svg_prefix(equation: bool):
    prefix = ''
    if equation:
        prefix = 'eq_'
    else:
        prefix = 'in_'
    return prefix

def make_svg(latex_str: str, svg_path: str, svg_i: int, equation: bool):
    prefix = svg_prefix(equation)
    out = {}
    try:
        out = latex2svg(latex_str)   
    except subprocess.CalledProcessError as err:
        raise err      
        
    f = open(f'{svg_path}/{prefix}{svg_i}.svg', 'w')
    f.write(out['svg'])
    f.close()    

def insert_svg(latex: PageElement, svg_path: str, svg_i: int, equation: bool):
    prefix = svg_prefix(equation)
    
    node = BeautifulSoup('<img>', features="lxml")
    img = node.find('img')
    img.attrs['src'] = f'{svg_last_dir(svg_path)}/{prefix}{svg_i}.svg'
    img.attrs['style'] = 'vertical-align: middle; margin: 0.5em 0;'
    
    p = wrap_svg(img, equation)
    latex.insert_after(p)

def to_svg(latexs: [PageElement], svg_path: str, equation=False):
    ps = []
    for (svg_i, latex) in enumerate(latexs):  
        print(latex.string)
        latex_str = wrap_latex(latex, equation)
        
        p = Process(target=make_svg, args=(latex_str, svg_path, svg_i, equation))
        ps.append(p)
    for p in ps:
        p.start()
    for p in ps:
        p.join()
        
    # for (svg_i, latex) in enumerate(latexs):  
    #     insert_svg(latex, svg_path, svg_i, equation)
        
def mathjax2svg(source: str, svg_path: str) -> str:
    Path(svg_path).mkdir(parents=True, exist_ok=True)    
    
    soup = BeautifulSoup(source, features="lxml")
    clean_mathjax(soup, 'span', 'MathJax')
    clean_mathjax(soup, 'div', 'MathJax_Display')
    clean_mathjax(soup, 'span', 'MathJax_Preview')
    
    latexs = soup.find_all('script', {'type': 'math/tex'})
    to_svg(latexs, svg_path, equation=False)
    
    latexs = soup.find_all('script', {'type': 'math/tex; mode=display'})   
    to_svg(latexs, svg_path, equation=True)
    
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
