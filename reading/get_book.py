#!/usr/bin/env python3
# -*- utf-8 -*-

import gzip
import re
import json
import socket
from urllib import request
from datetime import datetime,timedelta

socket.setdefaulttimeout(20)

update_time=datetime.today()
SITE='http://www.shenmaxiaoshuo.com'

def ungzip(data):
    try:
        data = gzip.decompress(data)
        return data
    except:
        pass

def filter_chapter(chapters):
    seen = set()
    for chapter in chapters:
        chapter_name = chapter[1]
        if chapter_name not in seen:
            yield chapter
            seen.add(chapter_name)

def download_webpage(url):
    header = {
        'Host': 'www.shenmaxiaoshuo.com',
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
        page = request.urlopen(req).read()
        page_data = ungzip(page)
        catalog = page_data.decode('gbk')
        return catalog
    except:
        print('Download failed: ' + url)

def get_chapter_content(chapter):
    global SITE
    chapter_url = SITE + chapter[0]
    title = chapter[1]
    regex = re.compile(r'id="htmlContent".*</script></div>(.*?)更多手打全文字章节',re.S)
    chapter_content = download_webpage(chapter_url)
    chapter_content = regex.search(chapter_content).group(1)
    chapter_content = re.sub(r'<br.?/>','\n',chapter_content)
    chapter_content = re.sub(r'&nbsp;|\r\n','',chapter_content)
    return (title,chapter_content)

def download_book(book):
    catalog = get_catalog_content(book)
    chapters = get_chapter_list(catalog)
    file_name = book['bookname'] + '.txt'
    with open(file_name, 'wt') as f:
        for chapter in chapters:
            title, content = get_chapter_content(chapter)
            f.write(title + content)

def generate_post(bookname, title, content):
    global update_time
    update_time = update_time+timedelta(seconds=1)
    post_name = bookname+' '+title + '.md'
    title='title: '+ bookname + ' ' + title+'\n'
    date = 'date: '+update_time.strftime("%Y-%m-%d %H:%M:%S")+'\n'
    tag = 'tags: ' + bookname + '\n'
    post_content =  title + date + tag + '---\n' + content
    with open(post_name, 'wt') as f:
        f.write(post_content)

def get_catalog_content(book):
    global SITE
    catalog_url = SITE + book['catalog']
    catalog = download_webpage(catalog_url)
    if book['latest']:
        catalog = re.search(r'(?<=href="'+book['latest']+').*',
                        catalog, re.S).group(0)
    return catalog

def get_chapter_list(catalog):
    regex = re.compile(r'<li><a href="(.*)">(.*(楔子|外传|章|卷|节).*)</a></li>')
    try:
        chapters = regex.findall(catalog)
        return list(filter_chapter(chapters))
    except:
        print('Catalog format error')

def save_chapter(name,content):
    try:
        fp=open(name,'w')
        fp.write(content)
        print("Save success: "+name)
    except:
        print("Save chapter error!")
    fp.close()

def get_books(books_json):
    fp = open(books_json, "r")
    books = json.loads(fp.read())
    fp.close()
    return books

def save_books(books, books_json):
    fp = open(books_json, "w")
    json.dump(books, fp, ensure_ascii=False)
    fp.close()


def get_latest_posts(book):
    catalog = get_catalog_content(book)
    chapters = get_chapter_list(catalog)
    print('\n %s有 %d 个章节更新:' % (book['bookname'], len(chapters)))
    for index, chapter in enumerate(chapters):
        title, content = get_chapter_content(chapter)
        generate_post(book['bookname'], title, content)
        print('已生成(%2d/%d): %s' % (index+1, len(chapters), title))
        book['latest'] = chapter[0]


if __name__ == "__main__" :
    books = get_books("books.json")
    for book in books:
        get_latest_posts(book)
    save_books(books, "books.json")
