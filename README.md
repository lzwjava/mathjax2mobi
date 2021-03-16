# feynman-lectures-mobi
convert feynman lectures online html pages to mobi e-book

![f_html](./img/f_html.png)

![svg_p](./img/svg_p.png)

![latex_debug](./img/latex_debug.png)

![epub_p](./img/epub_p.png)

### How to run

```shell
python feynman.py

pandoc -s -r html out.html -o feynman.epub
```

### Thanks

Thanks to the project [tuxu/latex2svg](https://github.com/tuxu/latex2svg). The `latex2svg.py` in this project is modified from that project.