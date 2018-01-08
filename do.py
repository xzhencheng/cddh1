# coding: utf-8
# quote from kmaiya/HQAutomator
# 谷歌搜索部分原版搬运，未做修改

import time
import json
import requests
import pytesseract
import os
import sys
import subprocess
import math
from PIL import Image
import random
from six.moves import input
from googleapiclient.discovery import build

try:
    from common import debug, config
except ImportError:
    print('请在项目根目录中运行脚本')
    exit(-1)


g_cse_id = '013420832712086879398:6akj6mfqmia'
g_cse_api_key = 'AIzaSyBHn6bHpkhpb3-M1X0H3T1tTHD8rxjgE9o'

questions = []
screenshot_way = 2

def google_search(query, start):
    service = build("customsearch", "v1", developerKey=g_cse_api_key)
    res = service.cse().list(q=query, cx=g_cse_id, start=start).execute()
    return res

# Google Question and count number of each result
def metric1Func(question, answers):
    met1 = [0, 0, 0]
	#res = google_search(question, None)
    res = google_search("煤气中毒", None)
    print(res)
    items = str(res['items']).lower()
    met1[0] = items.count(answers[0].lower())
    met1[1] = items.count(answers[1].lower())
    met1[2] = items.count(answers[2].lower()) 
    return met1


# Google Question and each specific Answer and count total results
def metric2Func(question, answers):
    met2 = [0, 0, 0]
    res0 = google_search(question + ' "' + answers[0] + '"', None)
    res1 = google_search(question + ' "' + answers[1] + '"', None)
    res2 = google_search(question + ' "' + answers[2] + '"', None)
    return [int(res0['searchInformation']['totalResults']), int(res1['searchInformation']['totalResults']), int(res2['searchInformation']['totalResults'])]


def predict(metric1, metric2, answers):
    max1 = metric1[0]
    max2 = metric2[0]
    for x in range(1, 3):
        if metric1[x] > max1:
            max1 = metric1[x]
        if metric2[x] > max2:
            max2 = metric2[x]
    if metric1.count(0) == 3:
        return answers[metric2.index(max2)]
    elif metric1.count(max1) == 1:
        if metric1.index(max1) == metric2.index(max2):
            return answers[metric1.index(max1)]
        else:
            percent1 = max1 / sum(metric1)
            percent2 = max2 / sum(metric2)
            if percent1 >= percent2:
                return answers[metric1.index(max1)]
            else:
                return answers[metric2.index(max2)]
    elif metric1.count(max1) == 3:
        return answers[metric2.index(max2)]
    else:
        return answers[metric2.index(max2)]

def yes_or_no(prompt, true_value='y', false_value='n', default=True):
    default_value = true_value if default else false_value
    prompt = '%s %s/%s [%s]: ' % (prompt, true_value, false_value, default_value)
    i = input(prompt)
    if not i:
        return default
    while True:
        if i == true_value:
            return True
        elif i == false_value:
            return False
        prompt = 'Please input %s or %s: ' % (true_value, false_value)
        i = input(prompt)


def pull_screenshot():
    '''
    新的方法请根据效率及适用性由高到低排序
    '''
    global screenshot_way
    if screenshot_way == 2 or screenshot_way == 1:
        process = subprocess.Popen('adb shell screencap -p', shell=True, stdout=subprocess.PIPE)
        screenshot = process.stdout.read()
        if screenshot_way == 2:
            binary_screenshot = screenshot.replace(b'\r\n', b'\n')
        else:
            binary_screenshot = screenshot.replace(b'\r\r\n', b'\n')
        f = open('autojump.png', 'wb')
        f.write(binary_screenshot)
        f.close()
    elif screenshot_way == 0:
        os.system('adb shell screencap -p /sdcard/autojump.png')
        os.system('adb pull /sdcard/autojump.png .')

def cut_image(im):
    '''
	对截屏图像进行剪切处理
    '''
    img_size = im.size
    box_q = (50,250,1000,610)
    region = im.crop(box_q)
    region.save("./questionImage.png")
    box_a1 = (50,640,1000,800)
    region = im.crop(box_a1)
    region.save("./answerImage1.png")
    box_a2 = (50,800,1000,960)
    region = im.crop(box_a2)
    region.save("./answerImage2.png")
    box_a3 = (50,960,1000,1120)
    region = im.crop(box_a3)
    region.save("./answerImage3.png")
		
def check_screenshot():
    '''
    检查获取截图的方式
    '''
    global screenshot_way
    if os.path.isfile('autojump.png'):
        os.remove('autojump.png')
    if (screenshot_way < 0):
        print('暂不支持当前设备')
        sys.exit()
    pull_screenshot()
    try:
        Image.open('./autojump.png').load()
        print('采用方式 {} 获取截图'.format(screenshot_way))
    except Exception:
        screenshot_way -= 1
        check_screenshot()

def get_answer():
    #resp = requests.get('http://htpmsg.jiecaojingxuan.com/msg/current',timeout=4).text
    #截屏
    pull_screenshot()
    im = Image.open('./autojump.png')
    cut_image(im)
    #resp = pytesseract.image_to_string(im, lang='chi_sim')
    #print(resp)
    #resp_dict = json.loads(resp)
    answers=[]
    questionImage = Image.open('./questionImage.png')
    question = pytesseract.image_to_string(questionImage, lang='chi_sim')
    print(question)
    answerImage1 = Image.open('./answerImage1.png')
    answerTxt1 = pytesseract.image_to_string(answerImage1, lang='chi_sim')
    answers.append(answerTxt1)
    print(answerTxt1)
    answerImage2= Image.open('./answerImage2.png')
    answerTxt2 = pytesseract.image_to_string(answerImage2, lang='chi_sim')
    answers.append(answerTxt2)
    print(answerTxt2)
    answerImage3 = Image.open('./answerImage3.png')
    answerTxt3 = pytesseract.image_to_string(answerImage3, lang='chi_sim')
    answers.append(answerTxt3)
    print(answerTxt3)

    '''
    if question not in questions:
            questions.append(question)
            met1 = metric1Func(question, answers)
            met2 = metric2Func(question, answers)
            return predict(met1, met2, answers)
        else:
            return 'Waiting for new question...'


    if resp_dict['msg'] == 'no data':
        return 'Waiting for question...'
    else:
        resp_dict = eval(str(resp))
        question = resp_dict['data']['event']['desc']
        question = question[question.find('.') + 1:question.find('?')]
        if question not in questions:
            questions.append(question)
            answers = eval(resp_dict['data']['event']['options'])
            met1 = metric1Func(question, answers)
            met2 = metric2Func(question, answers)
            return predict(met1, met2, answers)
        else:
            return 'Waiting for new question...'
    '''

def main():
    '''
    主函数
    '''
    op = yes_or_no('请确保手机打开了 ADB 并连接了电脑，然后打开跳一跳并【开始游戏】后再用本程序，确定开始？')
    if not op:
        print('bye')
        return
    #print('程序版本号：{}'.format(VERSION))
    debug.dump_device_info()
    check_screenshot()

    i, next_rest, next_rest_time = 0, random.randrange(3, 10), random.randrange(5, 10)
    while True:
        print(time.strftime('%H:%M:%S',time.localtime(time.time())))
        print(get_answer())
        time.sleep(1)


if __name__ == '__main__':
    main()
