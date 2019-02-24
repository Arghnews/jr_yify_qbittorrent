#!/usr/bin/env python3.7

import sys
import aiohttp
import asyncio

async def get(session, url):
    async with session.get(url) as resp:
        return await resp.text()

async def a_main():
    print("Hello")
    # await asyncio.sleep(1)
    async with aiohttp.ClientSession() as session:
        urls = ["http://httpbin.org/get"] * 10
        results = await asyncio.gather(*(get(session, url) for url in urls))
        print(results)

    print("World")

def main(argv):
    print("Running async")
    asyncio.run(a_main())
    print("Done")

if __name__ == "__main__":
    sys.exit(main(sys.argv))
