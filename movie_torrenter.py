#!/usr/bin/env python3

import argparse
import functools
import logging
import operator
import re
import requests
import sys
import textwrap

from collections import OrderedDict

# Install via pip, for copying output to clipboard
# import pyperclip

from my_logger import get_console_logger, get_console_and_file_logger

# TODO:
# Pyperclip if we pipe output results in program never closing
# Linebreaks in output
# Qbittorrent API integration?
# GUI?
# Extra option for output of just magnets
# Fix verbose argument inputs

log = logging.getLogger()

def search_movie(root, title):
    url = root + "/search/" + title + "/"
    log.debug("Requesting page " + url)
    content = str(requests.get(url).content)
    # Urls are on page twice each
    return list({"".join([root, m])
            for m in re.findall(r"href=\"(/movies[^\"]*)\"", content)})

def get_url_to_magnets(urls):
    url_to_magnets = {}
    for url in urls:
        page_content = str(requests.get(url).content)
        magnet = re.search(r"a href=\"(magnet[^\"]*)\"", page_content)[1]
        url_to_magnets[url] = magnet
    return url_to_magnets

# Unused for now - this and suffix version tend to remove too much
# def common_prefix_len(l):
#     shortest = functools.reduce(min, map(len, l))
#     for i in range(shortest):
#         ll = list(map(operator.itemgetter(i), l))
#         if not all(x == ll[0] for x in ll):
#             return i
#     return shortest

# After stripping the front of the link and the .html suffix
# Watch for extended edition etc. suffixes
# the-lord-of-the-rings-the-fellowship-of-the-ring-extended-2001-yify-1080p
# the-lord-of-the-rings-the-fellowship-of-the-ring-theatrical-edition-2001-yify-1080p
#
# Two movies with same name but different year
# the-aviator-1985-yify-1080p
# the-aviator-2004-yify-1080p
#
# Careful of not getting the year mixed
# die-hard-1988-yify-1080p
# die-hard-2-die-harder-1990-yify-1080p
#
# Can be at least 3 qualities
# rogue-one-a-star-wars-story-2016-yify-720p
# rogue-one-a-star-wars-story-2016-yify-1080p
# rogue-one-a-star-wars-story-2016-yify-3d
#
# Only 720p version exists
# the-incredibles-2004-yify-720p

def process_urls(url_to_magnets, root, include_3d):

    # url_to_magnets = list(url_to_magnets.items())
    done = {}
    # For testing
    # a = url_to_magnets.popitem()
    # url_to_magnets[a[0] + "asdf"] = a[1]

    prefix = root + "/movies/"
    suffix = ".html"

    # Filter non-matching urls and put them in done
    for url, magnet in url_to_magnets.items():
        if not url.startswith(prefix) or not url.endswith(suffix):
            done[url] = magnet
        else:
            url = url[len(prefix):-len(suffix)]
            parts = url.split("-")
            if len(parts) < 4 or parts[-2] != "yify" or \
                    not re.match(r"\d{4}", parts[-3]):
                done[url] = magnet

    # Remove www prefix and .html suffix and remove urls in done that don't
    # match expected format
    def cleanse(url):
        parts = url[len(prefix):-len(suffix)].split("-")
        del parts[-2]
        return " ".join(parts)

    url_to_magnets = {cleanse(url): magnet
            for url, magnet in url_to_magnets.items() if url not in done}

    # If a 720p and 1080p version of the same url exist remove the 720p
    for url in [url for url in url_to_magnets if url.endswith("720p") \
            and url.replace("720p", "1080p") in url_to_magnets]:
        log.debug("Removing (worse quality) duplicate " + url)
        del url_to_magnets[url]

    if not include_3d:
        # If a 720p and 1080p version of the same url exist remove the 720p
        for url in [url for url in url_to_magnets if url.endswith("3d")]:
            log.debug("Removing 3d " + url)
            del url_to_magnets[url]

    # Sort by year, note how we removed the "yify" entry so index changed
    # Then normally sort anyway
    return OrderedDict(
            sorted(url_to_magnets.items(),
                key = lambda x: (int(x[0].split(" ")[-2]), x))
            + sorted(done.items()))

def movies_from_file(filepath):
    with open(filepath, "r") as f:
        return [l for l in f.read().splitlines() if l and l[0] != "#"]

