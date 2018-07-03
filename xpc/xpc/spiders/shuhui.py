# -*- coding: utf-8 -*-
import json
import scrapy
from scrapy import Request


class DiscoverySpider(scrapy.Spider):
    name = 'shuhui'
    allowed_domains = ['ishuhui.com']
    start_urls = ['http://www.ishuhui.com/cartoon']

    def parse(self, response):
        """处理漫画列表页面"""
        post_url = "http://api.ishuhui.com/cartoon/category_latest/ver/%s.json"
        # 获取列表页面id，{'a': '97053263', 's': '97053263'}
        pid = json.loads(response.xpath('//meta[@name="ver"]/@content').get())['a']
        request = Request(post_url % pid, callback= self.ajaxdata)
        # post_list = response.xpath('//div[@class="cartoon-card-wp"]/div[@class="cartoon-card"]')
        yield request

    def ajaxdata(self, response):
        data = json.loads(response.text)
        infolist=data['data']['data']
        item = {}
        for i in infolist:
            item['book'] = i['book']
            item['title'] = i['title']
            item['id'] = i['id']
            item['number'] = i['number']
            item['name'] = i['name']
            item['thumb'] = 'http://pic01.ishuhui.com' + i['thumb'].split('upload')[1]
            yield item
