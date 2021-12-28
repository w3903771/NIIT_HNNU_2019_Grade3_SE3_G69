# NIIT_HNNU_2019_Grade3_SE3_G69

***
![image](https://img.shields.io/github/checks-status/w3903771/NIIT_HNNU_2019_Grade3_SE3_G69/main)
![image](https://img.shields.io/github/repo-size/w3903771/NIIT_HNNU_2019_Grade3_SE3_G69?label=size)
![image](https://img.shields.io/badge/License-Apache--2.0-green)

A project for PUBG data analyze with scraping in Python.</br></br>
This project is also being manually synchronized on [Github](https://github.com/w3903771/PUBG-data-analyze)

# Overview

***
This project mainly analyzed data from more than 2,000 PUBG matches from 12,546 different players and gathered more than
22w information to promote a proposal about this game.

```
Project
│   README.md
│   LICENSE
│   config.ini                      配置文件
│   data.sql                        总数据
│   requirement.txt                 依赖库
│   代码规范.docx 
│   
└───Fetch
│   │   Selenium.py                 基于selenium的单个网页爬取
│   │   Spider.py                   爬取控制
│   │   Sql.py           
│      
└───API_getdata
│   │   Get_data.py                 获取比赛数据
│   │   Sql.py              
│  
└───Doc                             项目日志与技术文档
│   │   Dev log 7.8.docx
│   │   Dev log 7.9.docx
│   │   Dev log 7.10.docx
│   │   Dev log 7.11.docx
│   │   Dev log 7.12.docx
│   │   技术文档.md
│  
└───html
│   │   hdrelitu.png                海岛热力图
│   │   smrelitu.png                沙漠热力图
│   │   index.html                  展示网页
│   │   index.css
│   │   video.mp4
│   │   如何优雅地吃鸡.ipython       数据分析文件
│   │ 
    └───map
│   │   erangel.jpg
│   │   miramar
│   
```

# Requirements

***

* Python 3.5+
* PUBG Api
* pandas
* numpy
* pymysql
* BeautifulSoup
* configparser
* chicken_dinner
* selenium
* Works on Windows

# Installation

***
To run this project, first download this file to your computer. You can get it by either Zip or using git command

```
git clone https://gitee.com/light_of_heaven/PUBG-data-analyze.git
```

Run commands below in cmd to install the core dependencies.

```bash
pip install -r requirements.txt
```

Change config.ini to make sure your PUBG key and database is well configured。</br>

You can apply for a PUBG key at [https://developer.pubg.com/](https://developer.pubg.com/)

# Dev log

***

* [2021.07.08](https://gitee.com/light_of_heaven/PUBG-data-analyze/blob/main/Doc/Dev%20log%207.8.docx) Create Git
  project, prepare framework
* [2021.07.09](https://gitee.com/light_of_heaven/PUBG-data-analyze/blob/main/Doc/Dev%20log%207.9.docx) Ready for
  scraping, select data needed from api
* [2021.07.10](https://gitee.com/light_of_heaven/PUBG-data-analyze/blob/main/Doc/Dev%20log%207.10.docx) Done for
  username scraping, arranging for match data
* [2021.07.11](https://gitee.com/light_of_heaven/PUBG-data-analyze/blob/main/Doc/Dev%20log%207.11.docx) Start getting
  match data, design web site
* [2021.07.12](https://gitee.com/light_of_heaven/PUBG-data-analyze/blob/main/Doc/Dev%20log%207.12.docx) Finally done!

# Thanks

***
Thanks for my deer team members[@sorplus](https://gitee.com/sorplus)
[@zhang-botian](https://gitee.com/zhang-botian)
[@oreo12138](https://gitee.com/oreo12138)
[@tw1stzz](https://gitee.com/tw1stzz)
</br>We are so struggled together to finish this work in 5 days 