# !/user/bin/env python
# -*- coding:utf-8 -*-
# code author jiang qiang hua
import time
import random
import os
import json
import re
import subprocess
from PIL import Image


def randRange(start,end):
    return random.randint(start,end)

def isSimilar(target,src,similar):
    if(src - similar)<target<(src + similar):
        return True

def isSimilarColor(piex1, piex2,similar):
    flag = True
    for i in range(0,3):
        if not isSimilar(piex1[i],piex2[i],similar):
            flag = False
            break

    if flag:
        return True
    else:
        return False

#获取分辨率
def get_screen_size():
    #1920*1080
    size_str = os.popen('adb shell wm size').read()
    if not size_str:
        print('请安装adb以及驱动并配置环境变量')
        exit()
    m = re.search(r'(\d+)x(\d+)',size_str)
    if m:
        return "%sx%s" % (m.group(2),m.group(1))
    pass

# 初始化信息，获取配置，检查环境
def init():
    # 获取分辨率
    screen_size = get_screen_size()
    print(screen_size)
    # 配置文件路径
    config_file_path = 'config/%s/config.json' % screen_size
    # 判断路径是否存在
    if os.path.exists(config_file_path):
        with open(config_file_path,'r') as f:
            print('load config file from %s' % config_file_path)
            return json.loads(f.read())
    else:
        with open('config/default.json','r') as f:
            print('load config file from default.json')
            return json.loads(f.read())
    pass

# 获取截图
def get_screenshot():
    # 截图到的图片名称 auto.png
    #adb shell screencap  -p
    process = subprocess.Popen('adb shell screencap  -p',shell=True,stdout=subprocess.PIPE)
    screenshot = process.stdout.read()
    #mac
    screenshot = screenshot.replace(b'\r\n',b'\n')

    #window
    #screenshot = screenshot.replace(b'\r\n', b'\n')
    with open('auto.png','wb') as f:
        f.write(screenshot)
    #print(screenshot)
    pass

# 根据图片和配置文件找到棋盘和棋子坐标
def find_piece_board(img,config):
    #扫描到起始的y坐标
    scan_screen_start_y = 0
    scan_screen_end_y = 0
    board_x = 0
    board_y = 0
    first_piexl = []
    #棋子的最大y坐标
    piece_y_max = 0
    w,h =img.size
    img_pixel = img.load()
    for i in range(h//3,h*2//3,50):
        first_piexl = img_pixel[0,i]
        for j in range(0,w):
            piexl = img_pixel[j,i]
            #判断是否是纯色,如果不是纯色，说明找到拉有棋盘的最高点
            #if first_piexl[:-1] != piexl[:-1]:
            if not isSimilarColor(first_piexl,piexl,20):
                scan_screen_start_y = i - 50
                board_x = j
                break
        if scan_screen_start_y:
            break;
    # 扫描棋子
    left = 0
    right = 0
    for i in range(scan_screen_start_y,h*2//3):
        flag = True
        #  切掉左右八分之一
        for j in range(w//8,w*7//8):
            piexl = img_pixel[j,i]
            # 判断棋子颜色，找到最后一行点的棋子起始末尾
            if(50<piexl[0]<60) and (53<piexl[1]<63) and (95<piexl[2]<110):
                if flag:
                    # 表示第一次碰到棋子颜色
                    left = j
                    flag = False
                right = j
                piece_y_max = max(i,piece_y_max)
    piece_x = (left + right)//2
    piece_y = piece_y_max - config['piece_base_height_1_2']

    # 从棋子的末尾开始往上找，找到与棋盘一开始相同的像素类似的点
    for i in range(piece_y,scan_screen_start_y,-10):
        for j in range(0,w):
            piexl = img_pixel[j, i]
           # print(piexl)
            # if (first_piexl[0]== piexl[0]) and (first_piexl[1] == piexl[1]) and (first_piexl[2] == piexl[2]):
            #     scan_screen_end_y = i
            #     break
            if isSimilarColor(first_piexl,piexl,2):
                scan_screen_end_y = i
                break
        if scan_screen_end_y:
            break
    print('scan_screen_start_y=%s scan_screen_end_y=%s' % (scan_screen_start_y,scan_screen_end_y))
    board_y = (scan_screen_end_y + scan_screen_start_y)//2
    return piece_x,piece_y,board_x,board_y
    pass

# 根据距离和按压系数开始跳
def jump(distance,press_ratio,config):
    #adb shell input tap x y
    time = distance * 1.3 + 20
    clickx = randRange(config['swipe']['x'][0],config['swipe']['x'][1])
    clicky = randRange(config['swipe']['y'][0],config['swipe']['y'][1])
    jumpcmd = 'adb shell input swipe %s %s %s %s %d' % (clickx,clicky,clickx,clicky,time)
    print(jumpcmd)
    os.popen(jumpcmd)
   # return time
    pass

def run():
    # 主函数
    # 1 初始化信息，获取配置，检查环境
    config = init()
    print(config)
    # 2 循环
    while True:
        # 3 获取截图
        get_screenshot();
        img = Image.open('auto.png')
        # 4 获取棋子和棋盘的坐标
        piece_x,piece_y,board_x,board_y = find_piece_board(img,config)
        print('piece_x %s piece_y %s board_x %s board_y %s'% (piece_x,piece_y,board_x,board_y))
        # 5 计算棋子和棋盘的距离
        distance = ((piece_x-board_x)**2 + (piece_y - board_y)**2)**0.5
        print('distance %s' % distance)
        # 6 开始跳跃
        jump(distance,config['press_ratio'],config)
        #  随机休息1到3秒
        time1 = randRange(2,3)
        print('delay -- %s' , time1)
        time.sleep(time1)
    pass

if __name__ == '__main__':
    run()
