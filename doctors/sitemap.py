from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class DoctorStaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return [
            'doctors:dashboard',
            'doctors:appointments',
            'doctors:consultations',
            'doctors:patients',
            'doctors:profile',
        ]

    def location(self, item):
        return reverse(item)
