"""
Author: Chen Xianwei & WnagYufeng
Zhejiang University, Hangzhou, China
Date: 2018/11/21
Version: V 1.0

"""
from __future__ import with_statement
import numpy as np
import sys
import oscillator
from PyQt5 import QtCore, QtGui
from libs.oscilloscope.wave import Wave
from PyQt5 import QtWidgets
from Ui_qtdesigner import Ui_MainWindow
import os
import matplotlib.pyplot as plt
from pylab import *
import peakutils
from PyQt5.QtWidgets import QMessageBox
import time
import asyncio

class DesignerMainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self, parent=None):

        # 主窗口继承 
        super(DesignerMainWindow, self).__init__(parent)
        self.setupUi(self)

        # 主界面上的按钮触发执行与停止采集函数的进程
        self.selectButton.clicked.connect(self.Start_to_do_something)
        self.stopButton.clicked.connect(self.Start_to_do_nothing)

        # 主界面菜单栏上的帮助与更多选项跳转到信息介绍窗口
        self.tableWidget.cellClicked.connect(self.update_graph)
        self.actionexit_it.triggered.connect(app.quit)
        self.actionAbout_QT.triggered.connect(self.aboutQT)
        self.actionAbout_PYQT.triggered.connect(self.aboutPYQT)
        self.actionAbout_ZJU.triggered.connect(self.aboutZJU)

        # 选择文件夹按钮打开一个文件夹
        self.tableWidget.setHorizontalHeaderLabels(['filename'])
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.line_Directory.setReadOnly(True)
        self.textEdit.setReadOnly(True)

        # 点击按钮触发打开文件
        self.button_Browse.clicked.connect(self.browse)

        self.getthread = Getthread() # 多线程
        self.analysis = Analysis() # 数据分析
        self.getthread.saving_signal.connect(self.Oscillator_save) # 储存信号为文本文件
        self.analysis.saving_signal.connect(self.AnalysisInfo)

        # 触发执行将文本数据存储为图片的函数
        self.analysis.save_img.connect(self.save_img)
        self.analysis.save_ans.connect(self.save_ans)
        self.analysis.save_pow.connect(self.save_pow)
        self.analysis.save_qow.connect(self.save_qow)
        self.analysis.save_multi_pow.connect(self.save_multi_pow)
        self.analysis.save_multi_qow.connect(self.save_multi_qow)
        self.analysis.save_unimodal_pow.connect(self.save_unimodal_pow)
        self.analysis.save_multi_unimodal_pow.connect(self.save_multi_unimodal_pow)

        self.currentwave = [] # 当前采集的信号数据
        self.count = 0 # 当前采集的信号数
        
    def browse(self): 

        # 选择文件夹后将文件夹中所有的" .txt" 文件列出来
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Find Folder", QtCore.QDir.currentPath())
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        self.line_Directory.setText(directory)
        dirIterator = QtCore.QDirIterator(directory,  ['*.txt'])

        while(dirIterator.hasNext()):
            dirIterator.next()
            dataname = dirIterator.filePath()
            name = QtWidgets.QTableWidgetItem(dataname)
            analysis = QtWidgets.QTableWidgetItem('Not Yet')
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row, 0, name)

    def get_the_wave(self, filename):

        col1 = np.loadtxt(filename,  delimiter='\t',  usecols = (0,),  dtype = float) # 文本文件中的x轴(即时间轴)
        col2 = np.loadtxt(filename,  delimiter='\t',  usecols = (1,),  dtype = float) # 文本文件中的y轴(即电压轴)
        return col1,  col2
        
    def get_the_result(self,  t):

        # 当前波形数据
        self.currentwave = t

    def Oscillator_save(self, x, y, n):

        # 采集数据的方法
        if (Ui_MainWindow.stdo == 1):

            n = len(os.listdir(self.line_Directory.text()))

            # 文本框的消息提示
            self.textEdit.append('...We have already gotten ' + str(n) + ' signals')
            self.textEdit.append('...preparing for the next signal')
            self.textEdit.append('...connection rebuild')
            self.textEdit.append('...waiting for the next signal')
            self.textEdit.append('...')
            outfile = open(self.line_Directory.text() + '/' + str(n) + '.txt', 'w+')
            for _x, _y in zip(x,y):
                outfile.write(str(_x) + '\t' + str(_y) + '\n')
            outfile.close()
            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            name = QtWidgets.QTableWidgetItem(self.line_Directory.text() + '/' + str(n) + '.txt')
            analysis = QtWidgets.QTableWidgetItem('Not Yet')
            self.tableWidget.setItem(row, 0, name)
            self.tableWidget.setItem(row, 1, analysis)
            time,  voltage = self.get_the_wave(self.tableWidget.item(row,  0).text())
            self.mpl.canvas.ax.clear()
            self.mpl.canvas.ax.get_xaxis().grid(True)  
            self.mpl.canvas.ax.get_yaxis().grid(True)
            self.mpl.canvas.ax.plot(voltage,  'k')
            self.mpl.canvas.ax.set_title('Original Wave')
            self.mpl.canvas.ax.set_ylabel(r'$Amplitude(V)$')
            self.mpl.canvas.ax.set_xticklabels(('0', '2.0', '4.0', '6.0', '8.0',  '10.0'))
            updated_voltage = np.fft.rfft(voltage)
            for i in range(len(updated_voltage)):
                updated_voltage[i] = 0
            updated_voltage = np.fft.irfft(updated_voltage)  
            self.mpl.canvas.draw()

    def Start_to_do_something(self):

        Ui_MainWindow.stdo = 1

        if self.folderbutton.isChecked():
            if len(self.line_Directory.text()) == 0:
                self.textEdit.append('Sorry! You must choose a directory!')
                return
            self.selectButton.setEnabled(False)
            self.folderbutton.setEnabled(False)
            self.directlybutton.setEnabled(False)
            self.stopButton.setEnabled(False)
            self.peakthresholdbox.setEnabled(False)
            self.peakthresholdbox_2.setEnabled(False)
            self.triggerbox.setEnabled(False)
            #self.triggerbox_2.setEnabled(False)
            self.button_Browse.setEnabled(False)
            self.textEdit.append('<p><br /></p><p><strong>Analyzing...... '
                + '</strong></p><p><strong>It will take a long time. '
                + ' </strong></p><p><strong>Please wait patiently!</strong></p>')
            self.analysis.begin(self.line_Directory.text())

        else:
            if len(self.line_Directory.text()) == 0:
                self.textEdit.append('Sorry! You must choose a directory!')
                return
            self.selectButton.setEnabled(False)
            self.folderbutton.setEnabled(False)
            self.directlybutton.setEnabled(False)
            self.peakthresholdbox.setEnabled(False)
            self.peakthresholdbox_2.setEnabled(False)
            self.triggerbox.setEnabled(False)
            self.button_Browse.setEnabled(False)

            isgood = self.getthread.Begin(self.line_Directory.text() + '/')
            if isgood == -1:
                self.textEdit.append('Sorry! The device dose not work! Please check it out!')

    def Start_to_do_nothing(self):

        # 禁用所有按钮
        Ui_MainWindow.stdo = 0
        self.selectButton.setEnabled(True)
        self.folderbutton.setEnabled(True)
        self.directlybutton.setEnabled(True)
        self.peakthresholdbox.setEnabled(True)
        self.peakthresholdbox_2.setEnabled(True)
        self.triggerbox.setEnabled(True)
        self.button_Browse.setEnabled(True)

    def update_graph(self, row, col):

        # 画图
        time,  voltage = self.get_the_wave(self.tableWidget.item(row,  0).text())
        self.mpl.canvas.ax.clear()
        self.mpl.canvas.ax.get_xaxis().grid(True)  
        self.mpl.canvas.ax.get_yaxis().grid(True)
        self.mpl.canvas.ax.plot(voltage,  'k')
        self.mpl.canvas.ax.set_title('Original Wave')
        self.mpl.canvas.ax.set_ylabel(r'$Amplitude(V)$')
        self.mpl.canvas.ax.set_xticklabels(('0', '2.0', '4.0', '6.0', '8.0',  '10.0'))
        updated_voltage = np.fft.rfft(voltage)
        for i in range(len(updated_voltage)):
            if True:
                updated_voltage[i] = 0
        self.mpl.canvas.draw()

    def AnalysisInfo(self, _str):

        # 分析结束的标志
        self.textEdit.append(_str)
        if _str == 'Done!!':
            self.selectButton.setEnabled(True)
            self.folderbutton.setEnabled(True)
            self.directlybutton.setEnabled(True)
            self.stopButton.setEnabled(True)
            self.peakthresholdbox.setEnabled(True)
            self.peakthresholdbox_2.setEnabled(True)
            self.triggerbox.setEnabled(True)
            self.button_Browse.setEnabled(True)

    def aboutQT(self):

        # 设置帮助菜单中的关于QT的信息介绍
        QMessageBox.aboutQt(self, 'About QT')

    def aboutPYQT(self):

        # 设置帮助菜单中的关于PYQT的信息介绍
        QMessageBox.about(self, 'About PYQT5', '<p><p style="text-align:justify; ' 
            + ' font-family:&quot;font-size:16px;background-color:#FFFFFF; '
            + ' ">PyQt5 is dual licensed on all platforms under the Riverbank Commercial License and the GPL v3. '
            + ' Your PyQt5 license must be compatible with your Qt license. '
            + ' If you use the GPL version then your own code must also use a compatible license.'
            + ' </p><p style="text-align:justify;font-family:&quot;font-size:16px;background-color:#FFFFFF;">PyQt5, '
            + ' unlike Qt, is not available under the LGPL.</p><p style="text-align:justify;font-family:&quot;font-size:16px; '
            + ' background-color:#FFFFFF;">You can purchase a commercial PyQt5 license&nbsp; '
            + ' <a class="reference external" href="https://www.riverbankcomputing.com/commercial/buy">here</a>.</p></p>')

    def aboutZJU(self):

        # 设置帮助菜单中的关于浙江大学的信息介绍
        QMessageBox.about(self, 'About ZJU', '<p>866 Yuhangtang Rd, Hangzhou 310058, P.R. China&nbsp;</p><p>Copyright &copy; '
            + ' 2018 <a href="http://www.zju.edu.cn/" target="_blank">Zhejiang University</a>&nbsp;</p><p>Seeking Truth, Pursuing Innovation.</p>')

    def save_img(self, x, y, i, indexes):

        # 绘制并保存保存双峰μ子信号的波形图
            plt.plot(x, y)
            plt.plot(x[indexes], y[indexes], 'o-r')
            plt.savefig(self.line_Directory.text() + '\\' + str(i) + '.png')
            plt.close()

    def save_ans(self, title, distribute):

        # 绘制并保存双峰μ子信号两个峰时间差的寿命统计直方图
            plt.bar(range(len(distribute)), distribute)
            plt.title(title)
            plt.xlabel('The life time of moun(us)')
            plt.ylabel('The number of the moun')
            plt.savefig(self.line_Directory.text() + '\\' + '4.1lifetimeofMoun.png')
            plt.close()

    def save_pow(self, title, distribute):

        # 绘制并保存双峰μ子信号第一个峰幅值的能量统计直方图
            plt.bar(range(len(distribute)), distribute)

        # 对直方图进行多项式函数曲线的拟合
            a = np.arange(0, len(distribute), 1)
            b = distribute
            c = np.polyfit(a, b, 20)
            d = np.poly1d(c)
            print(d)
            bvals = d(a)
            plot1 = plt.plot(a, bvals, 'r', label = 'polyfit values')
            plt.title(title)
            plt.xlabel('The power level of moun(V)')
            plt.ylabel('The number of moun')
            plt.savefig(self.line_Directory.text() + '\\' + '1.1powerofMoun.png')
            plt.close()

    def save_qow(self, title, distribute):

        # 绘制并保存双峰μ子信号第二个峰幅值的能量统计直方图
            plt.bar(range(len(distribute)), distribute)

        # 对直方图进行多项式函数曲线的拟合
            a = np.arange(0, len(distribute), 1)
            b = distribute
            c = np.polyfit(a, b, 20)
            d = np.poly1d(c)
            print(d)
            bvals = d(a)
            plot1 = plt.plot(a, bvals, 'r', label = 'polyfit values')
            plt.title(title)
            plt.xlabel('The power level of elec(V)')
            plt.ylabel('The number of elec')
            plt.savefig(self.line_Directory.text() + '\\' + '3.1powerofElec.png')
            plt.close()

    def save_multi_pow(self, title, distribute):

        # 绘制并保存加入了权重后的双峰μ子信号第一个峰幅值的能量统计直方图
            plt.bar(range(len(distribute)), distribute)

        # 对直方图进行多项式函数曲线的拟合
            a = np.arange(0, len(distribute), 1)
            b = distribute
            c = np.polyfit(a, b, 20)
            d = np.poly1d(c)
            print(d)
            bvals = d(a)
            plot1 = plt.plot(a, bvals, 'r', label = 'polyfit values')
            plt.title(title)
            plt.xlabel('The multipower level of moun(V)')
            plt.ylabel('The number of moun')
            plt.savefig(self.line_Directory.text() + '\\' + '1.2multipowerofMoun.png')
            plt.close()

    def save_multi_qow(self, title, distribute):

        # 绘制并保存加入了权重后的双峰μ子信号第二个峰幅值的能量统计直方图
            plt.bar(range(len(distribute)), distribute)
        # 对直方图进行多项式函数曲线的拟合
            a = np.arange(0, len(distribute), 1)
            b = distribute
            c = np.polyfit(a, b, 20)
            d = np.poly1d(c)
            print(d)
            bvals = d(a)
            plot1 = plt.plot(a, bvals, 'r', label = 'polyfit values')
            plt.title(title)
            plt.xlabel('The multipower level of elec(V)')
            plt.ylabel('The number of elec')
            plt.savefig(self.line_Directory.text() + '\\' + '3.2multipowerofElec.png')
            plt.close()

    def save_unimodal_pow(self, title, distribute):

        # 绘制并保存单峰与双峰μ子信号第一个峰幅值的能量统计直方图
            plt.bar(range(len(distribute)), distribute)
        # 对直方图进行多项式函数曲线的拟合
            a = np.arange(0, len(distribute), 1)
            b = distribute
            c = np.polyfit(a, b, 20)
            d = np.poly1d(c)
            print(d)
            bvals = d(a)
            plot1 = plt.plot(a, bvals, 'r', label = 'polyfit values')
            plt.title(title)
            plt.xlabel('The power level of unimodal moun(V)')
            plt.ylabel('The number of unimodal moun')
            plt.savefig(self.line_Directory.text() + '\\' + '2.1powerofUnimodalMoun.png')
            plt.close()

    def save_multi_unimodal_pow(self, title, distribute):

        # 绘制并保存加入了权重后的单峰与双峰μ子信号第一个峰幅值的能量统计直方图
            plt.bar(range(len(distribute)), distribute)
        # 对直方图进行多项式函数曲线的拟合
            a = np.arange(0, len(distribute), 1)
            b = distribute
            c = np.polyfit(a, b, 20)
            d = np.poly1d(c)
            print(d)
            bvals = d(a)
            plot1 = plt.plot(a, bvals, 'r', label = 'polyfit values')
            plt.title(title)
            plt.xlabel('The multipower level of unimodal moun(V)')
            plt.ylabel('The number of unimodal moun')
            plt.savefig(self.line_Directory.text() + '\\' + '2.2multipowerofUnimodalMoun.png')
            plt.close()

