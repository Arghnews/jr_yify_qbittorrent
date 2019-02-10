#!/usr/bin/env python3

#VERSION: 0.1
#AUTHORS: Justin Riddell

import re
import requests
import sys

import bs4

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

def movie_urls(title, root = yify_root):
    url = root + "/search/" + title + "/"
    content = str(requests.get(url).content)
    # Urls are on page twice each
    return list({"".join([root, m])
            for m in re.findall(r"href=\"(/movies[^\"]*)\"", content)})

def metadata_from_url(url, root = yify_root):
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

    metadata["link"] = soup.find("a", href = re.compile("^magnet:.*"))["href"]

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

class jr_yify:
    url = yify_root
    name = "yify-movies.net"
    supported_categories = {"all": "0", "movies": "6",}

    def __init__(self):
        self._pool = Pool(processes = 10)

    def search(self, what, cat = "movies"):
        urls = movie_urls(what)
        # print(urls)

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
            prettyPrinter(movie)

def main(argv):
    searcher = jr_yify()
    searcher.search("star wars")

if __name__ == "__main__":
    sys.exit(main(sys.argv))
