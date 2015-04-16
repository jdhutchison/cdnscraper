"""
URL sensitive List operations.
"""
import urlparse

def urlInCollection(url, collection, wwwIsSame=True):
    """
    Checks to see if a URL is in a collection of URLs, checking to see if both the www. and non www.
    version are present if required.
    :param url: [string] the URL to check for
    :param collection: [list] The set of all URLs
    :param wwwIsSame: [boolean] True if www.someurl and someurl should be checked for
    :return: [boolean] True if URL is found in collection
    """
    if not wwwIsSame:
        return __directorySensitiveCheck(url, collection)

    urlFragments = urlparse.urlparse(url)

    # If www.domain and domain are the same then at first look to see
    # if there is a match and if not try the alternative
    if __directorySensitiveCheck(url, collection):
        return True

    if urlFragments.netloc.startswith('www.'):
        url = urlFragments.scheme + '://' + urlFragments.netloc[4:] + urlFragments.path
    else:
        url = urlFragments.scheme + '://www.' + urlFragments.netloc + urlFragments.path

    # Check for directory duplicates (i.e. check for x and x/)
    return __directorySensitiveCheck(url, collection)

def __directorySensitiveCheck(url, collection):
    """
    Check for directory duplicates (i.e. check for x and x/ being present).
    :param url: the URL to look for
    :param collection: [list] the set of URLs to look in
    :return: [boolean] True if URL is present, or an equivalent URL is present
    """
    if url in collection:
        return True
    elif url[:-1] in collection:
        return True
    else:
        return (url + '/') in collection

def addUrlsNotIn(new, existing, isWwwSame):
    """
    Finds all urls in new that do not match (or are equivalent to) a url in the existing collection.

    The result is all unqiue URLs.

    :param new: [list] All new URLs to check
    :param existing: [list] What to check against
    :param isWwwSame: [boolean] if True urls with www. in front will be will have the www ignored
    :return: [list] all exsting URLs with any new, unique URLs added.
    """
    for url in new:
        if not urlInCollection(url, existing, isWwwSame):
            existing.append(url)
    return existing

def removeUrlsIn(removeFrom, checkAgainst, wwwIsSame):
    """
    Removes all URLs from one list of URLs that are in another list, in effect returning
    list a - list b. The returned list is new and the input parameters are not altered.

    :param removeFrom: [list] the list to filter
    :param checkAgainst: [list] What to check against
    :param wwwIsSame: [boolean] if True urls with www. in front will be will have the www ignored
    :return: [list] a new list containing all URLs that are in removeFrom but not in checkAgainst
    """
    clean = []
    for url in removeFrom:
        if not urlInCollection(url, checkAgainst, wwwIsSame):
            clean.append(url)
    return list(set(clean))

def filterForUniqueUrls(list, wwwIsSame):
    """
    Removes URLs from a list that have an equivalent URL earlier in the list. The result will
    contain URLs that do not refer to the same resource.

    The return value is a new list and the list original passed in is not altered.

    :param list: [list] the URLs to filter through
    :param wwwIsSame: [boolean] if True urls with www. in front will be will have the www ignored
    :return: [list] A new list featuring unique URLs from the input list
    """
    filtered = []
    for url in list:
        if not urlInCollection(url, filtered, wwwIsSame):
            filtered.append(url)
    return filtered
