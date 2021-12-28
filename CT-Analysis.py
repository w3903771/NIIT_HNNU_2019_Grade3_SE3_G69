# -*- coding = utf-8 -*-
# @Time : 2021/12/8 1:08
# @Author :　James
# @File : thirdPython.py
# @Software: PyCharm

'''
# @Time : 2021-12-18 12:49
# @Author : cAMP-Cascade-DNN
# @Software : Pycharm
# @Contact: qq:1071747983
#          mail:wuxiaolong8001@163.com
修改合并
'''
import os
import sys

import SimpleITK as sitk
import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import qdarkstyle
from PyQt5 import uic
from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox, QProgressDialog
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

from Visualization import Imshow, Imshow3D

pg.setConfigOptions(imageAxisOrder='row-major')
play_total = 0  # 记录点击播放按钮的次数
open_origin = 0  # 记录是否打开原文件
open_segmentation = 0  # 记录是否打开分割文件
finish_segmentation = 0  # 是否分析过该文件
flag_analysis = 0  # 记录是否点分析完毕
choice_3D = 1  # 记录3D影像显示方式 0为肝脏 1为原图
flag_show_3D = 0  # 记录是否显示3D影像
updown_num = 0  # 记录3D影像上下滑动按钮的位置
leftright_num = 0  # 记录3D影像左右滑动按钮的位置
frontafter_num = 0  # 记录3D影像左右滑动按钮的位置
last_file = ['']  # 记录当前读取文件的路径
last_segmentation = ['']  # 记录当前分割文件的路径
picture_len = 0  # 记录打开文件的长度
window_flag = 1  # 记录点击最大化/正常化窗口的按钮
segmentation = 1  # 记录分割方式 1为边界框 0为覆盖
file_num = 0  # 记录当前打开文件的编号

# 生成代码或可执行文件的目录路径，后续文件引用均基于该路径使用相对路径
if getattr(sys, 'frozen', False):
    code_path = os.path.dirname(sys.executable)
elif __file__:
    code_path = os.path.dirname(os.path.abspath(__file__))

# UI文件夹路径
UI_path = os.path.join(code_path, "UI")
# UI资源路径
UI_resources_path = os.path.join(UI_path, "resources")
# 导入创建的UI文件
ui = uic.loadUiType(os.path.join(UI_path, "windowGui.ui"))[0]

'''
变量定义说明

self.image1 原图数据
self.image1_array sitk库转换来的原始numpy数据 用于后续分析
image1_array_data 经Imageshow 得到的原图2d显示变量 可重复使用 仅用于显示！建议用局部变量

self.image2 分隔图数据
self.image2_array sitk库转换来的原始numpy数据 用于后续分析
image2_array_data 经Imageshow 得到的分隔图2d显示变量 可重复使用 仅用于显示！建议用局部变量

global data3d 3d显示专用全局变量
'''


# 图片同步线程
class MyThread1(QThread):
    def __init__(self, main_UI):
        super(MyThread1, self).__init__()
        self.main_UI = main_UI

    def run(self):
        # mouseEvents.HoverEvent
        global open_segmentation, finish_segmentation
        if open_segmentation or finish_segmentation:
            if self.main_UI.graphicsView_2.currentIndex != self.main_UI.graphicsView.currentIndex:
                self.main_UI.graphicsView_2.setCurrentIndex(
                    self.main_UI.graphicsView.currentIndex)
            QApplication.processEvents()


# 3D显示组件生成线程
class MyThread2(QThread):
    updateSig = pyqtSignal(int)  # 生成完毕信号

    def __init__(self):
        super(MyThread2, self).__init__()

    def run(self):
        global v, data_3d
        v = gl.GLVolumeItem(
            data_3d,
            sliceDensity=1,
            smooth=True,
            glOptions='translucent')
        v.translate(-data_3d.shape[0] / 2, -data_3d.shape[1] / 2, -150)
        self.updateSig.emit(1)


