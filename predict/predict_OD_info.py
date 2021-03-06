from database import app

@app.route("/predict/predict_OD_info")
def predict_OD_info():
    import pandas as pd
    import numpy as np
    from database import trips
    from database import db
    from database import workdays2020
    from database import predict_nextday_info
    from database import station
    #数据库获取数据
    data1 = db.session.query(trips).all()
    trips = pd.DataFrame([(d.id, d.User_id, d.In_station_name, d.In_station_time, d.Out_station_name,
                           d.Out_station_time, d.Channel_number, d.Price) for d in data1],
                         columns=["id", "User_id", "In_station_name", "In_station_time",
                                  "Out_station_name", "Out_station_time", "Channel_number", "Price"])

    data2 = db.session.query(workdays2020).all()
    workdays = pd.DataFrame([(d.Date, d.Date_type, d.Dayofyear) for d in data2],
                            columns=["Date", "Date_type", "Dayofyear"])

    data3 = db.session.query(predict_nextday_info)
    nextday = pd.DataFrame([(d.id,d.Station_name,d.Timeslot,d.InNums,d.OutNums)for d in data3],
                           columns=["id","Station_name","Timeslot","InNums","OutNums"])

    data4 = db.session.query(station).all()
    station=pd.DataFrame([(d.Number,d.Station_name,d.Line,d.Administrative_divisions)for d in data4],
                         columns=["Number","Station_name","Line","Administrative_divisions"])
    #以小时排序
    def changeT_orderby_hour(x):
        return (x[:14] + "00" + ":00")

    del trips["id"]
    del nextday["id"]
    #删除一些不合法数据
    trips = trips[trips["In_station_name"]!=trips["Out_station_name"]]

    #修改trips
    trips["Timeslot"] = trips["In_station_time"].apply(changeT_orderby_hour)
    trips["In_station_time"] = trips["In_station_time"].apply(lambda x : pd.to_datetime(x))

    #制作transform字典
    station["Station_name_num"] = station["Station_name"].apply(lambda x : int(x[3:]))
    station = station.sort_values("Station_name_num")
    station.reset_index(drop = True,inplace=True)

    transfrom = {}
    for row in station.iterrows():
        x = {"Sta"+str(row[1][4]):row[0]}
        transfrom.update(x)

    del station["Station_name_num"]

    #获得OD矩阵
    def get_ODMatrix(StartTime,EndTime,trips,station,transfrom):
        trips = trips[(trips["In_station_time"]>StartTime)&(trips["In_station_time"]<EndTime)]
        num = station.shape[0]
        ODMatrix = np.zeros((163,163))
        for row in trips.iterrows():
            if row[1][1] not in transfrom.keys():
                continue
            if row[1][3] not in transfrom.keys():
                continue
            i = transfrom[row[1][1]]
            j = transfrom[row[1][3]]
            if i == j:
                continue
            ODMatrix[i][j] = ODMatrix[i][j] + 1
        return ODMatrix

    #获得OD概率
    def get_OD_probability(OD_Matrix):
        each_station = []
        for i in OD_Matrix:
            p = 0
            for j in i:
                p += j
            each_station.append(p)
        for i in range(OD_Matrix.shape[0]):
            if each_station[i] ==0:
                continue
            for j in range(OD_Matrix.shape[1]):
                OD_Matrix[i][j] = OD_Matrix[i][j]/each_station[i]
        return OD_Matrix

    #删除非2020年的数据
    trips = trips.sort_values("In_station_time")
    trips["year"] = trips["In_station_time"].apply(lambda x : x.year)
    trips=trips[trips["year"] == 2020]
    trips = trips.drop(columns=["year"])
    trips = trips.reset_index(drop = True)

    #确定起始和终止时间
    StartTime = trips["Timeslot"][0]
    EndTime = trips["Timeslot"][trips.shape[0]-1]
    StartTime = pd.to_datetime(StartTime[:11] + "00:00:00")
    EndTime = pd.to_datetime(EndTime[:11] + "00:00:00")

    #用于存放矩阵
    T1 = []  #6:00-7:00
    T2 = []  #7:00-9:00
    T3 = []  #9:00-12:00
    T4 = []  #12:00-17:00
    T5 = []  #17:00-19:00
    T6 = []  #19-00-24:00

    #用于存放时间点
    TimePoint1 = pd.to_datetime("2020-01-01 06:00:00")
    TimePoint2 = pd.to_datetime("2020-01-01 07:00:00")
    TimePoint3 = pd.to_datetime("2020-01-01 09:00:00")
    TimePoint4 = pd.to_datetime("2020-01-01 12:00:00")
    TimePoint5 = pd.to_datetime("2020-01-01 17:00:00")
    TimePoint6 = pd.to_datetime("2020-01-01 19:00:00")
    TimePoint7 = pd.to_datetime("2020-01-01 23:59:59")
    Time_day = [TimePoint1,TimePoint2,TimePoint3,TimePoint4,TimePoint5,TimePoint6,TimePoint7]

    import datetime

    #获取OD矩阵
    Time = StartTime
    while Time != EndTime:
        for j in range(6):
            temp = get_ODMatrix(Time_day[j],Time_day[j+1],trips,station,transfrom)
            if j == 0:
                T1.append([Time_day[0].dayofyear,temp])
            elif j == 1:
                T2.append([Time_day[0].dayofyear,temp])
            elif j == 2:
                T3.append([Time_day[0].dayofyear,temp])
            elif j == 3:
                T4.append([Time_day[0].dayofyear,temp])
            elif j == 4:
                T5.append([Time_day[0].dayofyear,temp])
            elif j == 5:
                T6.append([Time_day[0].dayofyear,temp])
        Time = Time + datetime.timedelta(days=1)
        for k in range(7):
            Time_day[k] = Time_day[k] + datetime.timedelta(days = 1)

    workdays["Date"] =workdays["Date"].apply(lambda x:pd.to_datetime(x))
    workdays =workdays.sort_values("Date")
    workdays = workdays.reset_index(drop=True)

    #用于存放三种日期的OD矩阵
    workD = []
    weekE = []
    holiD = []

    #转换日期类型字典
    transformDt = {}
    for i in range(366):
        temp = {workdays.loc[i, "Dayofyear"]: workdays.loc[i, "Date_type"]}
        transformDt.update(temp)

    #获取日期类型分类的矩阵
    all_T = [T1,T2,T3,T4,T5,T6]
    for i in range(len(T1)):
        date_type = transformDt[T1[i][0]]
        temp = []
        for j in all_T:
            temp.append(j[i])
        if date_type == '1':
            workD.append(temp)
        elif date_type == '2':
            weekE.append(temp)
        elif date_type == '3':
            holiD.append(temp)

    #删除矩阵中的日期类型
    def del_type(x):
        temp1 = []
        temp2 = []
        for i in x:
            for j in i:
                temp1.append(j[1])
            temp2.append(temp1)
            temp1 = []
        return temp2

    workD = del_type(workD)
    weekE = del_type(weekE)
    holiD = del_type(holiD)


    #转换成概率
    def to_probability(x):
        for i in range(len(x)):
            for j in range(6):
                x[i][j] = get_OD_probability(x[i][j])
        return x

    workD = to_probability(workD)
    weekE = to_probability(weekE)
    holiD = to_probability(holiD)

    #获取概率矩阵
    def get_probability(x):
        T1 = x[0][0]
        T2 = x[0][1]
        T3 = x[0][2]
        T4 = x[0][3]
        T5 = x[0][4]
        T6 = x[0][5]
        for i in range(1,len(x)):
            for j in range(6):
                if j == 0:
                    T1 = T1 + x[i][j]
                elif j == 1:
                    T2 = T2 + x[i][j]
                elif j == 2:
                    T3 = T3 + x[i][j]
                elif j == 3:
                    T4 = T4 + x[i][j]
                elif j == 4:
                    T5 = T5 + x[i][j]
                elif j == 5:
                    T6 = T6 + x[i][j]
        result = [T1,T2,T3,T4,T5,T6]
        return result

    workD = get_probability(workD)
    weekE = get_probability(weekE)
    holiD = get_probability(holiD)

    #归一化
    def normalize(x):
        for i in range(6):
            x[i] = x[i]/x[i].sum(axis=1)[:,None]
        return x

    workD = normalize(workD)
    weekE = normalize(weekE)
    holiD = normalize(holiD)

    #获取明日日期类型
    date_type = int(transformDt[pd.to_datetime(nextday["Timeslot"][0]).dayofyear])

    del nextday['OutNums']

    #将明日客流转换成各个时间段的客流
    def to_six_timeslot(x):
        if int(x[11:13]) == 6:
            return 0
        elif int(x[11:13]) == 7 or int(x[11:13]) == 8:
            return 1
        elif int(x[11:13]) == 9 or int(x[11:13]) == 10 or int(x[11:13]) == 11:
            return 2
        elif int(x[11:13]) == 12 or int(x[11:13]) == 13 or int(x[11:13]) == 14 or int(x[11:13]) ==15 or int(x[11:13]) == 16:
            return 3
        elif int(x[11:13]) == 17 or int(x[11:13]) ==18:
            return 4
        elif int(x[11:13]) == 19 or int(x[11:13]) == 20 or int(x[11:13]) == 21 or int(x[11:13]) ==22 or int(x[11:13]) ==23:
            return 5
        else:
            return "None"

    nextday["T_6"] = nextday["Timeslot"].apply(to_six_timeslot)
    nextday = nextday[nextday["T_6"] != "None"]
    nextday = nextday.reset_index(drop = True)
    del nextday["Timeslot"]

    #获取明日各个时间段的客流
    info = nextday.groupby(["T_6","Station_name"]).agg("sum")
    info["idx"] = info.index
    info = info.reset_index(drop = True)
    info["T_6"] = info["idx"].apply(lambda x: x[0])
    info["Station_name"] = info['idx'].apply(lambda x: x[1])
    del info['idx']
    info["Station_num"] = info["Station_name"].apply(lambda x:transfrom[x])
    del info["Station_name"]
    info = np.array(info)

    #定义一个取整函数
    import math
    def quzheng(x,yu):
        xiaoshu = math.modf(x)[0]
        zhengshu = math.modf(x)[1]
        if xiaoshu >= yu:
            return zhengshu +1
        else:
            return zhengshu

    import math
    #获取结果
    def get_result(Matrix,info):
        for i in info:
            Matrix[i[1]][i[2]] = Matrix[i[1]][i[2]] * i[0]
        for i in range(6):
            for j in range(163):
                for k in range(163):
                    if pd.isnull(workD[i][j][k]):
                        workD[i][j][k] = 0.
                    else:
                        workD[i][j][k] = quzheng(workD[i][j][k], 0.275)
        return Matrix

    result = np.array((163,163))
    if date_type == 1:
        result = get_result(workD,info)
    elif date_type == 2:
        result = get_result(weekE,info)
    elif date_type == 3:
        result == get_result(holiD,info)


    def get_Timeslot(i):
        if i == 0:
            return "before_morning_rush"
        elif i==1:
            return "morning_rush"
        elif i==2:
            return "after_morning_rush"
        elif i==3:
            return "before_evening_rush"
        elif i==4:
            return "evening_rush"
        elif i==5:
            return "after_evening_rush"

    #定义一个逆字典
    transfrom_inv = {value:key for key,value in transfrom.items()}

    #向数据库写入数据
    from database import predict_OD_info
    db.session.query(predict_OD_info).delete()
    db.session.commit()
    all = []
    for i in range(6):
        for j in range(163):
            for k in range(163):
                if result[i][j][k] != 0:
                    Timeslot = get_Timeslot(i)
                    Starting_station = transfrom_inv[j]
                    Ending_station = transfrom_inv[k]
                    OD_pf = result[i][j][k]
                    temp = predict_OD_info(Timeslot=Timeslot, Starting_station=Starting_station,
                                           Ending_station=Ending_station, OD_pf=OD_pf)
                    all.append(temp)
    db.session.add_all(all)
    db.session.commit()
    from flask import jsonify
    return jsonify(msg = "OD客流预测数据更新成功！")

if __name__ == "__main__":
    app.run()