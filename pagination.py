#!/usr/bin/env python3.7

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
# Multiple pages of results with so many there's a last and not all on this page
# http://www.yify-movies.net/search/the/

def additional_urls(page):
    soup = bs4.BeautifulSoup(page, features = "html.parser")
    pages_div = soup.find("div", class_ = "pagination")

    # Likely no results at all for this title
    if not pages_div:
        return []

    # If pagination div is empty then we still need to yield this page
    hrefs = pages_div.find_all("a")
    if not hrefs:
        return []

    last = functools.reduce(max,
            (int(s["href"].split("/")[-2]) for s in hrefs[1:]))

    return ["/".join(["time", str(i), ""]) for i in range(2, last + 1)]

async def get(session, url):
    async with session.get(url) as resp:
        return await resp.text()

def page_movie_urls(page):
    return {m for m in re.findall(r"href=\"(/movies[^\"]*)\"", page)}

async def metadata_from_url(session, url, root):
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

    for movie in movies:
        # print(movie["name"], "-", movie["year"])
        novaprinter.prettyPrinter(movie)

async def main_a(title, root):
    async with aiohttp.ClientSession(
            connector = aiohttp.TCPConnector(limit = 500)) as session:
        await main_async(session, title, root)

def search_me(title, root):
    asyncio.get_event_loop().run_until_complete(main_a(title, root))

def main(argv):
    root = "http://www.yify-movies.net"
    # title = "asdfasdf" # No results
    # title = "mission impossible" # 1 page of results (current page)
    title = "batman" # 3 pages of results
    # title = "the" # Many many pages of results ~5000 movie magnets, long time
    search_me(title, root)
    # with aiohttp.ClientSession(
    #         connector = aiohttp.TCPConnector(limit = 500)) as session:
    #     asyncio.run(main_async(session, root, title))

if __name__ == "__main__":
    sys.exit(main(sys.argv))
