#!/usr/bin/env python3
# -*- utf-8 -*-
import argparse
import re
import json
from bs4 import BeautifulSoup
from urllib import request

'''
To get Sohu TV playlist urls to download by you-get,
you can get all urls or a part of it.

'''

def get_args(args=""):
    parser = argparse.ArgumentParser(description='Get episodes\' url by Sohu TV list\'s url')
    parser.add_argument('url', help="get all episodes' url by a sohu tv list's url")
    parser.add_argument('-n','--number',type=int, nargs='*', help="get episodes's url which you input ")
    parser.add_argument('-s','--start', type=int, help="number where to start")
    parser.add_argument('-e','--end', type=int, help="number where to end")
    if args:
        return parser.parse_args(args.split())
    return parser.parse_args()

def get_playlist_id(url):
    html_content = request.urlopen(url).read().decode('gbk')
    html_content = html_content.replace(' ','')
    playlist_id = re.search(r'(?<=playlistId=")\d+', html_content)
    return playlist_id.group(0)

def get_playlist_url(playlist_id):
    url = 'http://pl.hd.sohu.com/videolist?playlistid='+playlist_id+'&order=0&cnt=1&callback=__get_videolist'
    url_content = request.urlopen(url).read().decode('gbk')
    playlist_json = re.search(r'{.*}', url_content).group(0)
    videos = json.loads(playlist_json)['videos']
    videos_urls = [ x['pageUrl'] for x in videos]
    return videos_urls

def main():
    args = get_args()
    playlist_all_url = get_playlist_url(get_playlist_id(args.url))
    playlist_all_url = [len(playlist_all_url)]+playlist_all_url
    playlist_select_url = playlist_range_url = []
    if args.number is not None:
        playlist_select_url = [ playlist_all_url[x] for x in args.number]
    if args.start is not None:
        playlist_range_url = playlist_all_url[args.start:]
        if args.end is not None:
            playlist_range_url = playlist_all_url[args.start:args.end]
    elif args.end is not None:
        playlist_range_url = playlist_all_url[1:args.end]
    playlist_output = playlist_select_url + playlist_range_url
    if not len(playlist_output) :
        playlist_output = playlist_all_url[1:]
    print(' '.join(playlist_output))



if __name__ == "__main__" :
    main()
else :
    args = get_args('http://tv.sohu.com/s2015/sgnb/ -s 3 -s 6')
