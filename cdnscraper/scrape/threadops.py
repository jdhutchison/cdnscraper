import threading
"""
Thread utility functions.
"""

def executeThreads(function, urls, wwwIsSame, resources, processed, lock):
    threads = []
    for url in urls:
        t = threading.Thread(target=function, args=(url, wwwIsSame, resources, processed, lock))
        threads.append(t)
        t.start()
    return threads

def waitUntilComplete(threads):
    """
    Waits for a set of threads to complete and rejoin the spwaning thread. This call will
    block until all threads are complete.
    :param threads: [list] the set of threads to wait on
    :return: Void
    """
    if threads:
        for t in threads:
            t.join()

