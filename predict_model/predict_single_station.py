import pandas as pd
import numpy as np
from sshtunnel import SSHTunnelForwarder
import pymysql
import matplotlib.pyplot as plt

server = SSHTunnelForwarder(
    ssh_address_or_host=('106.15.10.138',22),
    ssh_username= 'root',
    ssh_password= 'Redhome@)@)',
    remote_bind_address=('localhost',3306)
)

#获取数据库数据
server.start()
conn = pymysql.connect(
    host='127.0.0.1',
    port = server.local_bind_port,
    user='SWORD',
    password='SwordRefersToS11',
    db = 'sword',
    charset='utf8'
)
trips = pd.read_sql('select * from trips',con=conn)
workdays = pd.read_sql('select * from workdays2020',con=conn)
station = pd.read_sql('select * from station',con=conn)
conn.close()
server.close()

#将时间分隔成以半小时为间隔的时间段
def changeT_orderby_halfhour(x):
    t = int(x[14:16])
    if t<30 and t>=0:
        t = "00"
    elif t>=30 and t<=59:
        t = "30"
    return (x[:14] + t + ":00")

#将时间分段
trips["in_time_slot"] = trips["In_station_time"].apply(changeT_orderby_halfhour)
trips["out_time_slot"] = trips["Out_station_time"].apply(changeT_orderby_halfhour)

#将时间段进站客流进行统计
temp1 = pd.DataFrame()
temp1[["Station_name","Time_slot"]] = trips[["In_station_name","in_time_slot"]]
temp1 = pd.DataFrame(temp1.value_counts())

#将时间段出站客流进行统计
temp2 = pd.DataFrame()
temp2[["Station_name","Time_slot"]] = trips[["Out_station_name","out_time_slot"]]
temp2 = pd.DataFrame(temp2.value_counts())

#将有客流的出站时间段和有客流的入站时间段拼接在一起
a = pd.DataFrame()
a[["Station_name","Time_slot"]] = trips[["In_station_name","in_time_slot"]]
b = pd.DataFrame()
b[["Station_name","Time_slot"]] = trips[["Out_station_name","out_time_slot"]]
c = a.append(b)
Timeslot_pf = c

#按时间段，组成基本数据格式
Timeslot_pf = Timeslot_pf.groupby(["Station_name","Time_slot"]).agg("count")
Timeslot_pf["InNums"] = temp1[0]
Timeslot_pf["OutNums"] = temp2[0]

#填补空值
Timeslot_pf = Timeslot_pf.fillna(0.0)

#用于过渡
Timeslot_pf["idx"] = Timeslot_pf.index

#从index获得站点名称
def get_Station_name(x):
    return x[0]

Timeslot_pf["Station_name"] = Timeslot_pf['idx'].apply(get_Station_name)

#从index获得时间段
def get_Time_slot(x):
    return x[1]

Timeslot_pf["Time_slot"] = Timeslot_pf['idx'].apply(get_Time_slot)

#重置index并且去掉idx行
Timeslot_pf = Timeslot_pf.reset_index(drop = True)
Timeslot_pf = Timeslot_pf.drop(columns=['idx'])

#添加一些基础特征
Timeslot_pf["Time_slot"] = Timeslot_pf["Time_slot"].apply(lambda x:pd.to_datetime(x))
Timeslot_pf["Dayofweek"] = Timeslot_pf["Time_slot"].apply(lambda x:x.dayofweek)
Timeslot_pf["Day"] = Timeslot_pf["Time_slot"].apply(lambda x:x.day)
Timeslot_pf["hour"] = Timeslot_pf["Time_slot"].apply(lambda x : x.hour)
Timeslot_pf["min"] = Timeslot_pf["Time_slot"].apply(lambda x : x.minute)