# 分析显示组件生成线程
class MyThread3(QThread):
    updateSig = pyqtSignal(int)  # 生成完毕信号

    def __init__(self, main_UI):
        super(MyThread3, self).__init__()
        self.main_UI = main_UI

    def run(self):
        global pd
        if pd.value() + 1 >= pd.maximum() or pd.wasCanceled():
            self.main_UI.timer2.stop()
        pd.setValue(pd.value() + 1)

        if pd.value() == 99:
            global flag_analysis
            flag_analysis = 1

            pd.setValue(pd.value() + 1)
            QMessageBox.about(self.main_UI, "提示", "分析完成！")
            pd.cancel()

            self.updateSig.emit(1)


# 创建主界面
class mainUI(QMainWindow, ui):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setupUi(self)
        self.move(70, 20)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.menubar.setMouseTracking(True)

        # 设置无边框窗口
        self.setWindowFlag(Qt.FramelessWindowHint)

        # 设置窗体内部件
        # 设置按钮的样式
        self.left_close.setStyleSheet(
            '''QPushButton{border-radius:5px;}QPushButton:hover{background:red;}''')
        self.left_maxi.setStyleSheet(
            '''QPushButton{border-radius:5px;}QPushButton:hover{background:yellow;}''')
        self.left_mini.setStyleSheet(
            '''QPushButton{border-radius:5px;}QPushButton:hover{background:green;}''')
        self.return_button.setStyleSheet(
            '''QPushButton{border-radius:5px;}QPushButton:hover{background:gray;}''')
        self.front_button.setStyleSheet(
            '''QPushButton{border-radius:5px;}QPushButton:hover{background:gray;}''')
        self.play_button.setStyleSheet(
            '''QPushButton{border-radius:5px;}QPushButton:hover{background:gray;}''')
        self.after_button.setStyleSheet(
            '''QPushButton{border-radius:5px;}QPushButton:hover{background:gray;}''')
        self.analysis_button.setStyleSheet(
            '''QPushButton{border-radius:5px;}QPushButton:hover{background:gray;}''')
        self.show_button.setStyleSheet(
            '''QPushButton{border-radius:5px;}QPushButton:hover{background:gray;}''')
        # 设置滑动条初值，最大值和最小值
        self.frontafter_scrollBar.setMaximum(600)
        self.updown_scrollBar.setMaximum(600)
        self.leftright_scrollBar.setMaximum(600)
        self.frontafter_scrollBar.setMinimum(-600)
        self.updown_scrollBar.setMinimum(-600)
        self.leftright_scrollBar.setMinimum(-600)
        self.frontafter_scrollBar.setValue(0)
        self.updown_scrollBar.setValue(0)
        self.leftright_scrollBar.setValue(0)
        # 完成设置窗体内部件

        # 设置窗体内各触发事件
        self.thread1 = MyThread1(self)  # 创建图片同步线程
        self.timer1 = QTimer()  # 图片同步timer
        self.timer1.timeout.connect(self.update1)
        self.timer2 = QTimer()  # 进度条timer
        self.timer2.timeout.connect(self.update2)
        self.select_file_2.triggered.connect(
            self.select_file_clicked)  # 点击菜单中 “打开” 选项触发事件
        self.line_action.triggered.connect(
            self.line_action_clicked)  # 点击菜单中 “线型分割” 选项触发事件
        self.full_action.triggered.connect(
            self.full_action_clicked)  # 点击菜单中 “覆盖型分割” 选项触发事件
        self.origin_action.triggered.connect(
            self.origin_action_click)  # 点击菜单中 “显示原图3D影像” 选项触发事件
        self.change_action.triggered.connect(
            self.change_action_click)  # 点击菜单中 “显示变图3D影像” 选项触发事件
        self.return_button.clicked.connect(
            self.play_return)  # 点击 “回到首帧“ 按钮触发事件
        self.front_button.clicked.connect(self.play_front)  # 点击 “向前一帧“ 按钮触发事件
        self.play_button.clicked.connect(self.play_handle)  # 点击 “播放/暂停“ 按钮触发事件
        self.after_button.clicked.connect(self.play_after)  # 点击 “向后一帧“ 按钮触发事件
        self.analysis_button.clicked.connect(
            self.start_analysis)  # 点击 “分析“ 按钮触发事件
        self.show_button.clicked.connect(self.show_3D)  # 点击 “显示3D影像“ 按钮触发事件
        self.left_close.clicked.connect(self.close)  # 点击 “关闭窗口” 按钮触发事件
        self.left_mini.clicked.connect(self.min_window)  # 点击 “最小化窗口” 按钮触发事件
        self.left_maxi.clicked.connect(
            self.max_window)  # 点击 “最大化/正常化窗口” 按钮触发事件
        self.updown_scrollBar.sliderMoved.connect(
            self.Updown_3D)  # 设置3D影像滑动 “前后“ 划钮后的触发事件
        self.leftright_scrollBar.sliderMoved.connect(
            self.Leftright_3D)  # 设置3D影像滑动 “前后“ 划钮后的触发事件
        self.frontafter_scrollBar.sliderMoved.connect(
            self.Frontafter_3D)  # 设置3D影像滑动 “前后“ 划钮后的触发事件
        # 完成设置窗体内各触发事件

    # 点击 “最小化窗口” 按钮处理事件
    def min_window(self):
        self.showMinimized()

    # 点击 “最大化/正常化窗口” 按钮处理事件
    def max_window(self):
        global window_flag
        if window_flag:
            self.showMaximized()
            window_flag = 0
        else:
            self.showNormal()
            window_flag = 1

    # 设置鼠标双击最小化处理事件
    def window_maximum(self):
        global window_flag
        if self.isMaximized():
            self.showMaximized()
        else:
            self.showMaximized()
        window_flag = 0

    # 鼠标双击最小化
    def mouseDoubleClickEvent(self, event):
        self.window_maximum()
        event.accept()  # 接受事件，禁止传到父控件

    # 鼠标移动
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._mouse_pos:
            self.move(self.mapToGlobal(event.pos() - self._mouse_pos))
        event.accept()  # 接受事件,不传递到父控件

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._mouse_pos = event.pos()
        event.accept()  # 接受事件,不传递到父控件

    def mouseReleaseEvent(self, event):
        self._mouse_pos = None
        event.accept()  # 接受事件,不传递到父控件

    # self.timer1 事件 调用线程1
    def update1(self):
        self.thread1.start()

    # self.timer2 事件 调用线程3进度条
    def update2(self):
        self.thread3.start()

    # 设置 “打开文件” 选项后的事件处理
    def select_file_clicked(self):
        file_name = QFileDialog.getOpenFileName(
            self, "Open File", "../", "nii (*.nii);;nii (*.nii.gz)")  # 获取文件名
        image_path = file_name[0]  # 获取文件路径
        if file_name[0] == "":
            # 如果未选中文件
            QMessageBox.information(self, "提示", "没有选择文件！")
        else:
            global last_file
            if last_file[0] == image_path:
                QMessageBox.information(self, "提示", "已打开该文件！")
            else:
                # 选中文件
                global open_origin, open_segmentation, finish_segmentation, flag_analysis, \
                    picture_len, flag_show_3D, play_total, choice_3D, file_num
                flag_analysis = 0
                flag_show_3D = 0
                play_total = 0
                open_origin = 1
                open_segmentation = 0
                finish_segmentation = 0
                last_segmentation[0] = ''
                choice_3D = 1  # 原图

                self.image1 = sitk.ReadImage(image_path)
                self.image1_arr = sitk.GetArrayFromImage(self.image1)
                image1_arr_data = Imshow(self.image1_arr)
                max = np.max(image1_arr_data)
                min = np.min(image1_arr_data)
                self.graphicsView.setImage(
                    image1_arr_data, levels=(
                        min, max), autoRange=True)
                picture_len = self.image1.GetDepth()

                # 获取编号
                file_num = image_path.split(
                    "/")[-1].split("-")[-1].split(".")[0]

                self.graphicsView_2.setImage(self.image1_arr)
                self.graphicsView_2.clear()
                self.openGLWidget.clear()
                last_file[0] = image_path
                print("(", image_path, ") len: ", picture_len)

    # 设置 “分割” 选项后的事件处理
    def show_segmentaion(self):
        global open_origin, segementation, open_segmentation, play_total
        if open_origin:
            # 已打开分隔文件 重新进行显示
            if open_segmentation:
                play_total = 0
                self.graphicsView.play(0)
                self.graphicsView_2.play(0)
                try:
                    if segmentation == 1:
                        image2_arr_data = Imshow(
                            self.image1_arr, self.image2_arr, mode=True, overlap=False)
                    else:
                        image2_arr_data = Imshow(
                            self.image1_arr, self.image2_arr, mode=True, overlap=True)
                    max = np.max(image2_arr_data)
                    min = np.min(image2_arr_data)
                    self.graphicsView_2.setImage(
                        image2_arr_data, levels=(
                            min, max), autoRange=True)
                    if self.graphicsView_2.currentIndex != self.graphicsView.currentIndex:
                        self.graphicsView_2.setCurrentIndex(
                            self.graphicsView.currentIndex)
                    self.timer1.start(50)  # 打开图片同步timer
                except BaseException:
                    QMessageBox.information(self, "提示", "分割图叠加失败1")
            else:
                file_name = QFileDialog.getOpenFileName(
                    self, "Open File", "../", "nii (*.nii);;nii (*.nii.gz)")  # 获取文件名
                image_path = file_name[0]  # 获取文件路径
                if file_name[0] == "":
                    # 如果未选中文件
                    QMessageBox.information(self, "提示", "没有选择文件！")
                else:
                    self.image2 = sitk.ReadImage(image_path)
                    self.image2_arr = sitk.GetArrayFromImage(self.image2)
                    if self.image2.GetDepth() != self.image1.GetDepth():
                        QMessageBox.about(self, "错误", "分割文件与原文件不匹配！")
                    else:
                        play_total = 0
                        open_segmentation = 1
                        last_segmentation[0] = image_path
                        self.graphicsView.play(0)
                        self.graphicsView_2.play(0)
                        try:
                            if segmentation == 1:
                                image2_arr_data = Imshow(
                                    self.image1_arr, self.image2_arr, mode=True, overlap=False)
                            else:
                                image2_arr_data = Imshow(
                                    self.image1_arr, self.image2_arr, mode=True, overlap=True)
                            max = np.max(image2_arr_data)
                            min = np.min(image2_arr_data)
                            self.graphicsView_2.setImage(
                                image2_arr_data, levels=(
                                    min, max), autoRange=True)
                            if self.graphicsView_2.currentIndex != self.graphicsView.currentIndex:
                                self.graphicsView_2.setCurrentIndex(
                                    self.graphicsView.currentIndex)
                            self.timer1.start(50)  # 打开图片同步timer
                        except BaseException:
                            QMessageBox.information(self, "提示", "分割图叠加失败2")
        else:
            QMessageBox.about(self, "错误", "未读入原文件！")

    def line_action_clicked(self):
        global segmentation
        segmentation = 1
        self.show_segmentaion()

    def full_action_clicked(self):
        global segmentation
        segmentation = 0
        self.show_segmentaion()

    # 点击菜单中 “显示原图3D影像” 选项事件处理
    def origin_action_click(self):
        global choice_3D, flag_show_3D
        choice_3D = 1
        flag_show_3D = 0
        self.openGLWidget.clear()
        QApplication.processEvents()
        self.show_3D()

    # 点击菜单中 “显示变图3D影像” 选项事件处理
    def change_action_click(self):
        global choice_3D, flag_show_3D
        choice_3D = 0
        flag_show_3D = 0
        self.openGLWidget.clear()
        QApplication.processEvents()
        self.show_3D()

    # 设置点击 ”播放/暂停“ 按钮后的事件处理
    def play_handle(self):
        global play_total, open_origin, picture_len, open_segmentation
        if open_origin:
            play_total += 1
            if open_segmentation:
                if picture_len <= 100:
                    if play_total % 2 != 0:
                        self.graphicsView.play(10)
                        self.graphicsView_2.play(10)
                    else:
                        self.graphicsView.play(0)
                        self.graphicsView_2.play(0)
                else:
                    if play_total % 2 != 0:
                        self.graphicsView.play(15)
                        self.graphicsView_2.play(15)
                    else:
                        self.graphicsView.play(0)
                        self.graphicsView_2.play(0)
            else:
                if picture_len <= 100:
                    if play_total % 2 != 0:
                        self.graphicsView.play(10)
                    else:
                        self.graphicsView.play(0)
                elif picture_len >= 500:
                    if play_total % 2 != 0:
                        self.graphicsView.play(17)
                    else:
                        self.graphicsView.play(0)
                else:
                    if play_total % 2 != 0:
                        self.graphicsView.play(15)
                    else:
                        self.graphicsView.play(0)
            self.timer1.start(50)  # 打开图片同步timer
        else:
            QMessageBox.about(self, "错误", "未读入文件！")

    # 设置点击 ”向前一帧“ 按钮后的事件处理
    def play_front(self):
        global open_origin
        if open_origin:
            if self.graphicsView.currentIndex <= 0:
                QMessageBox.about(self, "提示", "已到首帧...")
            else:
                self.front_button.setAutoRepeat(True)
                self.front_button.setAutoRepeatDelay(2000)  # 初始长按时间
                self.front_button.setAutoRepeatInterval(200)  # 长按后重复间隔
                self.graphicsView.setCurrentIndex(
                    self.graphicsView.currentIndex - 1)
        else:
            QMessageBox.about(self, "错误", "未读入文件！")

    # 设置点击 ”向后一帧“ 按钮后的事件处理
    def play_after(self):
        global picture_len, open_origin
        if open_origin:
            if self.graphicsView.currentIndex >= picture_len - 1:
                QMessageBox.about(self, "提示", "已到尾帧...")
            else:
                self.graphicsView.setCurrentIndex(
                    self.graphicsView.currentIndex + 1)
        else:
            QMessageBox.about(self, "错误", "未读入文件！")

    # 设置点击 ”回到首帧“ 按钮后的事件处理
    def play_return(self):
        global open_origin
        if open_origin:
            if self.graphicsView.currentIndex == 0:
                QMessageBox.about(self, "提示", "已到首帧...")
            else:
                self.graphicsView.setCurrentIndex(0)
        else:
            QMessageBox.about(self, "错误", "未读入文件！")

    # 设置点击 ”分析“ 按钮后的事件处理
    def start_analysis(self):
        global open_origin, file_num
        if open_origin:
            global flag_analysis
            find_segmentation_file = ""
            file_name_total = last_file[0].split('/')
            for num in range(len(file_name_total)):
                if num != len(file_name_total) - 1:
                    find_segmentation_file += file_name_total[num]
                    find_segmentation_file += "/"
            find_segmentation_file += "result"
            filenames = os.listdir(find_segmentation_file)
            for name in filenames:
                now_num = name.split('-')[1].split('.')[0]
                if now_num == file_num:
                    QMessageBox.about(self, "提示", "该文件已完成分析！")
                    flag_analysis = 1
            if not flag_analysis:
                global pd
                pd = QProgressDialog(self)
                pd.setWindowTitle("开始分析")
                pd.setLabelText("分析中...")
                pd.setCancelButtonText("取消分析")
                pd.resize(300, 100)
                pd.setRange(0, 100)
                pd.setValue(0)
                pd.show()

                self.thread3 = MyThread3(self)  # 创建分析显示生成线程
                self.thread3.start()
                self.timer2.start(1000)
                os.system("start python %s --test_data_path %s --cpu" % (
                    os.path.join(code_path, 'Unet', 'test.py'), last_file[0]))
        else:
            QMessageBox.about(self, "错误", "未读入文件！")

    # 接受信号更新主界面
    def show_3D_handle(self, flag):
        global v, open_origin
        if open_origin:
            self.openGLWidget.addItem(v)
            QApplication.processEvents()

    # 设置点击 “显示3D影像“ 按钮后的事件处理
    def show_3D(self):
        global open_origin
        if open_origin:
            global flag_show_3D, picture_len, choice_3D, play_total
            global data_3d

            if choice_3D == 1:
                if not flag_show_3D:
                    play_total = 0
                    self.graphicsView.play(0)
                    self.graphicsView_2.play(0)
                    self.timer1.stop()  # 空出资源
                    # get MRI data
                    image1_arr = sitk.GetArrayFromImage(self.image1)
                    data = Imshow3D(image1_arr)

                    # create qtgui
                    self.openGLWidget.orbit(256, 256)
                    if picture_len > 500:
                        self.openGLWidget.opts['distance'] = picture_len * 1.5
                    elif picture_len > 200:
                        self.openGLWidget.opts['distance'] = picture_len * 3.8
                    else:
                        self.openGLWidget.opts['distance'] = picture_len * 4.3
                    self.openGLWidget.setWindowTitle(
                        'pyqtgraph example: GLVolumeItem')
                    # g = gl.GLGridItem()
                    # g.scale(20, 20, -20)
                    # self.openGLWidget.addItem(g)
                    # QApplication.processEvents()

                    data_3d = data

                    self.thread2 = MyThread2()  # 创建3D图像组件生成线程
                    self.thread2.updateSig.connect(
                        self.show_3D_handle)  # 线程结束事件连接
                    self.thread2.start()

                    flag_show_3D = 1

                    self.timer1.start(50)
                else:
                    QMessageBox.about(self, "提示", "已显示3D影像！")
            else:
                global open_segmentation
                if open_segmentation:
                    if not flag_show_3D:
                        play_total = 0
                        self.graphicsView.play(0)
                        self.graphicsView_2.play(0)
                        self.timer1.stop()  # 空出资源
                        # get MRI data
                        image1_arr = sitk.GetArrayFromImage(self.image2)
                        data = Imshow3D(image1_arr)

                        # create qtgui
                        self.openGLWidget.orbit(256, 256)
                        if picture_len > 500:
                            self.openGLWidget.opts['distance'] = picture_len * 1.5
                        elif picture_len > 200:
                            self.openGLWidget.opts['distance'] = picture_len * 3.8
                        else:
                            self.openGLWidget.opts['distance'] = picture_len * 4.3
                        self.openGLWidget.setWindowTitle(
                            'pyqtgraph example: GLVolumeItem')
                        # g = gl.GLGridItem()
                        # g.scale(20, 20, -20)
                        # self.openGLWidget.addItem(g)
                        # QApplication.processEvents()

                        data_3d = data

                        self.thread2 = MyThread2()  # 创建3D图像组件生成线程
                        self.thread2.updateSig.connect(
                            self.show_3D_handle)  # 线程结束事件连接
                        self.thread2.start()

                        flag_show_3D = 1

                        self.timer1.start(50)
                    else:
                        QMessageBox.about(self, "提示", "已显示3D影像！")
                else:
                    QMessageBox.about(self, "错误", "非打开分割文件！")
        else:
            QMessageBox.about(self, "错误", "未读入文件！")

    # 设置3D影像滑动 “上下“ 划钮后的事件处理
    def Updown_3D(self):
        global updown_num
        now = self.updown_scrollBar.value()
        self.openGLWidget.pan(0, 0, updown_num - now, relative='global')
        QApplication.processEvents()
        updown_num = now

    # 设置3D影像滑动 “左右“ 划钮后的事件处理
    def Leftright_3D(self):
        global leftright_num
        now = self.leftright_scrollBar.value()
        self.openGLWidget.pan(leftright_num - now, 0, 0, relative='global')
        QApplication.processEvents()
        leftright_num = now

    # 设置3D影像滑动 “前后“ 划钮后的事件处理
    def Frontafter_3D(self):
        global frontafter_num
        now = self.frontafter_scrollBar.value()
        self.openGLWidget.pan(0, now - frontafter_num, 0, relative='global')
        QApplication.processEvents()
        frontafter_num = now


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 加载 icon 最好放到上面的代码里
    app.setWindowIcon(QIcon('../icon.jpg'))
    main_UI = mainUI()
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt5'))

    main_UI.show()

    sys.exit(app.exec_())
