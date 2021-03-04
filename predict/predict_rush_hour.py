import numpy as np
import pandas as pd
import pymysql
import matplotlib.pyplot as plt
from sshtunnel import SSHTunnelForwarder

#从数据导入数据
server = SSHTunnelForwarder(
    ssh_address_or_host=('106.15.10.138',22),
    ssh_username= 'root',
    ssh_password= 'Redhome@)@)',
    remote_bind_address=('localhost',3306)
)
server.start()
conn = pymysql.connect(
    host='127.0.0.1',
    port = server.local_bind_port,
    user='SWORD',
    password='SwordRefersToS11',
    db = 'sword',
    charset='utf8'
)
nextday = pd.read_sql('select * from predict_nextday_info',con = conn)
station = pd.read_sql('select * from station',con = conn)
conn.close()
server.close()

#分离hour，min数据
nextday["hour"] = nextday["Timeslot"].apply(lambda x : int(x[11:13]))
nextday["min"] = nextday["Timeslot"].apply(lambda x : int(x[14:16]))

#判断是否处于早晚高峰时间
morning_rushhour_pf = nextday[(nextday.hour == 7) | (nextday.hour == 8)]
evening_rushhour_pf = nextday[((nextday.hour== 16) & (nextday.min == 30))| ((nextday.hour== 18) & (nextday.min == 00))|(nextday.hour== 17)]

#统计出早晚高峰进出站客流
morning_rushhour_pf = morning_rushhour_pf[["Station_name","InNums","OutNums"]].groupby(["Station_name"]).agg("sum")
evening_rushhour_pf = evening_rushhour_pf[["Station_name","InNums","OutNums"]].groupby(["Station_name"]).agg("sum")

#算出早高峰站点客流
morning_rushhour_pf["morning_rushhour_pf"] = morning_rushhour_pf["InNums"] + morning_rushhour_pf["OutNums"]
del morning_rushhour_pf["InNums"]
del morning_rushhour_pf["OutNums"]

#算出晚高峰站点客流
evening_rushhour_pf["evening_rushhour_pf"] = evening_rushhour_pf["InNums"] + evening_rushhour_pf["OutNums"]
del evening_rushhour_pf["InNums"]
del evening_rushhour_pf["OutNums"]

#将两个dataframe整合在一起
rushhour_pf = morning_rushhour_pf
rushhour_pf["evening_rushhour_pf"] = evening_rushhour_pf["evening_rushhour_pf"]
rushhour_pf["Station_name"] = rushhour_pf.index
rushhour_pf = rushhour_pf.reset_index(drop =True)

#将数据写入数据库
server.start()
conn = pymysql.connect(
    host='127.0.0.1',
    port=server.local_bind_port,
    user='SWORD',
    password='SwordRefersToS11',
    db='sword',
    charset='utf8'
)

cursor = conn.cursor(pymysql.cursors.SSDictCursor)
sql1 = 'Delete from predict_rushhour_info'
num1 = cursor.execute(sql1)
if num1 > 0:
    conn.commit()
else:
    conn.rollback()

for row in rushhour_pf.iterrows():
    Day = "NextWeekDay1"
    Station_name = row[1][2]
    Morning_rushhour_pf = row[1][0]
    Evening_rushhour_pf = row[1][1]
    sql = "insert into predict_rushhour_info values(%s,%s,%s,%s)"
    arg = (Day, Station_name, Morning_rushhour_pf, Evening_rushhour_pf)
    num = cursor.execute(sql, arg)
    if num > 0:
        conn.commit()
    else:
        conn.rollback()

conn.close()
server.close()
