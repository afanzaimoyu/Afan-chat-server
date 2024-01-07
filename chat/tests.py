import re
import requests
long_str = "其中包含一个URL www.baidu.com，一个带有端口号的URL http://www.jd.com:80, 一个带有路径的URL http://mallchat.cn, " \
           "还有美团技术文章https://mp.weixin.qq.com/s/hwTf4bDck9_tlFpgVDeIKg,https://www.bing.com/search?q=re+%5Cw+%E5%95%8A%E5%95%8A%E5%95%8A&qs=n&form=QBRE&sp=-1&lq=0&pq=re+%5Cw+a%27a%27a&sc=7-11&sk=&cvid=1C3CE2C7A6574B9C83C3EBF9F92608E8&ghsh=0&ghacc=0&ghpl="
PATTERN = re.compile(r"(https?://)?(www\.)?([\w_-]+(?:\.[\w_-]+)+)([\w@?^=%&:/~+#-]*)", re.U)
# PATTERN = re.compile(r"(https?://)?(www\.)?([^\u4e00-\u9fa5]+)([\w.,@?^=%&:/~+#-]*)", re.S)
match_list = [''.join(m) for m in re.findall(PATTERN, long_str)]
print(match_list)
head = {
    "User-Agent":'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
}
r = requests.get('http://www.baidu.com',headers=head)
r.encoding = 'utf-8'
print(r.text)