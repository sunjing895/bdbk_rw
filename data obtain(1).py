import requests
import re
import time
import multiprocessing
import pymongo

# 页面请求
def GetHtml(url,head):
    try:
        html = requests.get(url,headers=head,timeout=30)
        html.raise_for_status()
        html.encoding = html.apparent_encoding
        return html
    except:
        return html.status_code

# 筛选出人物词条页面并提取信息（多进程类）
class Get_PersonHtml(multiprocessing.Process):
    def __init__(self,start_num,end_num,process_lock):
        multiprocessing.Process.__init__(self)
        self.start_num=start_num
        self.end_num=end_num
        self.html_list=[]   #存储本进程爬取的任务词条链接
        self.process_lock=process_lock

    def run(self):
        hd = {
            'user-agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'X-request-with': 'XMLHttpRequest'}

        #   连接数据库
        myclient = pymongo.MongoClient('mongodb://localhost:27017')
        db = myclient.person_data
        my_dict = db.data
        #   ..........................

        temp = self.start_num
        index = True
        while temp <= self.end_num:
            temp += 1
            url = "http://baike.baidu.com/view/" + str(temp)
            html = GetHtml(url, hd)
            if type(html)==int:
                print("页面错误code_status = "+html+'              '+url)
                if html >= 500 & index:
                    temp -= 1
                    index = False   #为由于服务器错误而导致的页面请求错误提供一次重请求机会
                continue
            index = True

            patten = re.compile('<span class="taglist">(.)人物', re.M | re.I | re.S)  #确定页面为词条
            if patten.search(html.text):
                self.html_list.append(url)
                if GetPersonData(html,temp,my_dict) == 0:
                    print('基本信息获取成功'+"             " + url)
                else:
                    print('网页中无所需信息'+"             " + url)
                continue

        # #   将人物词条链接写入文件
        # self.process_lock.acquire()
        # f = open("person_list.txt", 'a+')
        # for item in self.html_list:
        #     f.write(item)
        #     f.write('\n')
        # f.close()
        # self.process_lock.release()
        # #   ......................


# 人物词条基本信息获取
def GetPersonData(html,url_info,my_dict):
    patten = re.compile(r'''<dt class="basicInfo-item name">(.+?)</dt>.?<dd class="basicInfo-item value">(.+?)</dd>''',
                        re.S | re.M)
    Tuple = patten.findall(html.text)
    if len(Tuple) == 0:   #页面中没有基本的信息直接返回-1
        return -1
    PersonInfo = {"_id":url_info}   #手动分配id字段，id字段值即为该人物词条的链接编号
    for term in Tuple:

        #   删除信息中的空格、换行符、url
        index = term[0]
        index = re.sub(r'&nbsp;', '', index)
        index = re.sub(r'\n', '', index)
        index = re.sub(r'<.*?>', '', index)

        value = term[1]
        value = re.sub(r'&nbsp;', '', value)
        value = re.sub(r'\n', '', value)
        value = re.sub(r'<.*?>', '', value)
        #   ...................................

        PersonInfo.update({index: value})
    print(PersonInfo)

    #   将提取的信息存入数据库
    try:
        my_dict.insert_one(PersonInfo)
    except pymongo.errors.DuplicateKeyError as e:
        print("数据库中已存在此词条信息")
    #   ..........................

    return 0

if __name__=="__main__":
    time1 = time.time()

    #   连接数据库，读取开始页面编号，以从上一次停止处继续爬站
    start_num = 5001   #页面开始编号
    end_num = 1000   #页面结束编号
    #   .....................................................

    #   开启多进程爬取人物词条
    process_num = 4  # 爬站进程数量,至少为2个
    if ((end_num - start_num) % process_num == 0):
        process_num -= 1
    distance = int((end_num - start_num) / process_num)
    L = list(range(start_num, end_num, distance))
    L[-1] = end_num + 1  # 构造各个进程爬站的范围
    process = []
    process_lock = multiprocessing.Lock()

    for i in range(process_num):
        t = Get_PersonHtml(L[i], L[i + 1],process_lock)
        t.daemon = True
        process.append(t)
        t.start()

    for t in process:
        t.join()
    #   ......................

    time2 = time.time()
    T="进程数： "+str(process_num)+"总耗时： "+str((time2-time1)/60)+'分钟'+'\n'
    print(T)

# Q1：同义项时会出现重复的人物，即两个页面url不同，但是提取出得内容相同 eg：柏拉图
# Q2：个别页面不是人物页面，但是错误的将其设定为人物标签（不是算法问题）

