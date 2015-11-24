#!/usr/bin/env python3
# -*- utf-8 -*-

from urllib import request
from datetime import datetime,timedelta
import gzip
import re
import json

update_time=datetime.today()
def ungzip(data):
    try:
        data = gzip.decompress(data)
        return data
    except:
        pass

def get_webpage(url):
    header = {
        'Host': 'www.ranwen.org',
        'Connection': 'keep-alive',
        'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                   'image/webp,*/*;q=0.8'),
        'User-Agent': ('Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36'
                       '(KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36'),
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8,zh-CN;q=0.6,zh;q=0.4',
    }
    try:
        req = request.Request(url, headers = header)
        page = request.urlopen(req, timeout = 2).read()
        page_data = ungzip(page)
        catalog = page_data.decode('gbk')
        return catalog
    except:
        print('Get url: ' + url + ' failed!')

def parse_chapter_content(chapter):
    regex = re.compile(r'id="content">(.*?)</(div|DIV)>',re.S)
    page_content = get_webpage(chapter[0])
    content = regex.search(page_content).group(1)
    content = content.replace('<br/>','\r\n')
    return content

def md_format(name, content):
    global update_time
    update_time = update_time+timedelta(seconds=1)
    md_time = 'date: '+update_time.strftime("%Y-%m-%d %H:%M:%S")+'\r\n'
    md_head='title: '+name+'\r\n'+md_time+'---\r\n'
    format_content =  md_head + content
    return format_content

def parse_chapters(catalog):
    regex = re.compile(r'<dd><a href="(.*\d+.html)">(.*(第+|章+|节+).*)</a>')
    try:
        chapters = regex.findall(catalog)
        return chapters
    except:
        print('catalog format error')

def save_chapter(name,content):
    try:
        fp=open(r'source/_posts/'+name,'w')
        fp.write(content)
        print("update "+name)
    except:
        print("save chapter error!")
    fp.close()

def get_books(books_json):
    fp = open(books_json, "r", encoding='utf-8')
    books = json.loads(fp.read())
    fp.close()
    return books

def save_books(books, books_json):
    fp = open(books_json, "w", encoding='utf-8')
    json.dump(books, fp, ensure_ascii=False)
    fp.close()



def main(book):
    url = book['read_url']
    latest_chapter_url = book['latest_chapter_url']
    catalog = get_webpage(url)
    if latest_chapter_url :
        catalog = re.search(r'(?<=href="'+latest_chapter_url+').*', catalog, re.S).group(0)
    chapters = parse_chapters(catalog)
    if len(chapters) == 0 :
        print("update nothing")
        return 0
    for i in chapters:
        chapter_name = ' '.join([book['book_name'], i[1].strip()])
        try:
            chapter_content = parse_chapter_content(i)
        except:
            print('miss ' + chapter_name)
            continue

        save_chapter(chapter_name + '.md',
                     md_format(chapter_name, chapter_content))
    book['latest_chapter_url'] = chapters[-1][0]
    return 1

if __name__ == "__main__" :
    # url = 'http://www.ranwen.org/files/article/40/40109/index.html'
    # url = 'http://www.ranwen.org/files/article/77/77384/index.html'
    is_update=False
    books = get_books("books.json")
    for book in books[1:]:
        is_update=main(book)
    if is_update:
        save_books(books, "books.json")

