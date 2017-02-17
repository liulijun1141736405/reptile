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
LOG_FILE = 'wb_topic.log'  
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
    logger.info('逐页列表解析开始\n')  
    list_array = []
    for list_key in topic_list:
        read_num = list_key["desc2"]
        topic_title = list_key["title_sub"]  
        #判断是否有阅读数目
        if "超级话题" in read_num:
            logger.info(str(topic_title)+'超级话题拼链接，进行请求\n') 
            #拼链接
            link_title = re.split('#',read_num)[1]
            oid = list_key["actionlog"]["oid"]
            fid = list_key["actionlog"]["fid"]
            topic_link="http://api.weibo.cn/2/guest/page?networktype=wifi&extparam="+link_title+"&c=android&s=29d67dbb&wm=14010_0013&v_f=2&lang=zh_CN&containerid="+str(oid)
            logger.info('超级话题的链接：'+str(topic_link))
            try:
                topic_page = requests.get(topic_link,timeout=5)
                logger.info('超级话题请求码'+str(topic_page.status_code))
            except Exception  as e :
                logger.info('异常',e)
                #topic_page = requests.get(topic_link,timeout=5) 
                statuscode = topic_page.status_code
                logger.info('链接请求'+str(statuscode))
                while statuscode!=200:
                    topic_page = requests.get(topic_link,timeout=5)
                logger.info('错误处理后的json'+str(topic_page.json()))
            tpage_json = topic_page.json() 
            try :
                read_num = tpage_json["pageInfo"]["desc_more"]
            except KeyError:
                continue
            read_num = re.split('　', read_num[0])
            if len(read_num) == 1:
                read_num = re.split(' ', read_num[0])
                logger.info('超级话题阅读数'+str(read_num)+'\n')
            read_num_res = str(read_num[0])
            
        else:
            read_num_res = re.split('　', read_num)[-1]
        
        if "阅读" in read_num_res:        
            read_num_res = read_num_res.replace('阅读', '')
            read_num_res = transform(read_num_res)     
        list_array.append(topic_title)
        list_array.append(read_num_res)  
    logger.info('本页数据'+str(list_array)+'\n')
    return list_array
#获取列表+解析函数运行
def get_topic_list(page_url):
    topic_list_array = []
    for page_url_key in range(1,2): #（x,y）调整页码个数
        url=page_url+"&page="+str(page_url_key)
        logger.info('页码 '+str(url))
        try:
            web_page = requests.get(url,timeout=5) 
        except Exception  as e :
            logger.info('异常',e)            
            page_status = web_page.status_code
            while page_status!=200:
                web_page = requests.get(url,timeout=5)       
        topic_json = web_page.json()
        logger.info('topic_json+成功')
        
        #页码链接不存在
        try:
            message = topic_json["errmsg"]
            errno = topic_json["errno"]
        except KeyError:
            message="no"
            errno=''
        logger.info('errno'+str(errno))
        #请求错误循环开始
        while errno == -200:
            logger.debug('请求频繁出错——重新请求\n')
            logger.info('请求频繁出错——重新请求')
            url=page_url+"&page="+str(page_url_key)
            web_page = requests.get(url) 
            topic_json = web_page.json()
            try:
                errno = topic_json["errno"]
            except KeyError:
                errno='' 
            if errno=='' :
                break
        #请求错误循环结束
        if message == "无数据内容":
            logger.info(str(page_url_key)+'页码无数据内容\n')  
            continue
        #电影应第一页结构不同进行区别分析
        if not  topic_json["cards"] or ("card_group" not in topic_json["cards"][0]):
            try:
                topic_list = topic_json["cards"][1]["card_group"]
            except IndexError:
                logger.info('科普数目有限')
            logger.info("电影"+str(topic_list))
        else:
            topic_list = topic_json["cards"][0]["card_group"]
         
        logger.info('数组相加topic_list_array'+str(topic_list_array)+'\n')
        ex_list = list_analysis(topic_list)
        topic_list_array.extend(ex_list)
    logger.info('本页数据'+str(len(topic_list_array))+str(topic_list_array)+'\n')
    return topic_list_array
#写数据
def fill_topic(array):
    #final_array_title = array[::2]
    #final_array_num = array[1::2]    
    today = str(datetime.datetime.now())[:13].replace(' ', '_')
    #num = int(len(array)/2)
    logger.info('要写的数据'+str(array)+'\n')
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
    url_array = [
        'http://api.weibo.cn/2/guest/cardlist?&lang=zh_CN&containerid=100803_-_page_hot_list',
        'http://api.weibo.cn/2/guest/cardlist?&lang=zh_CN&containerid= 100803_ctg1_1_-_page_topics_ctg1__1',
        'http://api.weibo.cn/2/guest/cardlist?&lang=zh_CN&containerid=100803_ctg1_138_-_page_topics_ctg1__138',
        'http://api.weibo.cn/2/guest/cardlist?&lang=zh_CN&containerid=100803_ctg1_3_-_page_topics_ctg1__3',
        'http://api.weibo.cn/2/guest/cardlist?&lang=zh_CN&containerid=100803_ctg1_100_-_page_ctg_hot_list__100',
        
    ]

    num_array=[0,1,2,3,4]##出错后是url_array[data_arry[num_array]]
    topic_text_array = ['话题', '社会', '科技', '科普', '电影']
    list_array = []
    # 主体
    for topic_key in range(0,5):
        with codecs.open(today + '.csv', "a", "utf-8") as f:
            f.write('\n\n' + topic_text_array[topic_key] + '\n\n')      
        logger.info(str(topic_text_array[topic_key])+'获取列表开始')
        get_topic = get_topic_list(url_array[topic_key])
        logger.info('结果'+str(get_topic)+'\n')
        get_topic = sort_array(get_topic)
        logger.info('排序后的结果'+str(get_topic)+'\n')
        fill_topic(get_topic)
    #日志

    
        
if __name__ == '__main__':
    main()
