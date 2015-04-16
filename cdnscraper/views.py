import re
import logging

from django.shortcuts import render
from django.http import JsonResponse

from cdnscraper.scrape import net
from cdnscraper.scrape import processor
from cdnscraper.scrape import urls as customUrls


"""
View logic.
"""
DOMAIN_REGEX = '^([a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]\.)+[a-zA-Z]{2,}(?:\.[a-z]{2})?$'

def index(request):
    return render(request, 'index.html')


def resources(request):
    results = __getResourcesForDomain(request)
    return render(request, 'resources.html', results)


def resourcesAsJson(request):
    results = __getResourcesForDomain(request)
    return JsonResponse(results)


def __getResourcesForDomain(request):
    domain = __getDomainFromRequest(request)
    result = {'domain': domain}

    try:
        # Validate domain
        domain = customUrls.stripDomain(domain)
        if not re.compile(DOMAIN_REGEX).match(domain):
            result['error'] = 'Domain is not valid (fails regex validation)'
        else:
            isWwwSame = net.isWwwCname(domain)
            scheme = net.determineScheme(domain, isWwwSame)
    except Exception, e:
        logging.error('Unable to get resources for %s', domain, exc_info=True)
        result['error'] = e.message

    if 'error' not in result:
        try:
            resources = []
            url = scheme + '://' + domain + '/'
            processor.multiThreadedProcessor(url, True, resources)
            result['resources'] = resources
        except Exception, e:
            logging.error('Unable to get resources for %s', domain, exc_info=True)
            result['error'] = e.message

    return result

def __getDomainFromRequest(request):
    if request.method == 'POST' and request.POST:
        return request.POST.get('domain')
    elif request.method == 'GET' and request.GET:
        return request.GET.get('domain')
    else:
        return ''
