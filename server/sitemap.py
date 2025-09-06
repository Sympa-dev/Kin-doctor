from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "daily"

    def items(self):
        return ['accounts:login', 'accounts:signup', 'core']  # noms des URLs dans urls.py

    def location(self, item):
        return reverse(item)
