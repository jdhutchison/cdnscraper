import logging
import re
import threading
from itertools import count

from bs4 import BeautifulSoup


from cdnscraper.scrape import listops
from cdnscraper.scrape.net import fetchResource, checkContentTypeOnServer
from cdnscraper.scrape import filetypes
from cdnscraper.scrape.settings import MAX_CONCURRENT_PROCESSES, THOROUGHNESS
from cdnscraper.scrape import threadops
from cdnscraper.scrape import urls

CSS_RESOURCE = 'text/css'
HTML_RESOURCE = 'text/html'
HTML_EXTENSIONS = ('html', 'htm')
NEED_CHECKING = (HTML_RESOURCE, CSS_RESOURCE)

CSS_URL_REGEX = 'url\\(.+?\\)'

def genericResourceProcessor(url, wwwCName, contentParsingFunction):
    """
    Finds references (that is, URLs) to resources within the content of some resource.
    :param url: [string] the URL of the resource to parse
    :param wwwCName: [boolean] If www.domain and domain are considered the same (is there a www CNAME record)
    :param contentParsingFunction: [function] a function that takes one argument - the URL of a resource - loads
    the resource, and identifies all the other URLs within the contents
    :return: [list] all the URLs found within the contents. Empty list if the contents cannot be parsed.
    """
    foundResources = []
    if url is None or len(url) == 0:
        return foundResources

    for match in contentParsingFunction(url):
        # Check if URL is local or from another domain
        newUrl = urls.joinurl(url, match)
        newUrl = urls.removeQueryString(newUrl)
        if urls.isInDomain(url, newUrl, wwwCName):
            if newUrl not in foundResources:
                foundResources.append(newUrl)

    return foundResources


def cssContentParser(url):
    """
    Identifies URLs in CSS content that is fetched from the server.
    :param url: [string] the URL of the CSS resource to parse
    :return: [list] all the URLs found in the CSS.
    """
    response = fetchResource(url)
    if response is None:
        return []
    resourceRegex = re.compile(CSS_URL_REGEX)
    matches = []
    for match in resourceRegex.findall(response.text):
        matches.append(match[4:-1].replace('"', '').replace("'", '')) # remove url()
    return matches

def htmlContentParser(url):
    """
    Fetches some HTML content and finds all links/references to other resources within it.
    :param url: [string] The URL of the html to go and get
    :return: [list] the (absolute) URLs of all links within the loaded content. Empty list
    if the content could not be read.
    """
    resources = []
    attributesToCheck = ('src', 'href')
    response = fetchResource(url)
    if response is None:
        return []

    dom = BeautifulSoup(response.text)
    for attribute in attributesToCheck:
        for element in dom.select('[%s]' % attribute):
            resources.append(element.get(attribute))
    return resources

def identifyContentType(url, checkOnServer=True):
    """
    Attempts to figure out the content type of a resource at a URL by the extension
    or by checking directly with the hosting server if neccesary. This doubles as a nice
    check to see if the resource exists and is accessible.

    :param url: [string] the URL to get the content type for
    :return: [string] the content type of the resource or None if it cannot be
    determined. If no URL is passed then None is returned.
    """
    if url is None or len(url) == 0:
        return None

    extension = urls.getExtnesionOfUrl(url)

    # No extension means it is likely dynamic HTML content
    if extension is None or len(extension) == 0:
        return HTML_RESOURCE
    # Check for the importnt types quickly
    elif extension in HTML_EXTENSIONS:
        return HTML_RESOURCE
    elif extension == 'css':
        return CSS_RESOURCE
    elif checkOnServer:
        return checkContentTypeOnServer(url)
    # Try to guess using the extension
    elif extension in filetypes.FILE_EXTENSION_MAP:
        return filetypes.FILE_EXTENSION_MAP[extension]
    # Fallback assumption is tht it is dynamic content
    else:
        return HTML_RESOURCE

def alternateProcess(url, wwwIsSame, thorough):
    """
    Processes a resource by identifying what other resources in the same domain the resource at a given
    URL points to.

    :param url: the url of a resource to check
    :param wwwIsSame: [boolean] if www.domain and domain are considered the same
    :return: [list] The absolute URLs of any resources that this resource points to that are hosted
    on the same domain. Will return None if there is an error.

    """
    logging.debug('Processing %s', url)
    contentType = identifyContentType(url, thorough)
    resources = []
    try:
        if contentType == HTML_RESOURCE:
            links = genericResourceProcessor(url, wwwIsSame, htmlContentParser)
        elif contentType == CSS_RESOURCE:
            links = genericResourceProcessor(url, wwwIsSame, cssContentParser)
            resources.append(url)
        else:
            logging.debug('Content type of %s is %s...it\'s a static resource, no need to process',
                          url, contentType)
            return ([url], [])

        # More aggresively identifying things as resources if appropriate
        if not thorough:
            resources.extend(__identifyResourcesThatDontNeedProcessing(links))
            links = [item for item in links if item not in resources]

        return (listops.filterForUniqueUrls(resources, wwwIsSame), listops.filterForUniqueUrls(links, wwwIsSame))

    except Exception:
        logging.error('An error occured when processing %s', url, exc_info=True)


def __identifyResourcesThatDontNeedProcessing(links):
    static = []
    for url in links:
        contentType = identifyContentType(url, False)
        if contentType  not in NEED_CHECKING:
            static.append(url)

    return static

def singleThreadedProcessor(url, wwwCName):
    toProcess = [url]
    resources = []
    processed = []
    while toProcess:
        url = toProcess.pop()
        processed.append(url)
        newResources, newLinks = alternateProcess(url, wwwCName, False)
        toProcess = listops.addUrlsNotIn(newLinks, toProcess, wwwCName)
        resources = listops.addUrlsNotIn(newResources, resources, wwwCName)
        toProcess = listops.removeUrlsIn(toProcess, processed, wwwCName)
        logging.info('For %s, there were %d resources found.', url, len(newResources))
    return resources



def multiThreadedProcessor(url, wwwCName, resources=[], processed=[],
                           lock=threading.BoundedSemaphore(MAX_CONCURRENT_PROCESSES)):

    if listops.urlInCollection(url, processed, wwwCName):
        return

    lock.acquire()
    # Need to check both before and after the lock has been aquired
    if listops.urlInCollection(url, processed, wwwCName):
        lock.release()
        return

    threads = None
    try:
        logging.debug('Checking %s for resources', url)
        found, links = alternateProcess(url, wwwCName, THOROUGHNESS)
        processed.append(url)
        resources = listops.addUrlsNotIn(found, resources, wwwCName)
        toProcess = listops.removeUrlsIn(links, processed, wwwCName)
        logging.debug('From %s found %d resources and %d links. Resources: [%s], Links: [%s]',
                      url, len(found), len(toProcess), ','.join(found), ','.join(toProcess))
        threads = threadops.executeThreads(multiThreadedProcessor, toProcess, wwwCName, resources, processed, lock)
    except Exception, e:
        logging.error('Processing failed for %s. Throwing exception upwards', url)
        raise e
    finally:
        lock.release()
        threadops.waitUntilComplete(threads)