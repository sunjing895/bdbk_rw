import requests
from bs4 import BeautifulSoup
import threading
import re
import time

# 页面请求
def GetHtml(url,head):
    try:
        html = requests.get(url,headers=head,timeout=30)
        html.raise_for_status()
        html.encoding = html.apparent_encoding
        return html
    except:
        return -1

# 筛选出人物词条页面并提取信息
class GetPersonHtml(threading.Thread):
    def __init__(self,start_num,end_num,html_list = []):
        threading.Thread.__init__(self)
        self.start_num=start_num
        self.end_num=end_num
        self.html_list=html_list

    def run(self):
        hd = {
            'user-agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'X-request-with': 'XMLHttpRequest'}

        temp = self.start_num
        while temp <= self.end_num:
            temp += 1
            url = "http://baike.baidu.com/view/" + str(temp)
            html = GetHtml(url, hd)
            if html == -1 or html.status_code != 200:
                print("页面错误")
                continue

            patten = re.compile('<span class="taglist">(.)人物', re.M | re.I | re.S)  #确定页面为词条
            if patten.search(html.text):
                html_list.append(url)
                if GetPersonData(html) == 0:
                    print('基本信息获取成功'+"             " + url)
                else:
                    print('网页中无所需信息'+"             " + url)
                continue
            print("不是人物词条")

# 人物词条基本信息获取
def GetPersonData(html):

    return 0

if __name__=="__main__":
    time1 = time.time()
    html_list = []  # 存储人物词条的链接

#   连接数据库，读取开始页面编号，以从上一次停止处继续爬站
    start_num = 0   #页面开始编号
    end_num = 100   #页面结束编号
#   .....................................................

#   开启多线程爬取人物词条
    thread_num = 10 #爬站线程数量,至少为2个
    if((end_num - start_num)%thread_num == 0):
        thread_num-=1
    distance = int((end_num - start_num)/thread_num)
    L = list(range(start_num,end_num,distance))
    L[-1] = end_num+1 #构造各个线程爬站的范围
    thread = []
    thread_lock=threading.Lock

    for i in range(thread_num):
        t = GetPersonHtml(L[i],L[i+1],html_list)
        thread.append(t)
        t.start()

    for t in thread:
        t.join()
#   ......................

#   将任务词条链接写入文件
    f=open("person_list.txt",'a+')
    for item in html_list:
        f.write(item)
        f.write('\n')

    time2 = time.time()
    T="线程数： "+str(thread_num)+"总耗时： "+str((time2-time1)/60)+'分钟'
    f.write(T)
    print(T)
    f.close()
#   ......................



