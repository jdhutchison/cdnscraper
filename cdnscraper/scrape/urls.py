import urlparse

def isInDomain(base, uri, wwwIsSame=True):
    """
    Checks a resource is part of the same domain or not. Does not validate that the resource
    exists.
    :param base: [string] the base url containing the domain in question
    :param uri: [string] URI of a resource to test
    :param wwwIsSame: Is www.domain the same as domain (e.g. is there a CNAME record for www)? Defaults
    to True.
    :return: [boolean] True if URI is for a resource that resides on the given domain
    """
    if uri is None or base is None:
        return False
    elif len(uri) > 0 and uri.startswith('/') and not uri.startswith('//'): #relative path
        return True
    else:
        return sameDomain(urlparse.urlparse(base).netloc, urlparse.urlparse(uri).netloc, wwwIsSame)

def sameDomain(domain, candidate, wwwIsSame=True):
    """
    Tests to see if a candidate domain is the same as an official test domain. The wwwIsSame parametre
    can be used to declare that www.somedomain.com is the same as domain.com and that they should
    not be treated differently.

    :param domain: [string] the domain to test against
    :param candidate: [string] the possible match
    :param wwwIsSame: Is www.domain the same as domain (e.g. is there a CNAME record for www)? Defaults
    to True.
    :return: [boolean] True if candidate is the same as a given domain
    """
    # If the WWW part is irrelevant then remove it if it exists
    if wwwIsSame:
        if domain.startswith('www.'):
            domain = domain[4:]
        if candidate.startswith('www.'):
            candidate = candidate[4:]

    return domain == candidate

def removeQueryString(url):
    """
    Removes any query string and target (anything after a #) from a URL.
    :param url: [string] the URL to tidy up.
    :return: The URL without the query stirng (anything left of the ?)
    """
    if url is None:
        return None

    index = url.find('?')
    if index > -1:
        url = url[:index]
    index = url.find('#')
    if index > -1:
        url = url[:index]

    return url


def getExtnesionOfUrl(url):
    """
    Identfies the file extension of the resource at a given URL if it is possible. The
    extension is taken to be the rightmost portion of the path (excluding the last .).
    :param url: [string] the URL to get extension for
    :return: None if no extension or None/empty string is given as an input
    """

    if url is None or len(url) == 0:
        return None

    parsedUrl = urlparse.urlparse(url)
    if parsedUrl.path.find('.') > -1:
        return parsedUrl.path.split('.')[-1]
    else:
        return None

def joinurl(base, url):
    """
    A wrapper around Python's urlparse.urljoin function to check for errors
    with a .. at the start of the path
    :param base: [string] the base url, the domain
    :param url: [string] the url to join on, the path
    :return: [string] None if there is no base, or base if there is no url, or the output of
    urlparse.urljoin filtered to remove .. at the start or a URL path.
    """
    if base is None:
        return None

    elif url is None:
        return base

    else:
        joined = urlparse.urljoin(base, url)
        # Check for bad path
        if urlparse.urlparse(joined).path.startswith('/../'):
            joined = joined.replace('/../', '/')
        return joined

def stripDomain(domain):
    """
    Removes any scheme information and www. from the front if present.

    :param domain: [string] domain/url to strip of not needed bits.
    :return: [string] altered domain
    """
    if domain.find('://') > -1:
        domain == domain[(domain.find('://') + 3):]
    if domain.startswith('www.'):
        domain = domain[4:]

    return domain