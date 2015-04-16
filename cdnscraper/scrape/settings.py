"""
Contains key configuration settings used throughout the scraper/spider code.
"""

# How many threads to have running concurrently when the scraper is in operation.
# More threads may be created and commenced running but those that do so will be
# blocked until other threads have finnished.
MAX_CONCURRENT_PROCESSES = 20

# How "Thorough" the spider/scraper is. If true, the scraper will process each URL
# individually, checking the content type by requesting meta data on the URL from the
# server (using a HEAD request). If false then the scraper will try and make educated
# guesses about what the content type is, and will only request a file is it is likely
# further processing is needed (i.e. for HTML or CSS resource types).
#
# Having this set to true is slower but has less chance of error, however the likely-
# hood of errors with False is low.
THOROUGHNESS = False