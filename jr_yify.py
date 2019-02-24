#!/usr/bin/env python3

#VERSION: 0.01
#AUTHORS: Justin Riddell

import itertools
import re
import requests
import sys

import bs4

from multiprocessing import cpu_count
from multiprocessing.dummy import Pool
from novaprinter import prettyPrinter

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

def metadata_from_url(url, root = yify_root):
    # print("Getting")
    metadata = {
            "engine_url": root,
            "desc_link": url,
            "url": url,
            }
    page = str(requests.get(url).content)
    data = metadata_from_page(page)
    metadata.update(data)
    return metadata

def metadata_from_page(page):
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

def movie_urls_on_page(page):
    return {m for m in re.findall(r"href=\"(/movies[^\"]*)\"", page)}

class jr_yify:
    url = yify_root
    name = "justin-yify-movies.net"
    supported_categories = {"all": "0", "movies": "6",}

    def __init__(self):
        self._pool = Pool(processes = max(6, cpu_count() * 0))

    def search(self, what, cat = "movies"):
        self.movie_urls(what)

    def other_pages_from_first(self, soup, root = yify_root):
        res = ["".join([root, link["href"]]) for link in
                soup.find("div", class_ = "pagination").find_all("a")[1:-1]]
        # print(res)
        # sys.exit(0)
        return res

    def movie_urls(self, title, root = yify_root):
        url = root + "/search/" + title + "/"
        page = str(requests.get(url).content)
        soup = bs4.BeautifulSoup(page, features = "html.parser")

        # TODO:
        # this can be parallelised better by removing the dependency stages
        # for each part so that any part can flow as fast as possible to the end

        # pages = itertools.chain(page, (str(next_page.content)
        #     for next_page in self._pool.map(
        #         requests.get, self.other_pages_from_first(soup))))
        def f(*args):
            # print("Started")
            return requests.get(*args)

        # print(url)
        pages = [page] + [str(next_page.content)
            for next_page in self._pool.imap_unordered(
                f, self.other_pages_from_first(soup))]
        # print(pages)

        urls = [root + url for p in pages for url in movie_urls_on_page(p)]
        # print(urls)
        # print(len(urls))
        # for u in sorted(urls):
        #     print(u)

        # http://www.yify-movies.net/movies/solo-a-star-wars-story-2018-yify-720p.html
        # Remove 720p version if 1080p version exists
        remove = [url for url in urls if
                (url.endswith("720p.html")
                    and url.replace("720p.html", "1080p.html") in urls)
                or url.endswith("3d.html")]
        urls = [url for url in urls if url not in remove]

        movies = sorted([movie for movie in
                self._pool.imap_unordered(metadata_from_url, urls)],
                key = lambda movie: (int(movie["year"]), movie["name"]))
        for movie in movies:
            pass
            prettyPrinter(movie)

def main(argv):
    searcher = jr_yify()
    searcher.search("scott pilgrim")

if __name__ == "__main__":
    sys.exit(main(sys.argv))

