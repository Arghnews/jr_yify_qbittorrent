This project is a small qBittorrent plugin in Python3 that searches yify for magnet links. It uses and was made as a way to learn more about python's (awesome) asyncio stuff. Using asyncio means it can utilise a very small (possibly 1) number of threads (under the hood, this is an implementation detail of asyncio) to service a much greater number of connections/many webpages in parallel - particularly well suited to an I/O bound task such as this one. I do *not* endorse pirating movies.

## Requirements
* Python3.6
    * Python modules: [asyncio](https://docs.python.org/3.7/library/asyncio.html), [aiohttp](https://aiohttp.readthedocs.io/en/stable), [beautiful soup 4](https://www.crummy.com/software/BeautifulSoup/bs4/doc)

## Usage
1. Clone this repo (all you actually need is the jr_yify.py file)
2. Add the jr_yify.py file to [qBittorrent as a search plugin](https://github.com/qbittorrent/search-plugins/wiki/Install-search-plugins)
