from os import replace
import subprocess
from typing import List
from bs4 import BeautifulSoup
from bs4.element import PageElement
from latex2svg import latex2svg, default_params
from pathlib import Path
from multiprocessing import Process
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

def make_svg(latex_str: str, macros: str, svg_path: str, svg_i: int, equation: bool):
    prefix = svg_prefix(equation)
    out = {}
    try:
        default_params['macros'] = macros
        out = latex2svg(latex_str)   
    except subprocess.CalledProcessError as err:
        print(err.stderr)
        print(err.stdout)
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
    
def to_svg_sync(latexs: List[PageElement], macros: str, svg_path: str, equation=False):
     for (svg_i, latex) in enumerate(latexs):  
         latex_str = wrap_latex(latex.string, equation)
         make_svg(latex_str, macros, svg_path, svg_i, equation)
         insert_svg(latex, svg_path, svg_i, equation)
    

def to_svg(latexs: List[PageElement], macros:str, svg_path: str, equation=False):
    ps = []
    for (svg_i, latex) in enumerate(latexs):  
        print(latex.string)
        latex_str = wrap_latex(latex.string, equation)
        
        p = Process(target=make_svg, args=(latex_str, macros, svg_path, svg_i, equation))
        ps.append(p)
    for p in ps:
        p.start()
    for p in ps:
        p.join()
        
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
    start = script_str.find('Macros: {')
    end = script_str.find('});')
    script_str = script_str[(start + 8):(end-8)]
    script_str = script_str.replace(' ', '')
    script_str = script_str.replace('\n', '')
    script_str = script_str.replace(':[', '":[')
    script_str = script_str.replace('],', '],"')
    script_str = script_str.replace('{', '{"', 1)
    json_macros = json.loads(script_str)
    # print(json_macros)        
    macros = ''
    for name in json_macros:
        value = json_macros[name]
        # print(name, value)
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
    
    # print(macros)
    return macros
    
        
def mathjax2svg(source: str, svg_path: str) -> str:
    Path(svg_path).mkdir(parents=True, exist_ok=True)    
    
    soup = BeautifulSoup(source, features="lxml")
    clean_mathjax(soup, 'span', 'MathJax')
    clean_mathjax(soup, 'div', 'MathJax_Display')
    clean_mathjax(soup, 'span', 'MathJax_Preview')
    macros = extract_latex_command(soup)
    
    latexs = soup.find_all('script', {'type': 'math/tex'})
    to_svg(latexs, macros, svg_path, equation=False)
    
    latexs = soup.find_all('script', {'type': 'math/tex; mode=display'})   
    to_svg(latexs, macros, svg_path, equation=True)
    
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
    # a =wrap_latex(r"""
    # \label{Eq:I:6:7}
    # D_N^2=
    # \begin{cases}
    # D_{N-1}^2+2D_{N-1}+1,\\[2ex]
    # \kern 3.7em \textit{or}\\[2ex]
    # D_{N-1}^2-2D_{N-1}+1.
    # \end{cases}                  
    #            """,  True)
    # print(a)
    # pass
