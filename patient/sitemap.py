from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class PatientStaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return [
            'patient:dashboard',
            'patient:find_doctor',
            'patient:appointments',
            'patient:documents',
            'patient:messages',
            'patient:medical_records',
            'patient:prescriptions',
            'patient:billing',
        ]

    def location(self, item):
        return reverse(item)
