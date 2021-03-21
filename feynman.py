from os import fdopen, replace
import subprocess
from typing import List
from bs4 import BeautifulSoup
from bs4.element import PageElement
from latex2svg import latex2png, latex2svg, default_params
from pathlib import Path
from multiprocessing import Pool
import json
import re

def clean_mathjax(soup, name, cls):
    previews = soup.find_all(name, {'class': cls})
    for preview in previews:
        preview.decompose()        
        
def clean_script(soup):
    scripts = soup.find_all('script')
    for s in scripts:
        s.decompose()    

def wrap_latex(latex_str, equation = False):
    wrap = ''
    if equation:
        wrap = latex_str
        # There mustn't be any empty lines within equation 
        wrap = wrap.replace('\n\n','\n')
        wrap = re.sub(r'\\kern{(.*)em}', r'\\kern \1em ', wrap)
    else:
        wrap = '$' + latex_str + '$'
    if 'tag' not in wrap:
        # Package amsmath Error: Multiple \tag.        
        wrap = wrap.replace('label', 'tag')
    return wrap
 
def wrap_svg(svg, equation):
    if equation:
        p = BeautifulSoup(f'<div style="text-align:center;"></div>', features="html.parser")
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

def make_svg(latex_str: str, macros: str, svg_path: str, svg_i: int, equation: bool) -> bool:
    prefix = svg_prefix(equation)
    path = f'{svg_path}/{prefix}{svg_i}.svg'
    # if os.path.exists(path):
    #     return
    out = {}
    try:
        default_params['macros'] = macros
        out = latex2svg(latex_str)
    except subprocess.CalledProcessError as err:
        print(err.stderr)
        print(err.stdout)
        print(path)
        if 'Missing number' in str(err.stdout) or \
           'Illegal unit of measure' in str(err.stdout) or \
            'A <box> was supposed' in str(err.stdout) or \
            'Undefined control sequence' in str(err.stdout):
                raise err
                # return False
        else:
                raise err
        
    f = open(path, 'w')
    f.write(out['svg'])
    f.close()
    return out

def insert_svg(latex: PageElement, svg_path: str, svg_i: int, equation: bool, out = {}):
    prefix = svg_prefix(equation)
    
    node = BeautifulSoup('<img>', features="html.parser")
    img = node.find('img')
    img.attrs['src'] = f'{svg_last_dir(svg_path)}/{prefix}{svg_i}.png'
    if 'width' in out:
        width = out['width']
        height = out['height']
        img.attrs['style'] = f'vertical-align: middle; margin: 0.5em 0; width={width}px; height={height}px;'
    else:
        img.attrs['style'] = 'vertical-align: middle; margin: 0.5em 0;'
    
    p = wrap_svg(img, equation)
    latex.insert_after(p)
    
def to_svg_sync(latexs: List[PageElement], macros: str, svg_path: str, equation=False):
    for (svg_i, latex) in enumerate(latexs):  
         latex_str = wrap_latex(latex.string, equation)
         out = make_svg(latex_str, macros, svg_path, svg_i, equation)
         insert_svg(latex, svg_path, svg_i, equation, out)
    

def to_svg(latexs: List[PageElement], macros:str, svg_path: str, equation=False):
    pool = Pool(processes = 30)
    results = []
    for (svg_i, latex) in enumerate(latexs):  
        print(latex.string)
        latex_str = wrap_latex(latex.string, equation)
        result = pool.apply_async(make_svg, args=(latex_str, macros, svg_path, svg_i, equation))
        results.append(result)
    for (i,result) in enumerate(results):    
        result.get()
    for (svg_i, latex) in enumerate(latexs):
        insert_svg(latex, svg_path, svg_i, equation)
        
def find_script(soup: BeautifulSoup):
    s1 = soup.find_all('script', attrs={'type':'text/x-mathjax-config'})
    s2 = soup.find_all('script', attrs={'type':'text/x-mathjax-config;executed=true'})
    if len(s1) == 2 and len(s2) == 0:
        return s1[0]
    elif len(s1) == 0 and len(s2) == 2:
        return s2[0]
    else:
        # no macros
        return None
        
def extract_latex_command(soup: BeautifulSoup):
    s = find_script(soup)
    if s is None:
        return ''
    script_str = s.string
    match = re.search(r'Macros:\s({[\s\S]*]\s*})', script_str)
    if match is None:
        raise Exception('not found macros')
    match_str = match.group(1)
    match_str = re.sub(r'(\S*):', r'"\1":', match_str)
    json_macros = json.loads(match_str)
    macros = ''
    for name in json_macros:
        value = json_macros[name]
        expand = value[0]
        arg_num = value[1]
        arg = ''     
        if arg_num > 0:
            arg = '[{}]'.format(arg_num)
        template = r'\newcommand{\name}arg{expand}' \
                        .replace('name', name) \
                        .replace('arg', arg) \
                        .replace('expand', expand)
        macros += template + '\n'
    
    return macros
    
        
def mathjax2svg(source: str, svg_path: str) -> str:
    Path(svg_path).mkdir(parents=True, exist_ok=True)
    
    soup = BeautifulSoup(source, features="html.parser")
    clean_mathjax(soup, 'span', 'MathJax')
    clean_mathjax(soup, 'div', 'MathJax_Display')
    clean_mathjax(soup, 'span', 'MathJax_Preview')
    macros = extract_latex_command(soup)
    
    latexs = soup.find_all('script', {'type': 'math/tex'})
    to_svg_sync(latexs, macros, svg_path, equation=False)
    
    latexs = soup.find_all('script', {'type': 'math/tex; mode=display'})   
    to_svg_sync(latexs, macros, svg_path, equation=True)
    
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
    # pass
