#!/usr/bin/env python
# -*-coding:utf-8-*-
import codecs
import datetime,time
import re,json
import requests
from bs4 import BeautifulSoup
import logging
import logging.handlers 

#日志
LOG_FILE = 'tst.log'  
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount = 5)
fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter) 
logger = logging.getLogger('tst')
logger.addHandler(handler)   
logger.setLevel(logging.DEBUG)
#亿万转换

def transform(datas_res):
    if datas_res[-1] == '亿':
        datas_res = datas_res.replace('亿', '')
        datas_res = float(datas_res) * 100000000
    else:
        datas_res = datas_res.replace('万', '')
        datas_res = float(datas_res) * 10000
    return datas_res
# 数组排序
def sort_array(data):
    fina_array = []
    for key in range(len(data)):
        fin_array_box = [] 
        if key%2==0:
            fin_array_box.append(data[key])
            fin_array_box.append(data[key+1])
            fina_array.append(fin_array_box)
    fina_array = sorted(fina_array, key=lambda x: x[1])
    return fina_array
#列表解析
def list_analysis(topic_list):
    logger.info('逐页列表解析开始')  
    list_array = []
    #topic_list_array = []
    for list_key in topic_list:
        #logger.info('本条需要解析的链接'+str(list_key))
        read_num = list_key["desc2"]
        topic_title = list_key["title_sub"]  
        #判断是否有阅读数目
        if "超级话题" in read_num:
            logger.info(str(topic_title)+'超级话题拼链接，进行请求') 
            #拼链接
            link_title = re.split('#',read_num)[1]
            oid = list_key["actionlog"]["oid"]
            fid = list_key["actionlog"]["fid"]
            topic_link="http://api.weibo.cn/2/guest/page?networktype=wifi&extparam="+link_title+"&c=android&s=29d67dbb&wm=14010_0013&v_f=2&lang=zh_CN&containerid="+str(oid)
            print(topic_link)
            topic_page = requests.get(topic_link) 
            tpage_json = topic_page.json() 
            try :
                read_num = tpage_json["pageInfo"]["desc_more"]
            except KeyError:
                continue
            read_num = re.split('　', read_num[0])
            if len(read_num) == 1:
                read_num = re.split(' ', read_num[0])
                logger.info('超级话题阅读数'+str(read_num))
            read_num_res = str(read_num[0])
            
        else:
            read_num_res = re.split('　', read_num)[-1]
        
        if "阅读" in read_num_res:        
            read_num_res = read_num_res.replace('阅读', '')
            read_num_res = transform(read_num_res)     
        list_array.append(topic_title)
        list_array.append(read_num_res)  
        logger.info('\n循环'+str(list_array)+'\n')
    logger.info('本页数据'+str(list_array))
    return list_array
#获取列表+解析函数运行
def get_topic_list(page_url):
    topic_list_array = []
    for page_url_key in range(1,4): #（x,y）调整页码个数
        url=page_url+"&page="+str(page_url_key)
        print('页码 '+str(url))
        web_page = requests.get(url) 
        topic_json = web_page.json()
        print(topic_json)
        #页码链接不存在
        try:
            message = topic_json["msg"]
        except KeyError:
            message=""
            pass
        if message == "无数据内容":
            logger.info(str(page_url_key)+'页码无数据内容')  
            continue
        #电影应第一页结构不同进行区别分析
        if not  topic_json["cards"] or ("card_group" not in topic_json["cards"][0]):
             
            topic_list = topic_json["cards"][1]["card_group"]
            print("电影"+str(topic_list))
        else:
            topic_list = topic_json["cards"][0]["card_group"]
         
        topic_list_array = topic_list_array + list_analysis(topic_list)
    logger.info('本页数据'+str(len(topic_list_array))+str(topic_list_array))
    return topic_list_array
#写数据
def fill_topic(array):
    #final_array_title = array[::2]
    #final_array_num = array[1::2]    
    today = str(datetime.datetime.now())[:13].replace(' ', '_')
    #num = int(len(array)/2)
   
    with codecs.open(today + '.csv', "a", "utf-8") as f:
        for key in range(len(array)):
            f.write(array[key][0] +'\t'+str(array[key][1])+'\n')    
def main():
    """
    抓取微博热点 
    """
    #时间
    today = str(datetime.datetime.now())[:13].replace(' ', '_')
    # 解析文章
   
    # 地址及类目数组
    url_array = ['http://api.weibo.cn/2/guest/cardlist?networktype=wifi&uicode=10000011&moduleID=708&checktoken=d322414e8a72505476416f1273160de2&lcardid=100803_-_card_home_menu&c=android&i=b7e6b69&s=29d67dbb&ua=smartisan-YQ601__weibo__6.10.0__android__android5.1.1&wm=14010_0013&aid=01AmwG_4WQHwOm5HgWJx5nMWVe3PHyOg1488thrtAHvYbQmF4.&did=dbae7fea9baa59e0e30eeedff9399fbbcc9a0baf&fid=100803_-_page_hot_list&uid=1005058098897&v_f=2&v_p=36&from=106A095010&gsid=_2AkMgsBC7f8NhqwJRmP0VyWPiZYV_ww_EieLBAH7sJRM3HRl-3T9kqm8ktRVT5nG9XvLsfkXo6TbkJ2TT-zwmjw..&imsi=460022010250369&lang=zh_CN&lfid=100803&page=1&skin=default&count=20&oldwm=14010_0013&sflag=1&containerid=100803_-_page_hot_list&luicode=10000011&need_head_cards=1', 
                 'http://m.weibo.cn/container/getIndex?openApp=0&from=1067295010&luicode=10000010&lfid=&containerid=100803_ctg1_1_-_page_topics_ctg1__1',
                 'http://m.weibo.cn/container/getIndex?openApp=0&from=1067295010&luicode=10000010&lfid=&containerid=100803_ctg1_138_-_page_topics_ctg1__138', 
                 'http://m.weibo.cn/container/getIndex?openApp=0&from=1067295010&luicode=10000010&lfid=&containerid=100803_ctg1_3_-_page_topics_ctg1__3',
                 'http://m.weibo.cn/container/getIndex?openApp=0&from=1067295010&luicode=10000010&lfid=&containerid=100803_ctg1_100_-_page_topics_ctg1__100']

    num_array=[0,1,2,3,4]##出错后是url_array[data_arry[num_array]]
    topic_text_array = ['话题', '社会', '科技', '科普', '电影']
    list_array = []
    # 主体
    for topic_key in range(0,5):
        with codecs.open(today + '.csv', "a", "utf-8") as f:
            f.write('\n\n' + topic_text_array[topic_key] + '\n\n')      
        logger.info(str(topic_text_array[topic_key])+'获取列表开始')
        get_topic = get_topic_list(url_array[topic_key])
        print('结果'+str(get_topic))
        get_topic = sort_array(get_topic)
        print('结果2'+str(get_topic))
        fill_topic(get_topic)
        print(get_topic)  
    #日志

    
        
if __name__ == '__main__':
    main()
