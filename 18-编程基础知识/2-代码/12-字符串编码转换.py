# 字符串编码转换
# （一）ASCII、GBK、GBK2312、UTF-8介绍
# 最早的字符串编码是美国标准信息交换码，即ASCII。它仅对10个数字、26个大写英文字母、26个小写英文字母及一些其他符号进行了编辑。ASCII码最多只能表示256个符号，每个字符占一个字节。
# 随着信息技术的发展，各国的文字都需要进行编码，于是出现了GBK、GBK2312、UTF-8编码等。其中GBK、GBK2312是我国制定的中文编码标准，使用1个字节表示英文字母，2个字节表示中文字符。UTF-8是国际通用的编码，对全世界所有国家需要用到的字符都进行了编码。UTF-8采用一个字节表示英文字符、3个字节表示中文。
# 在Python3.X中，默认采用的编码格式为UTF-8，采用这种编码有效解决了中文乱码的问题。
# （二）将汉字用gbk格式编码得到网址中使用的乱码
# 举例：输入不同的电影名，观察搜索结果页面的URL：《无名之辈》的搜索结果URL：
# http://s.ygdy8.com/plus/s0.php?typeid=1&keyword=%CE%DE%C3%FB%D6%AE%B1%B2
# keyword后面的乱码代表的是电影名

# 请阅读以下代码，注意注释哦：
a= '无名之辈'
b= a.encode('gbk')
# 将汉字，用gbk格式编码，赋值给b
print(quote(b))
# quote()函数，可以帮我们把内容转为标准的url格式，作为网址的一部分打开

# 输入不同的电影名，观察搜索结果页面的URL：
# 《无名之辈》的搜索结果URL：http://s.ygdy8.com/plus/s0.php?typeid=1&keyword=%CE%DE%C3%FB%D6%AE%B1%B2
# 《神奇动物》的搜索结果URL：http://s.ygdy8.com/plus/s0.php?typeid=1&keyword=%C9%F1%C6%E6%B6%AF%CE%EF
# 《狗十三》 的搜索结果URL：http://s.ygdy8.com/plus/s0.php?typeid=1&keyword=%B9%B7%CA%AE%C8%FD
# 观察URL，不难发现：http://s.ygdy8.com/plus/s0.php?typeid=1&keyword= 这些都是一样的，只不过不同的电影名对应URL后面加了一些我们看不懂的字符