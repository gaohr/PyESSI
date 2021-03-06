# -*- coding: utf-8 -*-
"""
Created Jan 2018

@author: Hao Chen

Class:
    SoilInfo
        functions:
            __init__(self)
            ReadSoilFile(self, soilFilename)
            CalcSoilPara(self)
            CalcAridIndex(self, bConst)
            SoilWaterDeficitPercent(self)
            SoilWaterDeficitContent(self)
            SoilAvgWater(self)

Functions:
    GetSoilTypeName(SoilTypeID)


"""

# load needed python modules
import os
import util.config
import math
import time

class SoilInfo:
    def __init__(self, stn, sfd):
        self.Soil_Name = ""
        self.Soil_id = 0
        self.iLayer = 0  # 土壤层数
        self.rootdepth = 0.  # 根区深度

        self.SP_BD = 0.  # 土壤剖面平均湿容重 g·cm-3
        self.SP_Por = 0.  # 土壤剖面平均孔隙率 %
        self.SP_Fc = 0.  # 田间持水量时土壤含水量 mm
        self.SP_Sat = 0.  # 土壤饱和时土壤含水量 mm
        self.SP_Sw = 0.  # 土壤实际含水量 mm
        self.SP_Wp = 0.  # 枯萎点时土壤含水量 mm
        self.SP_Arid = 0.  # 土壤干湿指标值
        self.Horton_K = 0.05  # 霍顿下渗曲线系数

        self.TPercolation = 0.  # 渗流阈值
        self.SP_Temp = 0.  #

        self.SP_Sat_K = 0.  # 土壤剖面平均饱和导水率

        self.SL_ID = []
        self.SL_Z = []  # 土层深度 mm
        self.SL_BD = []  # 土壤湿容重 g·cm-3
        self.SL_AWC = []  # 有效持水量 mm H2O / mm soil
        self.SL_Sat_K = []  # 饱和导水率 mm/hr
        self.SL_Stable_F = []  # 稳定下渗率系数
        self.SL_Org_C = []  # 有机物含量 %
        self.SL_Clay = []  # 土壤中粉粒含量组成 %
        self.SL_Silt = []  # 土壤中粘粒含量组成 %
        self.SL_Sand = []  # 土壤中砂粒含量组成 %
        self.SL_Rock = []  # 土壤中砾石含量组成 %
        self.SL_Init_F = []  #
        self.SL_bFillOK = []  #

        self.SL_HK = []  # 土壤水力传导率系数
        self.SL_P_Fc = []  # 田间持水量时植被可吸收水量 mm
        self.SL_Por = []  # 土层孔隙率 %
        self.SL_SW = []  # 土层每日实际可供水量 mm
        self.SL_Wp = []  # 枯萎点时土层含水量
        self.SL_Sat = []  # 土壤水饱和时土层可供水量 mm
        self.SL_FcRatio = []  #
        self.SL_WpRatio = []  #
        self.albedo = 0.23  #

        self.soilTypename = stn
        self.solFileDict = sfd

        # 这三个变量是否有需要定义？？
        self.SL_StaInfil = []
        self.SL_InitInfil = []
        self.SP_WFCS = 0.

    def ReadSoilFile(self, soilFilename):
        '''
        从文件中加载每一种指定土壤类型的主要输入物理参数（固有参数）
        :param soilTypeName:
        :param soilFilename:
        :return:
        '''
        soilInfos = self.solFileDict[soilFilename]
        self.Soil_Name = soilInfos[0].split('\n')[0].strip().split()[1]
        self.iLayer = int(soilInfos[1].split('\n')[0].strip().split()[1])
        self.rootdepth = float(soilInfos[2].split('\n')[0].strip().split()[1])
        self.albedo = float(soilInfos[3].split('\n')[0].strip().split()[1])
        self.Horton_K = float(soilInfos[4].split('\n')[0].strip().split()[1])
        self.InitSWP = float(soilInfos[5].split('\n')[0].strip().split()[1])
        for i in range(self.iLayer):
            self.SL_ID.append(i + 1)
            self.SL_Z.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[0]))
            self.SL_BD.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[1]))
            self.SL_AWC.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[2]))
            self.SL_Sat_K.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[3]))
            self.SL_Stable_F.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[4]))
            self.SL_Org_C.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[5]))
            self.SL_Clay.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[6]))
            self.SL_Silt.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[7]))
            self.SL_Sand.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[8]))
            self.SL_Rock.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[9]))
            self.SL_Init_F.append(float(soilInfos[i + 8].split('\n')[0].split(':')[1].strip().split()[10]))
            self.SL_bFillOK.append(True)

        self.CalcSoilPara()
        self.TPercolation = (self.SP_Sat - self.SP_Fc) / self.SP_Sat_K

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +    功能：利用固有土壤参数计算其它有用的土壤物理参数 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcSoilPara(self):
        for i in range(self.iLayer):
            self.SL_StaInfil.append(self.SL_Stable_F[i] * self.SL_Sat_K[i])
            self.SL_InitInfil.append(self.SL_Init_F[i] * self.SL_Sat_K[i])

            self.SL_WpRatio.append(0.4 * self.SL_Clay[i] * self.SL_BD[i] / 100.)
            if self.SL_WpRatio[i] <= 0.:
                self.SL_WpRatio[i] = 0.005

            self.SL_FcRatio.append(self.SL_WpRatio[i] + self.SL_AWC[i])
            self.SL_Por.append(1. - self.SL_BD[i] / 2.65)

            if self.SL_FcRatio[i] >= self.SL_Por[i]:
                self.SL_FcRatio[i] = self.SL_Por[i] - 0.05
                self.SL_WpRatio[i] = self.SL_FcRatio[i] - self.SL_AWC[i]
                if self.SL_WpRatio[i] <= 0.:
                    self.SL_FcRatio[i] = self.SL_Por[i] * 0.75
                    self.SL_WpRatio[i] = self.SL_Por[i] * 0.25

        acumudepth, sumpor, lyrdepth, pormm, stainfil, stainit, suminfil, suminit, sumsat_k, sat_k = 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.

        for i in range(self.iLayer):
            lyrdepth = self.SL_Z[i] - acumudepth
            pormm = self.SL_Por[i] * lyrdepth
            sat_k = self.SL_Sat_K[i] * lyrdepth
            stainfil = self.SL_StaInfil[i] * lyrdepth
            stainit = self.SL_InitInfil[i] * lyrdepth
            sumpor += pormm
            suminfil += stainfil
            suminit += stainit
            sumsat_k += sat_k
            self.SL_Sat.append((self.SL_Por[i] - self.SL_WpRatio[i]) * lyrdepth)
            self.SP_Sat += self.SL_Sat[i]
            self.SL_Wp.append(self.SL_WpRatio[i] * lyrdepth)
            self.SP_Wp += self.SL_Wp[i]
            self.SL_P_Fc.append((self.SL_FcRatio[i] - self.SL_WpRatio[i]) * lyrdepth)
            self.SP_Fc += self.SL_P_Fc[i]
            self.SL_SW.append(self.SL_P_Fc[i] * self.InitSWP)
            self.SL_HK.append((self.SL_Sat[i] - self.SL_P_Fc[i]) / self.SL_Sat_K[i])
            if self.SL_HK[i] < 1.:
                self.SL_HK[i] = 1.
            self.SP_Sw += self.SL_SW[i]
            acumudepth = self.SL_Z[i]

        self.SP_Por = sumpor / self.SL_Z[self.iLayer - 1]
        self.SP_BD = 2.65 * (1. - self.SP_Por)
        self.SP_Stable_Fc = suminfil / self.SL_Z[self.iLayer - 1]
        self.SP_Init_F0 = suminit / self.SL_Z[self.iLayer - 1]
        self.SP_Sat_K = sumsat_k / self.SL_Z[self.iLayer - 1]

        if self.SP_Sw < self.SP_Wp:
            self.SP_Sw = self.SP_Wp * 1.05

        f = 6.5309 - 7.32561 * self.SL_Por[0] + 0.001583 * math.pow(self.SL_Clay[0], 2)
        + 3.809479 * math.pow(self.SL_Por[0], 2) + 0.000344 * self.SL_Sand[0] * self.SL_Clay[0]
        - 0.049837 * self.SL_Por[0] * self.SL_Sand[0] + 0.001608 * math.pow(self.SL_Por[0], 2) * math.pow(self.SL_Sand[0], 2)
        + 0.001602 * math.pow(self.SL_Por[0], 2) * math.pow(self.SL_Clay[0], 2)
        - 0.0000136 * math.pow(self.SL_Sand[0], 2) * self.SL_Clay[0]
        - 0.003479 * math.pow(self.SL_Clay[0], 2) * self.SL_Por[0]
        - 0.000799 * math.pow(self.SL_Sand[0], 2) * self.SL_Por[0]

        self.SP_WFCS = 10. * math.exp(f)

    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +                功能：土壤干湿指标值 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    def CalcAridIndex(self, bConst):
        '''
        :param bConst:
        :return:
        '''
        if (bConst):
            # 用常数计算
            self.SP_Arid = (self.SP_Fc - self.SP_Wp) / self.SP_Fc
        else:
            # 用变量计算
            self.SP_Arid = (self.SP_Sw - self.SP_Wp) / self.SP_Fc


    # / *+++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # +                                                        +
    # +            功能：计算初始土壤水赤字 +
    # +                                                        +
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++ * /
    # 土壤水赤字比例
    def SoilWaterDeficitPercent(self):
        dthet = (1.0 - self.SP_Sw / self.SP_Fc) * self.SP_Por
        return dthet

    # 土壤水赤字量
    def SoilWaterDeficitContent(self):
        dthet = (1.0 - self.SP_Sw / self.SP_Fc) * self.SP_Por * self.rootdepth
        return dthet

    # 土壤剖面平均含水量
    def SoilAvgWater(self):
        dret = self.SP_Sw / self.rootdepth * 100
        return dret