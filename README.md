# 新片场爬虫
### 1. 防止url被过滤

```python
# dont_filter: 本次请求不执行过滤重复url
request = Request(url, dont_filter=True)
```

### 2.防止自定义的cookie被修改

**当爬虫需要分页爬取时，携带cookie爬取，所携带的cookie可能会被scrapy中自带的httpCookie.py中的方法所修改，在保证不修改源码的情况下只需修改spider文件中的`start_requests`方法**

```python
# 禁止合并cookie
request.meta['dont_merge_cookies'] = True
```

spiders/xx.py

```python
    def start_requests(self):
        """重载scrapy.Spider类的start_requests函数，以设置meta信息"""
        for url in self.start_urls:
            # dont_filter：本次请求不执行过滤重复url的逻辑
            request = Request(url, dont_filter=True)
            request.meta['dont_merge_cookies'] = True
            yield request
```

### 3. 分页

分页有多种实现方式，这里使用的是抓取当前页面显示的分页链接，然后进去爬取内容并继续返回新的链接，直到没有新的页面

<img src="http://qiniu.s001.xin/spider/fenye.png">

```python
# 当前页的链接列表
other_pages = response.xpath('//div[@class="page"]/a/@href').extract()

for page in other_pages:
    request = Request(page, callback=self.parse)
    # 不要合并cookies，这样可以使用settings里设置的cookies
    request.meta['dont_merge_cookies'] = True
    yield request
# 也可以简写
yield from [response.follow(page) for page in other_pages]
```

### 4.将字符串转成int

```python
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

# 使用时
ci(response.xpath('//span/text()').get())
```

### 5.连接数据库存储数据

**我们的需求是希望爬到的数据有重复就更新，没有就添加**

**而且尽可能的使代码优雅，表中字段过多时应想办法简化，不重复造轮子**



当爬虫数据插入数据库时，实际上是在执行Insert Into语句

```python
# 示例
insert into table
			(player_id,award_type,num)
    		values(20001,0,1) on  DUPLICATE key update
        	player_id=20001,award_type=0,num=1;
```



显然，比较麻烦的是

1.字段名都得输出

2.键值一一对应

3.每个表都得重复此操作

所以可以把表名、键、值提取出来

```python
# pipelines.py
class MysqlPipeline(object):

    def __init__(self):
        # 连接
        self.conn = None
        # 游标
        self.cur = None

    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='',
            db='数据库名',
            charset='utf8mb4',
        )
        self.cur = self.conn.cursor()

    def process_item(self, item, spider):
        # 判断是否有table_name,这里的table_name是表名
        if not hasattr(item, 'table_name'):
            return item
        # 键
        cols = item.keys()
        # 值
        values = list(item.values())
        # 四个括号分别对应 表名、键的占位符、值的占位符%s、解析键
        # 最后一个虽然解析了键 但又生成新的值的占位符%s
        sql = "INSERT INTO `{}` ({})"\
            "VALUES ({}) ON DUPLICATE KEY UPDATE {}".format(
                item.table_name,
                ','.join(['`%s`' % col for col in cols]),
                ','.join(['%s'] * len(cols)),
                ','.join('`{}`=%s'.format(col) for col in cols)
            )
        # 解析值,有两个地方占位,所以values*2
        self.cur.execute(sql, values * 2)
        self.conn.commit()
        print(self.cur._last_executed)
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
```

Items.py

```python
class PostItem(scrapy.Item):
    # 将每个class对应的表赋值给table_name,在pipelines中调用
    table_name = 'posts'
    pid = Field()
    title = Field()
```

### 6.ip代理

ip代理最大的问题是检测ip的可用性

<img src="http://qiniu.s001.xin/spider/ip.png" width="500">

代码实现

middlewares.py

```python
# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html
import random
from scrapy.exceptions import NotConfigured


class RandomProxyMiddleware(object):

    def __init__(self, settings):
        # 获取settings中的ip,每个ip初始状态为0 最大失败次数为3
        self.proxies = settings.getlist('PROXIES')
        self.stats = {}.fromkeys(self.proxies, 0)
        self.max_failed = 3

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool('HTTPPROXY_ENABLED'):
            raise NotConfigured
        return cls(crawler.settings)

    def process_request(self, request, spider):
        # ip池中随机选择
        request.meta['proxy'] = random.choice(self.proxies)
        print('use proxy: %s' % request.meta['proxy'])

    def process_response(self, request, response, spider):
        # 用response.status的值来判断请求是否成功
        # cur_proxy是请求时的ip
        cur_proxy = request.meta['proxy']
        if response.status >= 400:
            self.stats[cur_proxy] += 1
            print('get http status %s when use proxy: %s' % \
                  (response.status, cur_proxy))
        # 满足失败次数 从代理池中删除,remove_proxy方法在最下边定义
        if self.stats[cur_proxy] >= self.max_failed:
            self.remove_proxy(cur_proxy)
        return response
	# 因为scrapy是异步并发,所以存在一个失败ip多次请求的情况,失败次数大于3次删除ip之后,其余请求还会返回来删除ip,此时就会报错
    # 简单来说就是 两个人同时取一张卡中的钱,其中一个人取完了钱，另一边没有及时刷新就会报错
    # 所以在此处将此ip的请求一并删除
    def process_exception(self, request, exception, spider):
        cur_proxy = request.meta['proxy']
        print('raise exption: %s when use %s' % (exception, cur_proxy))
        self.remove_proxy(cur_proxy)
        del request.meta['proxy']
        return request
	# 删除ip
    def remove_proxy(self, proxy):
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            print('proxy %s removed from proxies list' % proxy)

```

Settings.py

<img src="http://qiniu.s001.xin/spider/proxy.png" height="300px">

### 7.使用tinyproxy在自己的服务器开启ip代理

**安装**

```bash
# centos
sudo yum install tinyproxy
# ubuntu
sudo apt install tinyproxy
```

打开配置文件

```bash
vim /etc/tinyproxy/tinyproxy.conf
```

**搜索并修改以下配置**

```bash
# 注释下面这行，大概在第210行
Allow 127.0.0.1
# 修改端口号
Port 1888
```

修改完保存退出

重启服务:

```bash
systemctl restart tinyproxy
```

查看日志文件的路径

```bash
tail -f /var/log/tinyproxy/tinyproxy.log
```
