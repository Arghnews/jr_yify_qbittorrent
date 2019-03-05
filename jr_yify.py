#!/usr/bin/env python3

#VERSION: 0.01
#AUTHORS: Justin Riddell

import sys

import aiohttp
import asyncio

import pagination

_ = """
Required for qbittorrent else -1
link => A string corresponding the the download link (the .torrent file or magnet link)
name => A unicode string corresponding to the torrent's name (i.e: "Ubuntu Linux v6.06")
size => A string corresponding to the torrent size (i.e: "6 MB" or "200 KB" or "1.2 GB"...)
seeds => The number of seeds for this torrent (as a string)
leech => The number of leechers for this torrent (a a string)
engine_url => The search engine url (i.e: http://www.mininova.org)
desc_link => A string corresponding to the the description page for the torrent

Mine
url => Search url
quality => Quality eg. 1080p, 3d
year => Year released
"""

yify_root = "http://www.yify-movies.net"

# Issues with regard to:
# https://aiohttp.readthedocs.io/en/stable/faq.html#why-is-creating-a-clientsession-outside-of-an-event-loop-dangerous
# Event loop should always live at least as long as the async objects scheduled
# in it - for now a version with essentially full tear down and creation each
# time - probably less efficient - would this break nicely(/at all?) if
# qbittorrent used asyncio stuff underneath (and messed with event loops)

class jr_yify:
    url = yify_root
    name = "jr-yify-movies.net"
    supported_categories = {"all": "0", "movies": "6",}

    def search(self, what, cat = "movies"):
        pagination.search_me(what, jr_yify.url)

def main(argv):
    searcher = jr_yify()
    searcher.search("scott pilgrim")
    searcher.search("batman")

if __name__ == "__main__":
    sys.exit(main(sys.argv))