# def bold(s):
#     return "\33[1m" + s + "\33[0m"

# def text_to_clipboard(text):
#     # Doesn't work on ubuntu 18.10 in Python 3.6.7 when run as script
#     print("Sending to clipboard:", text)
#     from tkinter import Tk
#     r = Tk()
#     # https://stackoverflow.com/a/4203897/8594193
#     # Withdraw this widget from the screen such that it is unmapped and
#     # forgotten by the window manager.
#     r.withdraw()
#     r.clipboard_clear()
#     r.clipboard_append(text)
#     # Enter event loop until all pending events have been processed by Tcl.
#     r.update()
#     # Destroy this and all descendants widgets. This will end the application
#     # of this Tcl interpreter.
#     r.destroy()

def text_to_clipboard(text):
    pass
    pyperclip.copy(text)
    pyperclip.paste()

def main(argv):

    # print(pyperclip.determine_clipboard()[0])
    # text_to_clipboard("See me on the clipboard!!!")
    # return

    parser = argparse.ArgumentParser(
            description = "Get movie magnet links from yify-movies.net",
            allow_abbrev = False,
            formatter_class = argparse.RawDescriptionHelpFormatter,
            epilog = textwrap.dedent("""\
            Note:
              Consider cases of movie names like spiderman vs spider-man
            Examples:
              Fetch Die Hard series and The Big Short
              -m "die hard" "the big short"
              Fetch Die Hard series and The Big Short and movies in file.movies
              -m "die hard" "the big short" -i file.movies
            """,
            ))
    parser.add_argument("-3d", "--include-3d", action = "store_true",
            help = "Include 3d films in output")
    parser.add_argument("-v", "--verbose", action = "store_true")
    parser.add_argument("-m", "--movies", nargs = "+",
            help = "Movies to fetch")
    parser.add_argument("-i", "--input-file",
            help = "File with movies to fetch")
    parser.add_argument("-o", "--output-file",
            help = "Also log to file")
    parser.add_argument("-q", "--quiet", action = "store_true",
            help = "Only print magnet outputs")

    args = parser.parse_args()

    global log
    if args.input_file is not None:
        if args.movies is None:
            args.movies = []
        args.movies += movies_from_file(args.input_file)
    if not args.movies:
        parser.error("No movies found")

    if args.output_file is not None:
        # Delete old output file
        with open(args.output_file, "w"):
            pass
        log = get_console_and_file_logger(args.output_file)
    else:
        log = get_console_logger()

    log.setLevel(logging.INFO)
    if args.verbose:
        log.setLevel(logging.DEBUG)
    elif args.quiet:
        # Set level to above info - only print magnet links
        log.setLevel(25)

    log.debug(args)

    # log.debug("Looking in " + input_movies_filepath + " for movies")
    # movies = movies_from_file(input_movies_filepath)
    log.info("Found " + str(len(args.movies)) + " movie(s)")
    for i, movie in enumerate(args.movies):
        log.debug("Movie " + str(i) + ": " + movie)
    # movies = ["the incredibles"]
    root = "http://www.yify-movies.net"

    movie_to_magnets = {}

    for movie in args.movies:
        log.info("Processing movie " + movie)
        urls = search_movie(root, movie)
        for url in urls:
            log.debug("Url: " + url)
        url_to_magnets = get_url_to_magnets(urls)
        url_to_magnets = process_urls(url_to_magnets, root, args.include_3d)
        log.debug(movie + " - " + str(len(url_to_magnets)) + " results")
        movie_to_magnets[movie] = url_to_magnets

    log.info("")
    for movie, url_to_magnet in movie_to_magnets.items():
        log.info("Movie \"" + movie + "\" has " +
                str(len(url_to_magnet)) + " result(s):\n")
        for url, magnet in url_to_magnet.items():
            log.info("\t" + url)
            # Print magnet links at high level so they are always displayed
            log.log(25, magnet)
        log.info("")
    magnets = "".join([magnet + "\n"
        for url_to_magnet in movie_to_magnets.values()
        for magnet in url_to_magnet.values()])
    # sys.stdout.flush()
    # sys.stdout.close()
    # text_to_clipboard(magnets)
    # return
    # log.info("The magnet links have been copied to your clipboard")

if __name__ == "__main__":
    sys.exit(main(sys.argv))

