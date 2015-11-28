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
def ungzip(data):
    try:
        data = gzip.decompress(data)
        return data
    except:
        pass

def download_webpage(url):
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
        page = request.urlopen(req).read()
        page_data = ungzip(page)
        catalog = page_data.decode('gbk')
        return catalog
    except:
        print('Download failed: ' + url)

def parse_chapter_content(chapter):
    regex = re.compile(r'id="content">(.*?)</(div|DIV)>',re.S)
    page_content = download_webpage(chapter[0])
    content = regex.search(page_content).group(1)
    content = re.sub(r'<br.?/>','\r\n',content)
    return content

def md_format(title, content, category="", tag=""):
    global update_time
    update_time = update_time+timedelta(seconds=1)
    title='title: '+title+'\r\n'
    date = 'date: '+update_time.strftime("%Y-%m-%d %H:%M:%S")+'\r\n'
    category = 'category: ' + category + '\r\n'
    tag = 'tags: ' + tag + '\r\n'
    format_content =  title + date + category + tag + '---\r\n' + content
    return format_content

def parse_chapters(catalog):
    regex = re.compile(r'<dd><a href="(.*\d+.html)">(.*(第+|章+|节+).*)</a>')
    try:
        chapters = regex.findall(catalog)
        return chapters
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
    fp = open(books_json, "r", encoding='utf-8')
    books = json.loads(fp.read())
    fp.close()
    return books

def save_books(books, books_json):
    fp = open(books_json, "w", encoding='utf-8')
    json.dump(books, fp, ensure_ascii=False)
    fp.close()



def update(book):
    global path
    url = book['read_url']
    # latest_chapter_url = book['latest_chapter_url']
    catalog = download_webpage(url)
    if book['latest_chapter_url'] :
        try:
            catalog = re.search(r'(?<=href="'+book['latest_chapter_url']+').*',
                            catalog, re.S).group(0)
        except:
            print("catalog format error,get failed")
            return 0

    have_new_chapter = parse_chapters(catalog)
    if have_new_chapter:
        for i in have_new_chapter:
            title = ' '.join([book['book_name'], i[1].strip()])
            try_time = 0
            while True:
                try:
                    chapter_content = parse_chapter_content(i)
                    chapter_content = re.sub(r'.{,3}燃.{,3}文.{,3}小.{,3}[说說].?', "", chapter_content)
                    chapter_content = re.sub(r'[wW]{3}\.[a-zA-Z]{6}\.[a-zA-Z]{3}.?', "", chapter_content)
                    chapter_content = re.sub(r'&nbsp;','', chapter_content)
                    break
                except:
                    try_time += 1
                    if try_time > 9:
                        break
            if try_time == 10:
                # print("Update failed: " + title)
                failed_list.append(title)
                continue
            chapter_content = md_format(title, chapter_content,
                                        book['category'], book['book_name'])
            save_path = path + title + '.md'
            save_chapter(save_path, chapter_content)
        book['latest_chapter_url'] = have_new_chapter[-1][0]
        return 1

# def download_failed_list(chapter, category, book_name):
#     global update_time
#     update_time = update_time+timedelta(seconds=1)
#     title='title: '+title+'\r\n'
#     date = 'date: '+update_time.strftime("%Y-%m-%d %H:%M:%S")+'\r\n'
#     chapter_content = parse_chapter_content(chapter[0])


if __name__ == "__main__" :
    path = r'source/_posts/'
    failed_list = []
    is_update=0
    books = get_books("books.json")
    for book in books:
        if update(book):
            save_books(books, "books.json")
            # print(books)
    if failed_list :
        print("Update faild %d chapters!!" % len(failed_list))
        print('\n'.join(failed_list))
        with open('Failed.log','w') as fp:
            fp.write('\n'.join(failed_list))

