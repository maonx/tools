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

def del_same(chapters):
    seen = set()
    for chapter in chapters:
        if chapter[2] not in seen:
            yield chapter
            seen.add(chapter[2])

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
    chapter_content = re.sub(r'&nbsp;','',chapter_content)
    chapter_content = re.sub(r'\r\n','',chapter_content)
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
    print('已生成: ' + post_name )

def get_catalog_content(book):
    global SITE
    catalog_url = SITE + book['catalog']
    catalog = download_webpage(catalog_url)
    if book['latest']:
        catalog = re.search(r'(?<=href="'+book['latest']+').*',
                        catalog, re.S).group(0)
    return catalog

def get_chapter_list(catalog):
    regex = re.compile(r'<li><a href="(.*)">(.*(第[零一二三四五六七八九十百千]*[章|节]).*)</a></li>')
    try:
        chapters = regex.findall(catalog)
        return list(del_same(chapters))
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
    print(book['bookname'] + '有 ' + str(len(chapters)) + ' 个章节更新')
    for chapter in chapters:
        title, content = get_chapter_content(chapter)
        generate_post(book['bookname'], title, content)
        book['latest'] = chapter[0]



def update(book):
    # global path
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
                    # chapter_content = re.sub(r'.{,3}燃.{,3}文.{,3}小.{,3}[说說].?', "", chapter_content)
                    # chapter_content = re.sub(r'[wW]{,3}\.[a-zA-Z]{6}\.[a-zA-Z]{3}.?', "", chapter_content)
                    chapter_content = re.sub(r'&nbsp;','', chapter_content)
                    break
                except:
                    try_time += 1
                    if try_time > 19:
                        break
            if try_time == 20:
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
#     title='title: '+title+'\n'
#     date = 'date: '+update_time.strftime("%Y-%m-%d %H:%M:%S")+'\n'
#     chapter_content = parse_chapter_content(chapter[0])


# if __name__ == "__main__" :
#     # path = r'/home/vagrant/update-latest-novel/source/_posts/'
#     failed_list = []
#     is_update=0
#     books = get_books("books.json")
#     for book in books:
#         if update(book):
#             save_books(books, "books.json")
#     if failed_list :
#         print("Update faild %d chapters!!" % len(failed_list))
#         print('\n'.join(failed_list))
#         with open('Failed.log','w') as fp:
#             fp.write('\n'.join(failed_list))

if __name__ == "__main__" :
    books = get_books("books.json")
    for book in books:
        get_latest_posts(book)
    save_books(books, "books.json")
