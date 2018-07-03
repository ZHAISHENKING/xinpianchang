# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import random
from scrapy.exceptions import NotConfigured


class RandomProxyMiddleware(object):

    def __init__(self, settings):
        self.proxies = settings.getlist('PROXIES')
        self.stats = {}.fromkeys(self.proxies, 0)
        self.max_failed = 3

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('HTTPPROXY_ENABLED'):
            raise NotConfigured
        return cls(crawler.settings)

    def process_request(self, request, spider):
        request.meta['proxy'] = random.choice(self.proxies)
        print('use proxy: %s' % request.meta['proxy'])

    def process_response(self, request, response, spider):
        cur_proxy = request.meta['proxy']
        if response.status >= 400:
            self.stats[cur_proxy] += 1
            print('get http status %s when use proxy: %s' % \
                  (response.status, cur_proxy))
        if self.stats[cur_proxy] >= self.max_failed:
            self.remove_proxy(cur_proxy)
        return response

    def process_exception(self, request, exception, spider):
        cur_proxy = request.meta['proxy']
        print('raise exption: %s when use %s' % (exception, cur_proxy))
        self.remove_proxy(cur_proxy)
        del request.meta['proxy']
        return request

    def remove_proxy(self, proxy):
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            print('proxy %s removed from proxies list' % proxy)

