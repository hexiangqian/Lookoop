# coding:UTF-8
# 2018-10-16
# region growing
# 区域生长法

import numpy as np
import os
import cv2
import datetime
from threshed import getThreshValue, loadData
from regression import *


__suffix = ["png", "jpg"]


def file(dirpath):
    file = []
    for root, dirs, files in os.walk(dirpath, topdown=False):
        for name in files:
            path = os.path.join(root, name)
            if name.split(".")[-1] in __suffix:
                file.append(path)
    return file


def handle(dirs, out_dir, clip, w0):
    start_time = datetime.datetime.now()
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    files = file(dirs)

    total = len(files)
    fail, success, skip, count = 0, 0, 0, 0

    for f in files:
        count += 1
        print(count, '/', total)
        img_dirs = os.path.join(out_dir, f.split("\\")[-1])
        if os.path.isfile(img_dirs):
            skip += 1
            continue
        try:
            
            # 1. 读取图片, 切边处理
            img = cv2.imread(f, 0)
            x,w,y,h = clip
            img = img[x:w , y:h]

            # 2. 轮廓提取
            img, w, h = crop(img, img_dirs, w0)
            
            # 3. 将图片扩充为正方形
            if w > h:
                gap = w - h
                fill = np.zeros([1, w], np.uint8)
                for i in range(gap//2):
                    img = np.concatenate((img,fill), axis = 0)
                for i in range(gap//2):
                    img = np.concatenate((fill, img), axis = 0)
            elif w < h:
                gap = h - w
                fill = np.zeros([h, 1], np.uint8)
                for i in range(gap//2):
                    img = np.concatenate((img,fill), axis = 1)
                for i in range(gap//2):
                    img = np.concatenate((fill, img), axis = 1)
            else:
                pass

            # 4. 归一化为256x256
            img_new = cv2.resize(img, (256, 256), interpolation=cv2.INTER_LINEAR)
            # 4.. 保存自适应阈值图像
            adaptive = cv2.adaptiveThreshold(img_new, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)
            saveImage(img_dirs, adaptive, "_adaptive")
            # 5. 转换为三通道
            img_new = cv2.cvtColor(img_new, cv2.COLOR_GRAY2BGR)

            # 6. 保存图片
            cv2.imwrite(img_dirs, img_new)

            # 控制台输出
            print("handled: ", f.split("\\")[-1])
            if count % 5 == 0 and count != total:
                end_time = datetime.datetime.now()
                expend = end_time - start_time
                print("\nexpend time:", expend, "\nexpected time: ", expend / count * total, '\n')
            success += 1

        except Exception as e:
            # 图片处理失败, 跳过图片保存目录: ./failed
            print("Error: " + str(e))
            
            failed_dir = os.path.join("\\".join(out_dir.split("\\")[:-1]), out_dir.split("\\")[-1] + "_failed")
            print("failed to handle %s, skiped.\nsaved in %s" % (f,failed_dir))
            if not os.path.isdir(failed_dir):
                os.mkdir(failed_dir)
            print(os.path.join(failed_dir, f.split("\\")[-1]))
            os.system("copy %s %s" % (f, os.path.join(failed_dir, f.split("\\")[-1])))
            fail += 1
            print()

    end_time = datetime.datetime.now()
    expend = end_time - start_time
    print("\n\ntotal: %d\nsuccessful: %d\nskip: %d\nfailed: %d\nExpend time: %s" %(total, success, skip, fail, expend))
    os.startfile(out_dir)


def crop(img, img_dirs, weight):
    img_w, img_h = img.shape
    # 获得处理后的二值图像
    thresh = getThresh(img, weight)
    # 使用区域生长获得轮廓
    res, growing = regionGrowing(img, thresh)

    # 扩充边缘
    x, y, w, h = cv2.boundingRect(growing)
    if x >= 10 and y >= 10 and x+w <= img_w and y+h <= img_h:
        x -= 10
        y -= 10
        w += 20
        h += 20

    # 切片
    img_new = res[y:y+h, x:x+w]
    
    # 保存二值图像, 生长区域
    saveImage(img_dirs, growing, "_growing_region")
    saveImage(img_dirs, thresh, "_thresh")
    # 转换为数组
    img_new = np.array(img_new)

    return img_new, img_new.shape[1], img_new.shape[0]


def saveImage(img_dirs, image, mid_name):
    """
    保存图像
    """
    basename = os.path.basename(img_dirs)
    file = os.path.splitext(basename)
    file_prefix = file[0]
    suffix = file[-1]
    image_file = os.path.join("\\".join(img_dirs.split("\\")[:-1]), file_prefix + mid_name + suffix)
    cv2.imwrite(image_file, image)


def getThresh(img, weight):
    """
    获得二值图形
    """
    mask = np.zeros((img.shape[0], img.shape[1]), np.uint8)

    thresh_value, _, _, thresh = getThreshValue(img, weight)

    # 二值,闭运算
    ret, thresh = cv2.threshold(thresh , thresh_value, 255, cv2.THRESH_BINARY)
    kernel = np.zeros((7,7), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel) # 闭运算，封闭小黑洞
    thresh = cv2.medianBlur(thresh, 5)

    return thresh


def regionGrowing(img, thresh):
    """
    区域生长
    """
    m, n = thresh.shape
    r, c = m // 2, n // 2 # 种子起始点
    visited = [[False for _ in range(n)] for _ in range(m)]
    queue = []
    queue.append([r, c])
    visited[r][c] = True
    while len(queue) != 0:
        row, col = queue.pop()
        if row > 1 and not visited[row - 1][col] and thresh[row - 1][col] != 0:
            queue.append([row - 1, col])
            visited[row - 1][col] = True

        # 往右搜索
        if row + 1 < m and not visited[row + 1][col] and thresh[row + 1][col] != 0:
            queue.append([row + 1, col])
            visited[row + 1][col] = True

        # 往上搜索
        if col - 1 >= 0 and not visited[row][col - 1] and thresh[row][col - 1] != 0:
            queue.append([row, col -1])
            visited[row][col - 1] = True

        # 往下搜搜
        if col + 1 < n and not visited[row][col + 1] and thresh[row][col + 1] != 0:
            queue.append([row, col + 1])
            visited[row][col + 1] = True  

    for i in range(m):
        for j in range(n):
            if not visited[i][j]:
                thresh[i][j] = 0


    # 为避免黑洞, 得到轮廓二值图像后还需要翻转
    r, c = m-1, (n-1)//2 # 获得轮廓外区域
    visited = [[False for _ in range(n)] for _ in range(m)]
    queue = []
    queue.append([r, c])
    visited[r][c] = True
    while len(queue) != 0:
        row, col = queue.pop()
        if row > 1 and not visited[row - 1][col] and thresh[row - 1][col] == 0:
            queue.append([row - 1, col])
            visited[row - 1][col] = True

        # 往右搜索
        if row + 1 < m and not visited[row + 1][col] and thresh[row + 1][col] == 0:
            queue.append([row + 1, col])
            visited[row + 1][col] = True

        # 往上搜索
        if col - 1 >= 0 and not visited[row][col - 1] and thresh[row][col - 1] == 0:
            queue.append([row, col -1])
            visited[row][col - 1] = True

        # 往下搜搜
        if col + 1 < n and not visited[row][col + 1] and thresh[row][col + 1] == 0:
            queue.append([row, col + 1])
            visited[row][col + 1] = True  

    for i in range(m):
        for j in range(n):
            if visited[i][j]:
                img[i][j] = 0


    return img, thresh


if __name__ == '__main__':
    dirs = "C:\\Study\\test\\image\\regression" # 原图片存储路径
    out_dir = "C:\\Study\\test\\regression_out" # 存储路径
    # 获得权值
    label = "label.txt" # 标签文件
    data = "data.txt" # 数据文件
    print("loading data ...")
    feature, label = loadData(label, data) # 融合标签文件和数据文件
    # 训练
    print ("traing...")
    method = ""
    if method == "bfgs":  # 选择BFGS训练模型
        print("using BFGS...")
        w0 = bfgs(feature, label, 0.5, 50, 0.4, 0.55)
    elif method == "lbfgs":  # 选择L-BFGS训练模型
        print("using L-BFGS...")
        w0 = lbfgs(feature, label, 0.5, 50, m=20)
    else:  # 使用最小二乘的方法
        print("using LMS...")
        w0 = ridgeRegression(feature, label, 0.5)

    print("handling...")
    handle(dirs, out_dir, (45,-45,45,-45), w0)