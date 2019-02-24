#!/usr/bin/env python3

import sys
import multiprocessing
from multiprocessing.dummy import Pool
import time

def job(i):
    print(i, "starting my sleep")
    time.sleep(2)
    return i

def main(argv):

    t1 = time.time()

    pool = Pool(processes = 2)

    for i in pool.imap_unordered(job, range(4)):
        print(i)

    print("Took:", str(time.time() - t1))

    print("Done")

if __name__ == "__main__":
    sys.exit(main(sys.argv))
