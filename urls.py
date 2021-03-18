def urls():
    for i in range(52):
        chapter_str = '{:02d}'.format(i+1)
        url = f'http://localhost:8000/{chapter_str}/I_{chapter_str}.html'
        print(url)

        