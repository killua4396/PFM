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
temp1 = temp1.sort_values(by="Time_slot")
temp1 = temp1.reset_index(drop=True)
Earliest_Time = temp1.loc[0]["Time_slot"]
temp1 = pd.DataFrame(temp1.value_counts())

#将时间段出站客流进行统计
temp2 = pd.DataFrame()
temp2[["Station_name","Time_slot"]] = trips[["Out_station_name","out_time_slot"]]
temp2 = temp2.sort_values(by="Time_slot")
temp2 = temp2.reset_index(drop = True)
Lastest_Time = temp2.loc[temp2.shape[0]-1]["Time_slot"]
temp2 = pd.DataFrame(temp2.value_counts())

#创建含有所有时间段的基本数据，主要用于后续shift时间
StartTime = pd.to_datetime(Earliest_Time)
EndTime = pd.to_datetime(Lastest_Time)
value = []
index1 = []
index2 = []
import datetime
for S_name in station["Station_name"]:
    Time = StartTime
    while Time != EndTime + datetime.timedelta(days=1):
        value.append(0)
        index1.append(S_name)
        index2.append(str(Time))
        Time = Time + datetime.timedelta(minutes=30)

Timeslot_pf = pd.DataFrame(index=[index1,index2])

#按时间段，组成基本数据格式
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

#定义一个函数用于shift时间
def time_shift(data_in_sta, data_in_shfit_cols, data_out_shfit_cols):
    lag_start = 48
    lag_end = 48 * 3
    data_out_sta = data_in_sta.copy()
    for i in range(lag_start, lag_end + 1, 48):
        for col in data_in_shfit_cols:
            data_in_sta[col + "_lag_{}".format(i)] = data_in_sta[col].shift(i)
            if (col != 'InNums') & (col != 'OutNums') & (i == lag_end):
                del data_in_sta[col]
        for col1 in data_out_shfit_cols:
            data_out_sta[col1 + "_lag_{}".format(i)] = data_out_sta[col1].shift(i)
            if (col1 != 'InNums') & (col1 != 'OutNums') & (i == lag_end):
                del data_out_sta[col1]

    return data_in_sta, data_out_sta

#shift时间前期处理
data_in_shfit = pd.DataFrame()
data_out_shfit = pd.DataFrame()

data_in_shfit_cols = list(Timeslot_pf)
data_in_shfit_cols.remove('Station_name')
data_in_shfit_cols.remove('Time_slot')
data_in_shfit_cols.remove('Day')
data_in_shfit_cols.remove('Dayofweek')
data_in_shfit_cols.remove('hour')
data_in_shfit_cols.remove('min')
data_in_shfit_cols.remove("date_type")


data_out_shfit_cols = list(Timeslot_pf)
data_out_shfit_cols.remove('Station_name')
data_out_shfit_cols.remove('Time_slot')
data_out_shfit_cols.remove('Day')
data_out_shfit_cols.remove('Dayofweek')
data_out_shfit_cols.remove('hour')
data_out_shfit_cols.remove('min')
data_out_shfit_cols.remove("date_type")

#对站点逐个进行shift时间
for i in station["Station_name"]:
    data_temp = Timeslot_pf[Timeslot_pf['Station_name'] == i]
    data_in_sta,data_out_sta = time_shift(data_temp,data_in_shfit_cols,data_out_shfit_cols)
    data_in_shfit = pd.concat([data_in_shfit, data_in_sta], axis=0, ignore_index=True)
    data_out_shfit = pd.concat([data_out_shfit, data_out_sta], axis=0, ignore_index=True)

#处理数据，分离出数据集和label
del data_in_shfit["Time_slot"]
data_in_shfit.fillna(0.0,inplace=True)
X = data_in_shfit.drop(columns=["InNums","OutNums"])
y_in = data_in_shfit["InNums"]
y_out = data_in_shfit["OutNums"]

#对数据进行标准化处理
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
StdScaler = StandardScaler()
wait = X[["Station_name","Dayofweek","Day","hour","min","date_type"]]
wait["Station_name"] = wait["Station_name"].apply(lambda x:x[3:])
wait = np.array(wait)
temp = X.drop(columns=["Station_name","Dayofweek","Day","hour","min","date_type"])
StdScaler.fit(temp)
temp = StdScaler.transform(temp)
X = np.hstack((wait,temp))

#train_test_split
len_X = X.shape[0]
X_train = X[:int(len_X*0.7)]
X_test = X[int(len_X*0.7):int(len_X*0.95)]
y_train = y_in[:int(len_X*0.7)]
y_test = y_in[int(len_X*0.7):int(len_X*0.95)]

#模型训练（未调参）
other_params = {'learning_rate': 0.1, 'n_estimators': 500, 'max_depth': 5, 'min_child_weight': 1, 'seed': 0,
                    'subsample': 0.8, 'colsample_bytree': 0.8, 'gamma': 0, 'reg_alpha': 0, 'reg_lambda': 1}
model = xgb.XGBRegressor(**other_params)
model.fit(X_train,y_train)
