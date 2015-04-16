from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^$', 'cdnscraper.views.index'),
    url(r'^resources$', 'cdnscraper.views.resources'),
    url(r'^resources/json$', 'cdnscraper.views.resourcesAsJson'),
)