#定义一个函数添加更多特征
def more_feature(result):
    tmp = result.copy()
    tmp = tmp[['Station_name', 'Dayofweek', 'Day', 'hour']]
    ###按week计算每个站口每小时客流量特征
    tmp = result.groupby(['Station_name', 'Dayofweek', 'hour'], as_index=False)['InNums'].agg({
        'inNums_ID_dh_max': 'max',  ###
        'inNums_ID_dh_min': 'min',  ###
        'inNums_ID_dh_mean': 'mean',  ###
        'inNums_ID_dh_sum': 'sum'
    })
    result = result.merge(tmp, on=['Station_name', 'Dayofweek', 'hour'], how='left')
    ###按week计算每个站口客流量特征
    tmp = result.groupby(['Station_name', 'Dayofweek'], as_index=False)['InNums'].agg({
        'inNums_ID_d_max': 'max',
        'inNums_ID_d_min': 'min',  # 都为0
        'inNums_ID_d_mean': 'mean',  ##
        'inNums_ID_d_sum': 'sum'
    })
    result = result.merge(tmp, on=['Station_name', 'Dayofweek'], how='left')

    ###每个站口所有天客流量特征
    tmp = result.groupby(['Station_name'], as_index=False)['InNums'].agg({
        'inNums_ID_max': 'max',
        'inNums_ID_min': 'min',
        'inNums_ID_mean': 'mean',  ##
        'inNums_ID_sum': 'sum'
    })
    result = result.merge(tmp, on=['Station_name'], how='left')
    ###每天所有站口客流量特征
    tmp = result.groupby(['Day'], as_index=False)['InNums'].agg({
        'inNums_d_max': 'max',
        'inNums_d_min': 'min',  # 都为0
        'inNums_d_mean': 'mean',  ##
        'inNums_d_sum': 'sum'
    })
    result = result.merge(tmp, on=['Day'], how='left')

    ###出站与进站类似
    tmp = result.groupby(['Station_name', 'Dayofweek', 'hour'], as_index=False)['OutNums'].agg({
        'outNums_ID_dh_max': 'max',
        'outNums_ID_dh_min': 'min',  ##
        'outNums_ID_dh_mean': 'mean',  ##
        'outNums_ID_dh_sum': 'sum'
    })
    result = result.merge(tmp, on=['Station_name', 'Dayofweek', 'hour'], how='left')

    tmp = result.groupby(['Station_name', 'Dayofweek'], as_index=False)['OutNums'].agg({
        'outNums_ID_d_max': 'max',
        'outNums_ID_d_min': 'min',  # 都为0
        'outNums_ID_d_mean': 'mean',  ##
        'outNums_ID_d_sum': 'sum'
    })
    result = result.merge(tmp, on=['Station_name', 'Dayofweek'], how='left')

    tmp = result.groupby(['Station_name'], as_index=False)['OutNums'].agg({
        'outNums_ID_max': 'max',
        'outNums_ID_min': 'min',
        'outNums_ID_mean': 'mean',
        'outNums_ID_sum': 'sum'
    })
    result = result.merge(tmp, on=['Station_name'], how='left')

    tmp = result.groupby(['Day'], as_index=False)['OutNums'].agg({
        'outNums_d_max': 'max',
        'outNumss_d_min': 'min',  # 都为0
        'outNums_d_mean': 'mean',
        'outNums_d_sum': 'sum'
    })
    result = result.merge(tmp, on=['Day'], how='left')

    return result

Timeslot_pf = more_feature(Timeslot_pf)

#去掉一些特征值不正常的列
good_cols = list(Timeslot_pf.columns)
for col in Timeslot_pf.columns:
    rate = Timeslot_pf[col].value_counts(normalize=True, dropna=False).values[0]
    if rate > 0.90:
        good_cols.remove(col)
        print(col, rate)
Timeslot_pf = Timeslot_pf[good_cols]

#定义一个日期类型转换字典
transform = {}
for i in range(366):
    temp = {workdays.loc[i, "Dayofyear"]: workdays.loc[i, "Date_type"]}
    transform.update(temp)

#去掉2019年的数据
for index,row in Timeslot_pf.iterrows():
    if row.Time_slot.year != 2020:
        Timeslot_pf = Timeslot_pf.drop(index=index)
    if row.Time_slot.year == 2020:
        break

#添加日期类型特征
Timeslot_pf["date_type"] = Timeslot_pf["Time_slot"].apply(lambda x : transform[x.dayofyear])
Timeslot_pf = Timeslot_pf.reset_index(drop = True)

print(Timeslot_pf)