class Getthread(QtCore.QThread):

        # 直接从示波器获取线程
        _signal = QtCore.pyqtSignal(int)
        saving_signal = QtCore.pyqtSignal(list,  list,  int)
        def __init__(self):
            super(Getthread,self).__init__()
            self.isgood = -1
        def Begin(self,  directory):
            self.wave = oscillator.The_wave(directory)
            self.start()
            return self.isgood
        def run(self):
            n = 0
            while Ui_MainWindow.stdo == 1:
                n = n + 1
                try:
                    x,  y = self.wave.get_wave(dmw.peakthresholdbox.value(), dmw.peakthresholdbox_2.value(), dmw.triggerbox.value())
                except:
                    self.quit()
                    self.isgood = -1
                    return
                else:
                    self.isgood = 0
                    self.saving_signal.emit(x,  y,  n)

class Analysis(QtCore.QThread):

        #分析的线程
        #_signal = QtCore.pyqtSignal(int)
        saving_signal = QtCore.pyqtSignal(str)

        # 将生成并存储图片的函数加入主线程
        save_img = QtCore.pyqtSignal(np.ndarray, np.ndarray, int, np.ndarray)
        save_ans = QtCore.pyqtSignal(str, list)
        save_pow = QtCore.pyqtSignal(str, list)
        save_qow = QtCore.pyqtSignal(str, list)
        save_multi_pow = QtCore.pyqtSignal(str, list)
        save_multi_qow = QtCore.pyqtSignal(str, list)
        save_unimodal_pow = QtCore.pyqtSignal(str, list)
        save_multi_unimodal_pow = QtCore.pyqtSignal(str, list)
        def __init__(self):
            super(Analysis, self).__init__()
        def begin(self, directory):
            self.directory = directory
            self.start()

        def run(self):

            # 定义256位的数组来存储多道分析的结果
            while Ui_MainWindow.stdo == 1:
                distribute_lifetime = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                distribute_muon     = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                distribute_elec     = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                multichannel_muon   = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                multichannel_elec   = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                unimodal_moun       = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                multichannel_unimodal=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

                # 双峰μ子寿命平均值初始化（双峰μ子信号两个峰的时间差）
                ave_time  = 0.0
                # 双峰μ子能量平均值初始化（双峰μ子信号第一个峰的幅值）
                ave_power = 0.0
                # 双峰e子能量平均值初始化（双峰μ子信号第二个峰的幅值）
                ave_qower = 0.0
                # 加权双峰μ子能量平均值初始化（加入了权重后的双峰μ子信号第一个峰的幅值）
                ave_multi_power = 0.0
                # 加权双峰e子能量平均值初始化（加入了权重后的双峰μ子信号第二个峰的幅值）
                ave_multi_qower = 0.0
                # 单峰双峰μ子能量平均值初始化（单峰与双峰μ子信号第一个峰的幅值）
                ave_unimodal = 0.0
                # 加权单峰双峰μ子能量平均值初始化（加入了权重后的单峰与双峰μ子信号第一个峰的幅值）
                ave_multi_unimodal = 0.0

                # 双峰μ子数量总量初始化
                num_of_moun   = 0
                # 双峰μ子能量总量初始化
                power_of_moun = 0
                # 双峰e子能量总量初始化
                power_of_elec = 0
                # 加入了权重后的双峰μ子能量总量初始化
                multipower_of_moun = 0
                # 加入了权重后的双峰e子能量总量初始化
                multipower_of_elec = 0
                # 单峰与双峰μ子数量总量初始化
                num_of_unimodal = 0
                # 单峰与双峰μ子能量总量初始化
                power_of_unimodal = 0
                # 加入了权重后的单峰与双峰μ子能量总量初始化
                multipower_of_unimodal = 0


                try:
                    num_of_file = len(os.listdir(self.directory))
                except:
                    self.saving_signal.emit('Sorry! The directory is wrong! Please check it out!')
                    Ui_MainWindow.stdo = 0
                    return
                else:
                    pass
                for i in range(1, num_of_file):
                    filename = self.directory + '\\' + str(i) + ".txt"
                    try:
                        x = np.loadtxt(filename,  delimiter='\t',  usecols = (0,),  dtype = float)
                        y = np.loadtxt(filename,  delimiter='\t',  usecols = (1,),  dtype = float)

                    except IOError:
                        continue

                    else:
                        y = np.fft.rfft(y)

                        for j in range(len(y)):
                            y[j] = -y[j]
                            if abs(y[j]) < 30:
                                y[j] = 0

                        y = np.fft.irfft(y)

                        indexes = peakutils.indexes(y, thres=0.2, min_dist=20)

                        for num in range(1,257):
                            if y[indexes[0]] < 0.04:
                                unimodal_moun[0] += 1
                            elif 0.04*num <= y[indexes[0]] <= 0.04*(num+1):
                                unimodal_moun[num] += 1
                            else:
                                pass

                            ave_unimodal += y[indexes[0]]

                        num_of_unimodal += 1

                        if (len(indexes) >= 2 and y[int((indexes[0] + indexes[1]) / 2)] < (0.9 * min(y[indexes[0]], y[indexes[1]])) and y[indexes[0]] == max(y[indexes])):
                            indexes = np.delete(indexes, range(2, len(indexes)))
                            print(indexes)
                            #self.save_img.emit(x, y, i, indexes)

                            if x[indexes[1]] - x[indexes[0]] < 1e-6:
                                distribute_lifetime[0] += 1
                            elif 1e-6 <= x[indexes[1]] - x[indexes[0]] < 2e-6:
                                distribute_lifetime[1] += 1
                            elif 2e-6 <= x[indexes[1]] - x[indexes[0]] < 3e-6:
                                distribute_lifetime[2] += 1
                            elif 3e-6 <= x[indexes[1]] - x[indexes[0]] < 4e-6:
                                distribute_lifetime[3] += 1
                            elif 4e-6 <= x[indexes[1]] - x[indexes[0]] < 5e-6:
                                distribute_lifetime[4] += 1
                            elif 5e-6 <= x[indexes[1]] - x[indexes[0]] < 6e-6:
                                distribute_lifetime[5] += 1
                            elif 6e-6 <= x[indexes[1]] - x[indexes[0]] < 7e-6:
                                distribute_lifetime[6] += 1
                            elif 7e-6 <= x[indexes[1]] - x[indexes[0]] < 8e-6:
                                distribute_lifetime[7] += 1
                            elif 8e-6 <= x[indexes[1]] - x[indexes[0]] < 9e-6:
                                distribute_lifetime[8] += 1
                            elif 9e-6 <= x[indexes[1]] - x[indexes[0]] < 10e-6:
                                distribute_lifetime[9] += 1
                            else:
                                distribute_lifetime[10] += 1

                            ave_time += x[indexes[1]] - x[indexes[0]]

                            for num in range(1,257):
                                if y[indexes[0]] < 0.1:
                                    distribute_muon[0] += 1
                                elif 0.04*num <= y[indexes[0]] < 0.04*(num+1):
                                    distribute_muon[num] += 1
                                else:
                                    pass

                            ave_power += y[indexes[0]]

                            for num in range(1,257):
                                if y[indexes[1]] < 0.04:
                                    distribute_elec[0] += 1
                                elif 0.04*num <= y[indexes[1]] < 0.04*(num+1):
                                    distribute_elec[num] += 1
                                else:
                                    pass

                            ave_qower += y[indexes[1]]

                            # 对双峰μ子信号中的第一个峰的幅值进行13731的权重加成
                            for num in range(1,257):
                                if num == 1:
                                    multichannel_muon[num] = 7*distribute_muon[num]/15 + 3*distribute_muon[num+1]/15 + 1*distribute_muon[num+2]/15
                                elif num == 2:
                                    multichannel_muon[num] = 3*distribute_muon[num-1]/15 + 7*distribute_muon[num]/15 + 3*distribute_muon[num+1]/15 + 1*distribute_muon[num+2]/15
                                elif num == 255:
                                    multichannel_muon[num] = 1*distribute_muon[num-2] + 3*distribute_muon[num-1]/15 + 7*distribute_muon[num]/15 + 3*distribute_muon[num+1]/15
                                elif num == 256:
                                    multichannel_muon[num] = 1*distribute_muon[num-2] + 3*distribute_muon[num-1]/15 + 7*distribute_muon[num]/15
                                else:
                                    multichannel_muon[num] = 1*distribute_muon[num-2] + 3*distribute_muon[num-1]/15 + 7*distribute_muon[num]/15 + 3*distribute_muon[num+1]/15 + 1*distribute_muon[num+2]/15
                            # 能量均值取加权之前的均值
                            ave_multi_power = ave_power

                            # 对双峰μ子信号中的第二个峰的幅值进行13731的权重加成
                            for num in range(1,257):
                                if num == 1:
                                    multichannel_elec[num] = 7*distribute_elec[num]/15 + 3*distribute_elec[num+1]/15 + 1*distribute_elec[num+2]/15
                                elif num == 2:
                                    multichannel_elec[num] = 3*distribute_elec[num-1]/15 + 7*distribute_elec[num]/15 + 3*distribute_elec[num+1]/15 + 1*distribute_elec[num+2]/15
                                elif num == 255:
                                    multichannel_elec[num] = 1*distribute_elec[num-2] + 3*distribute_elec[num-1]/15 + 7*distribute_elec[num]/15 + 3*distribute_elec[num+1]/15
                                elif num == 256:
                                    multichannel_elec[num] = 1*distribute_elec[num-2] + 3*distribute_elec[num-1]/15 + 7*distribute_elec[num]/15
                                else:
                                    multichannel_elec[num] = 1*distribute_elec[num-2] + 3*distribute_elec[num-1]/15 + 7*distribute_elec[num]/15 + 3*distribute_elec[num+1]/15 + 1*distribute_elec[num+2]/15
                            # 能量均值取加权之前的均值
                            ave_multi_qower = ave_qower

                            # 对单峰与双峰μ子信号中的第一个峰的幅值进行13731的权重加成
                            for num in range(1,257):
                                if num == 1:
                                    multichannel_unimodal[num] = 7*unimodal_moun[num]/15 + 3*unimodal_moun[num+1]/15 + 1*unimodal_moun[num+2]/15
                                elif num == 2:
                                    multichannel_unimodal[num] = 3*unimodal_moun[num-1]/15 + 7*unimodal_moun[num]/15 + 3*unimodal_moun[num+1]/15 + 1*unimodal_moun[num+2]/15
                                elif num == 255:
                                    multichannel_unimodal[num] = 1*unimodal_moun[num-2] + 3*unimodal_moun[num-1]/15 + 7*unimodal_moun[num]/15 + 3*unimodal_moun[num+1]/15
                                elif num == 256:
                                    multichannel_unimodal[num] = 1*unimodal_moun[num-2] + 3*unimodal_moun[num-1]/15 + 7*unimodal_moun[num]/15
                                else:
                                    multichannel_unimodal[num] = 1*unimodal_moun[num-2] + 3*unimodal_moun[num-1]/15 + 7*unimodal_moun[num]/15 + 3*unimodal_moun[num+1]/15 + 1*unimodal_moun[num+2]/15
                            # 能量均值取加权之前的均值
                            ave_multi_unimodal = ave_unimodal

                # 求和
                for item in distribute_lifetime:
                    num_of_moun += item
                for item in distribute_muon:
                    power_of_moun += item
                for item in distribute_elec:
                    power_of_elec += item
                for item in multichannel_muon:
                    multipower_of_moun += item
                for item in multichannel_elec:
                    multipower_of_elec += item
                for item in unimodal_moun:
                    power_of_unimodal += item
                for item in multichannel_unimodal:
                    multipower_of_unimodal += item
                try:
                    ave_time  /= num_of_moun
                    ave_power /= power_of_moun
                    ave_qower /= power_of_elec
                    ave_multi_power /= multipower_of_moun
                    ave_multi_qower /= multipower_of_elec
                    ave_unimodal /= power_of_unimodal
                    ave_multi_unimodal /= multipower_of_unimodal

                except ZeroDivisionError:
                    # 当选择了空文件夹时生成没有μ子的图片
                    self.save_ans.emit('Sorry! No moun!', distribute_lifetime)
                    self.save_pow.emit('Sorry! No moun!', distribute_muon)
                    self.save_qow.emit('Sorry! No moun!', distribute_muon)
                    self.save_multi_pow.emit('Sorry! No moun!', distribute_muon)
                    self.save_multi_qow.emit('Sorry! No moun!', distribute_muon)
                    self.save_unimodal_pow.emit('Sorry! No moun!', unimodal_moun)
                    self.save_multi_unimodal_pow.emit('Sorry! No moun!', unimodal_moun)

                    # 当选择了空文件夹时在主界面右下角显示没有μ子
                    self.saving_signal.emit('Done!!')
                    self.saving_signal.emit('The number of moun is ' + str(num_of_moun) + ' in ' + str(len(os.listdir(self.directory))) + 'datas!')
                    self.saving_signal.emit('The number of unimodal moun is ' + str(num_of_unimodal) + ' in ' + str(len(os.listdir(self.directory))) + 'datas!')
                    Ui_MainWindow.stdo = 0

                else:
                    # 当分析结束后在选择文件夹内生成图片
                    self.save_ans.emit('The number of moun is ' + str(num_of_moun) + '\n' + 'The average lifetime is ' + str(ave_time), distribute_lifetime)
                    self.save_pow.emit('The number of moun is ' + str(num_of_moun) + '\n' + 'The average power of moun is ' + str(ave_power), distribute_muon)
                    self.save_qow.emit('The number of elec is ' + str(num_of_moun) + '\n' + 'The average power of elec is ' + str(ave_qower), distribute_elec)
                    self.save_multi_pow.emit('The number of moun is ' + str(num_of_moun) + '\n' + 'The average multipower of moun is ' + str(ave_multi_power), multichannel_muon)
                    self.save_multi_qow.emit('The number of elec is ' + str(num_of_moun) + '\n' + 'The average multipower of elec is ' + str(ave_multi_qower), multichannel_elec)
                    self.save_unimodal_pow.emit('The number of unimodal moun is ' + str(num_of_unimodal) + '\n' + 'The average power of unimodal moun is ' + str(ave_unimodal), unimodal_moun)
                    self.save_multi_unimodal_pow.emit('The number of unimodal moun is ' + str(num_of_unimodal) + '\n' + 'The average multipower of unimodal moun is ' + str(ave_multi_unimodal), multichannel_unimodal)

                    # 当分析结束后在主界面右下角显示分析结果
                    self.saving_signal.emit('Done!!')
                    self.saving_signal.emit('The number of moun is' + str(num_of_moun) + ' in ' + str(len(os.listdir(self.directory))) + 'datas!')
                    self.saving_signal.emit('The number of unimodal muon is' + str(num_of_unimodal) + ' in ' + str(len(os.listdir(self.directory))) + 'datas!')
                    self.saving_signal.emit('The average lifetime is' + str(ave_time))
                    self.saving_signal.emit('The average power of moun is' + str(ave_power))
                    self.saving_signal.emit('The average power of elec is' + str(ave_qower))
                    self.saving_signal.emit('The average multipower of moun is ' + str(ave_multi_power))
                    self.saving_signal.emit('The average multipower of elec is ' + str(ave_multi_qower))
                    self.saving_signal.emit('The average power of unimodal moun is' + str(ave_unimodal))
                    self.saving_signal.emit('The average multipower of unimodal moun is ' + str(ave_multi_unimodal))

                    # 停止执行一切操作，等待主界面函数下达命令
                    Ui_MainWindow.stdo = 0

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    t = QtCore.QElapsedTimer()
    t.start()
    splash = QtWidgets.QSplashScreen(QtGui.QPixmap("logo.jpg"))
    while t.elapsed() < 1000:
        splash.show()
    splash.finish(splash)
    dmw = DesignerMainWindow()
    dmw.show()
    sys.exit(app.exec_())