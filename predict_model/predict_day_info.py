import numpy as np
import pandas as pd
import pymysql
import matplotlib.pyplot as plt
from sshtunnel import SSHTunnelForwarder

#用于提取时间戳中的日期
def To_day(x):
    return x.date()

#转化成星期
def ToDayofWeek(x):
    return x.dayofweek

#将时间字符串转化为时间戳
def Totimestamp(x):
    return pd.to_datetime(x)

#将日期转化为日期类型
def Day_to_DateType(x):
    return transform[x.dayofyear]



#建立SSH服务
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
conn.close()
server.close()

#将进站时间字符串转化成进站时间时间戳
trips['in_timestamp'] = trips['In_station_time'].apply(lambda x:pd.to_datetime(x))

#添加一列日期数据
trips["date"] = trips["in_timestamp"].apply(To_day)

#将每日的客流统计出来存入到dataframe中
EachDay_pf = pd.DataFrame(trips["date"].value_counts())
EachDay_pf["pf"] = EachDay_pf["date"]
EachDay_pf["date"] = EachDay_pf.index

#将原来的时间字符串数据转化为时间戳数据
EachDay_pf["date"] = EachDay_pf["date"].apply(Totimestamp)

#根据时间顺序排序
EachDay_pf = EachDay_pf.sort_values(by = "date")

#重置index列
EachDay_pf = EachDay_pf.reset_index(drop=True)

#添加一列Week特征
EachDay_pf["dayofweek"] = EachDay_pf["date"].apply(ToDayofWeek)

#定义一个日期类型转化字典
transform = {}
for i in range(366):
    temp = {workdays.loc[i, "Dayofyear"]: workdays.loc[i, "Date_type"]}
    transform.update(temp)

#添加一列日期类型特征
EachDay_pf["date_type"] = EachDay_pf["date"].apply(Day_to_DateType)

#添加三列特征，分别是前一日客流量，前五日平均客流量，前十日平均客流量
EachDay_pf['pre_date_flow'] = EachDay_pf.loc[:,['pf']].shift(1)
EachDay_pf['MA5'] = EachDay_pf['pf'].rolling(5).mean()
EachDay_pf['MA10'] = EachDay_pf['pf'].rolling(10).mean()

#去掉非2020年的数据行（开头几日的数据过少，明显不正常）
for index,row in EachDay_pf.iterrows():
    if row.date.year != 2020:
        EachDay_pf = EachDay_pf.drop(index=index)

#去除空值
EachDay_pf = EachDay_pf.dropna(subset=['MA10'])

#对离散变量做独热编码处理
one_hot = pd.get_dummies(EachDay_pf["dayofweek"][:])
one_hot.columns = ["isMonday","isTuesday","isWednesday","isThursday","isFriday","isSaturday","isSunday"]
EachDay_pf = EachDay_pf.join(one_hot)
one_hot = pd.get_dummies(EachDay_pf["date_type"][:])
one_hot.columns = ["isWorkday","isWeekend","isHoliday"]
EachDay_pf = EachDay_pf.join(one_hot)

#将data和target分开
X = EachDay_pf.drop(columns=["date","pf","dayofweek","date_type"])
y = EachDay_pf['pf']

#划分训练与测试数据集
X_length = X.shape[0]
split = int(X_length*0.9)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

#进行归一化
from sklearn.preprocessing import StandardScaler
standscaler = StandardScaler()
standscaler.fit(X_train,y_train)
X_train_stand = standscaler.transform(X_train)
X_test_stand = standscaler.transform(X_test)

#定义一个简单的线性回归,到时候会改模型，肯定不会用线回的
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
linreg = LinearRegression()
linreg.fit(X_train_stand,y_train)

#获取结果并与测试数据集进行比较
y_predict = linreg.predict(X_test_stand)
print(r2_score(y_test,y_predict))