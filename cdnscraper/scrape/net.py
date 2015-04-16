"""
Functions that involve network/internet calls.
"""
import logging
import urlparse
import requests

import dns.resolver

from requests.exceptions import ConnectionError
from cdnscraper.scrape import urls


def fetchResource(url):
    """
    A failsafe function to get the contents of a URL. Errors (of any sort) are handled and
    signalled by None being returned.
    :param url: [string] the URL of the resource to fetch
    :return: [string] the contents of the URL/resource as a string OR None if any error occurs.
    """
    try:
        return requests.get(url)
    except:
        logging.warn('Unable to fetch contents at %s', url, exc_info=True)
        return None


def checkContentTypeOnServer(url):
    """
    Checks the content type (as relayed via the server) of the resource at a given URL. This
    function is failsafe - errors will be caught and None returned. A HEAD request is made
    and the contents are not fetched at all.

    :param url: [string] the URL of the resource to check the content type of
    :return: [string] None if request fails to determine a content type or the content type as
    returned from the server.
    """
    try:
        logging.debug('Attempting to get content type of %s from server...', url)
        response = requests.head(url)
        contentType = response.headers['content-type']
        return contentType.split(';')[0] # Remove any charset data
    except:
        logging.warn('Unable to check content type for %s', url, exc_info=True)
        return None

def determineScheme(domain, isWWWSame=True, timeout=3):
    """
    Tries to connect to the website to determine the scheme (protocol) to use - either http or https.

    This method is fail fast and will raise an Exception. This is to provide a meaningful error message
    on the front end.

    :param domain: [string] domain to get scheme for
    :param isWWWSame [boolean] do not raise error on redirect to/from www if True (defaults to True).
    :param timeout: [integer] the number of seconds to try for before a connection attempt times out.
    Defaults to 3
    :return: [string] http or https, depending on how to connect
    """
    logging.debug('Trying to connect to %s via http or https', domain)
    try:
        response = requests.get('http://' + domain + '/')
    except ConnectionError, e:
        logging.warn('Unable to connect to %s using http. Trying https...', domain)
        if __isHttpsReachableForDomain(domain):
            return 'https'
    except Exception, e:
        logging.error('Error trying to connect to %s', domain, exc_info=True)
        raise Exception('Error trying to connect to %s: %s' % (domain, e.message))

    if response.status_code != 200:
        raise Exception('Unable to connect to %s. Instead get status code %s' % (domain, response.status_code))

    parsedUrl = urlparse.urlparse(response.url)
    if not urls.sameDomain(domain, parsedUrl.netloc, isWWWSame):
        logging.warn('Attempt to connect to %s ended up in a different domain: %s', domain, parsedUrl.netloc)
        raise Exception('%s redirected to a completely different domain, %s!' % (domain, parsedUrl.netloc))
    else:
        logging.debug('Connected to %s using %s', domain, parsedUrl.scheme)
        return parsedUrl.scheme

def __isHttpsReachableForDomain(domain):
    """
    Checks if an HTTPS connection can be made to a given domain. Fails fast with an exception
    if there are issues making the request.
    :param domain: [string] what to connect to on https
    :raises Exception on any sort of fatal error or simply not being able to connect over https.
    :return: True if connection can be made using https, never returns false (will throw exception instead).
    """
    try:
        # Try fallback to https
        response = requests.get('https://' + domain + '/')
    except Exception, e:
        logging.error('Error trying to connect to %s via https', domain, exc_info=True)
        raise Exception('Error trying to connect to %s: %s' % (domain, e.message))
    if response.status_code == 200:
        logging.debug('Successfully connected to %s over https', domain)
        return True
    else:
        logging.warn('Attempt to connect to %s using https failed', domain)
        raise Exception('Unable to connect to %s using either http or https' % domain)

def isWwwCname(domain):
    """
    Checks if there is a CNAME refering domain to www.domain or vice versa.

    :param domain: [string] the domain to check
    :raise Exception if unable to connect to a DNS server or find any DNS records
    :return: [boolean] True if there is a cname for the domain.
    """
    logging.debug('Testing for CNAME usage for %s', domain)

    dnsRecord = dns.resolver.query('www.' + domain, 'A')
    if dnsRecord.qname != dnsRecord.canonical_name:
        logging.debug('CNAME in use for www.%s -> %s', domain, domain)
        return True

    dnsRecord = dns.resolver.query(domain, 'A')
    if dnsRecord.qname != dnsRecord.canonical_name:
        logging.debug('CNAME in use for %s -> www.%s', domain, domain)
        return True

    logging.debug('No CNAME in use for %s', domain)
    return False