# -*- coding: utf-8 -*-
import json
import scrapy
from scrapy import Request


def conver_int(s):
    """将字符串转换成int
    >>>conver_int(' 123')
    >>>123
    >>>conver_int('')
    >>>0
    >>>conver_int('123,456')
    >>>123456
    """

    if not s:
        return 0
    return int(s.replace(',', ''))


ci = conver_int


class DiscoverySpider(scrapy.Spider):
    name = 'sucai'
    allowed_domains = ['588ku.com']
    start_urls = ['http://588ku.com/video/1-0-0-0-hot']

    def parse(self, response):
        """处理视频列表页面"""

        # 先取出所有的视频li节点
        post_list = response.xpath("//li[contains(@class,'video-list')]")
        # 遍历Li节点
        for post in post_list:
            # 提取视频ID
            post_url = post.xpath('./a[@class="title"]/@href').get()
            # 根据ID构造url，再根据url构造request对象
            request = Request(post_url, callback=self.parse_post)
            # 设置request.meta属性，传递缩略图、视频标题
            request.meta['title'] = post.xpath('./a[@class="title"]/text()').get()
            request.meta['thumbnail'] = post.xpath(
                './div[contains(@class,"img-box")]//img[contains(@class,"lazy")]/@data-original').get()
            yield request

    def parse_post(self, response):
        """处理视频详情页"""
        post = {}
        post['title'] = response.meta['title']
        post['thumbnail'] = response.meta['thumbnail']
        try:
            # post['duration'] = response.xpath('//div[@class="timetextchelspakonoh"]/text()').get()
            post['video'] = response.xpath('//video')[0].xpath('./@src').get()
            post['view'] = response.xpath('//span[@class="fl"]/b/text()').get()
            post['down'] = response.xpath('//span[@class="fr"]/b/text()').get()
            post['mark'] = response.xpath('//a[@id="collect-btn"]/b/text()').get()
            post['format'] = response.xpath('//div[@class="fr"]//ul/li/b/text()').extract()[0]
            post['size'] = response.xpath('//div[@class="fr"]//ul/li/b/text()').extract()[1]
            post['user'] = response.xpath('//a[@class="user-name"]/text()').get()
            post['uptime'] = response.xpath('//div[@class="user-related"]/b[@class="time"]/text()').get()
        except Exception as e:
            print(e)
        finally:
            yield post
            print(post)
