# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class PostItem(scrapy.Item):
    """保存视频信息的item"""
    table_name = 'posts'
    pid = Field()
    title = Field()
    thumbnail = Field()
    preview = Field()
    video = Field()
    category = Field()
    created_at = Field()
    duration = Field()
    play_counts = Field()
    like_counts = Field()
    description = Field()
    video_format = Field()


class CommentItem(scrapy.Item):
    """评论信息"""

    table_name = 'comments'
    commentid = Field()
    pid = Field()
    cid = Field()
    avatar = Field()
    uname = Field()
    created_at = Field()
    like_counts = Field()
    content = Field()
    reply = Field()


class ComposerItem(scrapy.Item):
    """用户信息"""

    table_name = 'composers'
    cid = Field()
    banner = Field()
    avatar = Field()
    name = Field()
    verified = Field()
    intro = Field()
    like_counts = Field()
    fans_counts = Field()
    follow_counts = Field()
    location = Field()
    career = Field()


class CopyrightItem(scrapy.Item):
    """著作权，视频和作者的对应关系"""
    table_name = 'copyrights'
    pcid = Field()
    pid = Field()
    cid = Field()
    roles = Field()
