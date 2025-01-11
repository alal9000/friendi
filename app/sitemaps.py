from django.contrib.sitemaps import Sitemap
from django.shortcuts import reverse
from events.models import Event

class StaticViewSitemap(Sitemap):
  def items(self):
    return ['home', 'about', 'create', 'recommendations', 'contact']

  def location(self, item):
    if isinstance(item, str):
          return reverse(item)
    else:
          return None  



