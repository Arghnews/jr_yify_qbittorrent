#!/usr/bin/env python3

#VERSION: 0.1
#AUTHORS: Justin Riddell

import sys

import aiohttp
import asyncio

# This has been written in a different (and more liberating) style from my usual
# stuff in the sense there is no error checking at all. The idea being that
# failure is non-critical and relatively easy to reproduce, test and fix. This
# makes the code faster to write and more compact.

### Start of pagination.py

# This was a separate file, however the instructions on making your own search
# plugin (to me) do not make it explicit that your plugin MUST be in one file
# only - it states that "that a qBittorrent search engine plugin is actually a
# Python class file" however this does NOT say one and only one.
# It turns out the importer uses some shenanigans (in nova2.py) messing about
# with module imports and in the actual app when you try to import you just get
# a generic error message. I wish this was made clear on the page or the error
# message given wasn't a generic "failed to load plugin".
# Simple solution, dump all this into one file.

# The way this works:
# 1. Download search page result ie. yify/search/batman
# 2. Parse and download any additional results pages for batman movies
# 3. For each results page, scrape the set of urls for actual movie pages
# 4. Download all actual movie pages and scrape metadata including magnet link
# 5. Print these magnet links

import asyncio
import bs4
import functools
import re
import sys

import aiohttp

import novaprinter

# Three types of pages:
# One page of results
# http://www.yify-movies.net/search/mission impossible/
# Multiple pages of results but no last
# http://www.yify-movies.net/search/batman/
# Multiple pages of results with so many there's a "last" and not all on this
# page
# http://www.yify-movies.net/search/the/

def additional_urls(page):
    """Returns list of additional results pages from the first results page"""
    soup = bs4.BeautifulSoup(page, features = "html.parser")
    pages_div = soup.find("div", class_ = "pagination")

    # Likely no results at all for this title
    if not pages_div:
        return []

    # If pagination div is empty then there are no additional results pages
    hrefs = pages_div.find_all("a")
    if not hrefs:
        return []

    last = functools.reduce(max,
            (int(s["href"].split("/")[-2]) for s in hrefs[1:]))

    return ["/".join(["time", str(i), ""]) for i in range(2, last + 1)]

async def get(session, url):
    """Given a session and url (awaits and) fetches the url content"""
    async with session.get(url) as resp:
        return await resp.text()

def page_movie_urls(page):
    return {m for m in re.findall(r"href=\"(/movies[^\"]*)\"", page)}

async def metadata_from_url(session, url, root):
    """Downloads a movie page from url, returning a dict of metadata"""
    # print("Getting")
    metadata = {
            "engine_url": root,
            "desc_link": url,
            "url": url,
            }
    page = await get(session, url)
    # page = str(requests.get(url).content)
    data = metadata_from_page(page)
    metadata.update(data)
    # doneso()
    return metadata

# For debugging to see how long each request is taking
# def doneso():
#     if not hasattr(doneso, "i"):
#         doneso.i = 0
#     print(doneso.i)
#     doneso.i += 1

def metadata_from_page(page):
    """Parses page to grab appropriate metadata including magnet link"""
    metadata = {"leech": "-1",}
    soup = bs4.BeautifulSoup(page, features = "html.parser")

    e = soup.find("div", class_ = "heading")
    e.contents[0].unwrap()
    name = e.string
    if name.endswith(" YIFY Movie"):
        name = name[:-len(" YIFY Movie")]
    metadata["name"] = name

    year_start = name.rfind("(") + 1
    year_end = name.rfind(")", year_start)
    metadata["year"] = name[year_start: year_end]

    metadata["link"] = soup.find("a", href = re.compile(r"^magnet:.*"))["href"]

    for tag in soup.find("div", class_ = "available").ul.find_all("li"):
        # Remove bold tag from first element
        tag.contents[0].unwrap()
        if tag.contents[0] == "Size:":
            metadata["size"] = tag.contents[1].strip()
        if tag.contents[0] == "Quality:":
            metadata["quality"] = tag.contents[1].strip()
        if tag.contents[0] == "Peers/Seeds:":
            peers, seeds = tag.contents[1].replace(" ", "").split("/")
            metadata["seeds"] = seeds
    return metadata

async def main_async(session, title, root):

    # Get first set of pages
    root_search_title = root + "/search/" + title + "/"
    pages = [await get(session, root_search_title)]
    urls = [root_search_title + url for url in additional_urls(pages[0])]
    if urls:
        pages += await asyncio.gather(*[get(session, url) for url in urls])
    movie_urls = [url for page in pages for url in page_movie_urls(page)]
    # print(len(pages))
    # print(len(movie_urls))

    # Remove bad quality or 3d versions
    remove = [url for url in movie_urls if
            (url.endswith("720p.html")
                and url.replace("720p.html", "1080p.html") in movie_urls)
            or url.endswith("3d.html")]
    movie_urls = [root + url for url in movie_urls if url not in remove]
    # print(len(movie_urls))

    # Get actual metadata including magnet links
    # print(movie_urls)
    magnets = await asyncio.gather(
            *[metadata_from_url(session, url, root) for url in movie_urls])
    movies = sorted(magnets,
            key = lambda movie: (int(movie["year"]), movie["name"]))

    # Print results
    for movie in movies:
        # print(movie["name"], "-", movie["year"])
        novaprinter.prettyPrinter(movie)

async def main_a(title, root):
    """Asynchronous entry point"""
    async with aiohttp.ClientSession(
            connector = aiohttp.TCPConnector(limit = 500)) as session:
        await main_async(session, title, root)

def search_me(title, root):
    """Synchronous entry point, root being yify url root"""
    asyncio.get_event_loop().run_until_complete(main_a(title, root))

### End of pagination.py



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

# Issues with regard to:
# https://aiohttp.readthedocs.io/en/stable/faq.html#why-is-creating-a-clientsession-outside-of-an-event-loop-dangerous
# Event loop should always live at least as long as the async objects scheduled
# in it - for now a version with essentially full tear down and creation each
# time - probably less efficient - would this break nicely(/at all?) if
# qbittorrent used asyncio stuff underneath (and messed with event loops)

class jr_yify:
    url = "http://www.yify-movies.net"
    name = "yify-movies.net"
    supported_categories = {"all": "0", "movies": "6",}

    def search(self, what, cat = "movies"):
        search_me(what, jr_yify.url)

def main(argv):
    searcher = jr_yify()
    searcher.search("scott pilgrim")
    searcher.search("batman")

if __name__ == "__main__":
    sys.exit(main(sys.argv))
