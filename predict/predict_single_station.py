from database import app
@app.route("/predict/predict_single_station")
def predict_single_station():
    from database import model_parameter
    parameter = model_parameter.query.filter(model_parameter.model == 'predict_singlestation')
    other_params = {}
    for i in parameter:
        if i.parameter == "n_estimators" or i.parameter == "max_depth" or i.parameter == "min_child_weight" \
                or i.parameter == "seed" or i.parameter == "reg_lambda":
            temp = {i.parameter: int(i.value)}
        else:
            temp = {i.parameter: float(i.value)}
        other_params.update(temp)

    import pandas as pd
    import numpy as np
    from database import db
    from database import trips
    from database import workdays2020
    from database import station
    data1 = db.session.query(trips).all()
    trips = pd.DataFrame([(d.id, d.User_id, d.In_station_name, d.In_station_time, d.Out_station_name,
                           d.Out_station_time, d.Channel_number, d.Price) for d in data1],
                         columns=["id", "User_id", "In_station_name", "In_station_time",
                                  "Out_station_name", "Out_station_time", "Channel_number", "Price"])

    data2 = db.session.query(workdays2020).all()
    workdays = pd.DataFrame([(d.Date, d.Date_type, d.Dayofyear) for d in data2],
                            columns=["Date", "Date_type", "Dayofyear"])

    data4 = db.session.query(station).all()
    station = pd.DataFrame([(d.Number, d.Station_name, d.Line, d.Administrative_divisions) for d in data4],
                           columns=["Number", "Station_name", "Line", "Administrative_divisions"])

    del trips["id"]
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
    temp1["Time_slot"] = temp1["Time_slot"].apply(lambda x:pd.to_datetime(x))
    temp1 = temp1.sort_values(by="Time_slot")
    temp1 = temp1.reset_index(drop=True)
    Earliest_Time = temp1.loc[0]["Time_slot"]
    temp1 = pd.DataFrame(temp1.value_counts())

    #将时间段出站客流进行统计
    temp2 = pd.DataFrame()
    temp2[["Station_name","Time_slot"]] = trips[["Out_station_name","out_time_slot"]]
    temp2["Time_slot"] = temp2["Time_slot"].apply(lambda x:pd.to_datetime(x))
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
            Time = Time + datetime.timedelta(minutes=30)
            value.append(0)
            index1.append(S_name)
            index2.append(Time)

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
    y_in = data_in_shfit[["Station_name","InNums"]]
    y_out = data_in_shfit[["Station_name","OutNums"]]

    #将训练数据与预测数据分离
    def info_predict_split(df):
        df = df.reset_index(drop = True)
        return df.loc[:df.shape[0]-49],df.loc[df.shape[0]-48:]


    train_X = pd.DataFrame()
    train_y_in = pd.DataFrame()
    train_y_out = pd.DataFrame()
    predict_X = pd.DataFrame()

    for i in station["Station_name"]:
        data_temp_X = X[X["Station_name"] == i]
        data_temp_y_in = y_in[y_in["Station_name"] == i]
        data_temp_y_out = y_out[y_out["Station_name"] == i]

        train_X_temp, predict_X_temp = info_predict_split(data_temp_X)
        train_y_in_temp, predict_y_in = info_predict_split(data_temp_y_in)
        train_y_out_temp, predicty_y_out = info_predict_split(data_temp_y_out)

        train_X = pd.concat([train_X, train_X_temp], axis=0, ignore_index=True)
        predict_X = pd.concat([predict_X, predict_X_temp], axis=0, ignore_index=True)
        train_y_in = pd.concat([train_y_in, train_y_in_temp], axis=0, ignore_index=True)
        train_y_out = pd.concat([train_y_out, train_y_out_temp], axis=0, ignore_index=True)

    X = train_X
    y_in = train_y_in
    y_out = train_y_out
    del y_in['Station_name']
    del y_out['Station_name']

    import xgboost as xgb
    from sklearn.preprocessing import StandardScaler

    #处理输入X数据
    def delwith_X(df):
        StdScaler = StandardScaler()
        #将需要标准化与不需要标准化的数据分开
        wait = df[["Station_name", "Dayofweek", "Day", "hour", "min", "date_type"]]
        wait["Station_name"] = wait["Station_name"].apply(lambda x: x[3:])
        wait = np.array(wait)
        temp = df.drop(columns=["Station_name", "Dayofweek", "Day", "hour", "min", "date_type"])
        StdScaler.fit(temp)
        temp = StdScaler.transform(temp)
        df = np.hstack((wait, temp))
        return df

    X = delwith_X(X)
    predict_X = delwith_X(predict_X)

    #train_test_split
    len_X = X.shape[0]
    X_train = X[:int(len_X*0.7)]
    X_test = X[int(len_X*0.7):int(len_X*0.95)]
    y_train = y_in[:int(len_X*0.7)]
    y_test = y_in[int(len_X*0.7):int(len_X*0.95)]

    #进行模型训练，有两个模型，分别是进和出
    #训练进模型
    model_in = xgb.XGBRegressor(**other_params)
    model_in.fit(X_train,y_train)

    #改变y_train和y_test
    y_train = y_out[:int(len_X*0.7)]
    y_test = y_out[int(len_X*0.7):int(len_X*0.95)]
    #训练出模型
    model_out = xgb.XGBRegressor(**other_params)
    model_out.fit(X_train,y_train)

    #进行预测
    future_y_in  = model_in.predict(predict_X)
    future_y_out = model_out.predict(predict_X)

    #对结果进行处理
    result_in = np.abs(np.round(future_y_in))
    result_out = np.abs(np.round(future_y_out))
    result_in = result_in.astype(np.int32)
    result_out = result_out.astype(np.int32)

    #获取站点名称
    sta = predict_X[:,0]
    sta = "Sta" + sta

    #获取时间节点
    Timeslot = []
    Time = EndTime
    while Time != EndTime + datetime.timedelta(days=1):
        Time = Time + datetime.timedelta(minutes=30)
        Timeslot.append(str(Time))

    Timeslot = (Timeslot * 163)

    #组成最终结果
    result = np.stack([sta,Timeslot,result_in,result_out],axis=1)

    #将数据输入到数据库
    from database import predict_nextday_info
    db.session.query(predict_nextday_info).delete()
    db.session.commit()
    all = []
    for i in result:
        sta = i[0]
        time = i[1]
        innums = i[2]
        outnums = i[3]
        temp = predict_nextday_info(Station_name=sta,Timeslot=time,InNums=innums,OutNums=outnums)
        all.append(temp)
    db.session.add_all(all)
    db.session.commit()
    from flask import jsonify
    return jsonify(msg = "明日预测数据更新成功")


@app.route("/predict/predict_single_station/update")
def update():
    import datetime
    import pandas as pd
    from database import station
    from database import db
    from database import predict_nextday_info
    data3 = db.session.query(predict_nextday_info)


    nextday = pd.DataFrame([(d.id, d.Station_name, d.Timeslot, d.InNums, d.OutNums) for d in data3],
                           columns=["id", "Station_name", "Timeslot", "InNums", "OutNums"])



    now = datetime.datetime.now()
    now = pd.to_datetime(now)
    del nextday["id"]

    def changeT_orderby_halfhour(x):
        t = int(x[14:16])
        if t < 30 and t >= 0:
            t = "00"
        elif t >= 30 and t <= 59:
            t = "30"
        return (x[:14] + t + ":00")

    now = changeT_orderby_halfhour(str(now))

    halfhour = nextday[nextday["Timeslot"] == now]
    del halfhour["Timeslot"]

    #获取当前的时间计算出未来半小时，一小时，一天的客流量
    now = pd.to_datetime(now)
    now_add_half = now + datetime.timedelta(minutes=+30)
    anhour = nextday[(nextday["Timeslot"] == str(now)) | (nextday["Timeslot"] == str(now_add_half))]
    anhour = anhour[["Station_name", "InNums", "OutNums"]].groupby("Station_name").agg("sum")
    day = nextday[["Station_name", "InNums", "OutNums"]].groupby("Station_name").agg("sum")

    #提取结果
    halfhour = halfhour.set_index("Station_name")
    halfhour.columns = ["halfhour_in_pf", "halfhour_out_pf"]
    anhour.columns = ["anhour_in_pf", "anhour_out_pf"]
    day.columns = ["aday_in_pf", "aday_out_pf"]

    #将结果拼接起来
    result = pd.concat([halfhour,anhour,day],axis=1)
    result["Station_name"] = result.index
    result = result.reset_index(drop=True)

    from database import predict_singlestation_info
    db.session.query(predict_singlestation_info).delete()
    db.session.commit()
    all = []
    for row in result.iterrows():
        Station_name = row[1][6]
        halfhour_in_pf = row[1][0]
        halfhour_out_pf = row[1][1]
        anhour_in_pf = row[1][2]
        anhour_out_pf = row[1][3]
        aday_in_pf = row[1][4]
        aday_out_pf = row[1][5]
        temp = predict_singlestation_info(Station_name=Station_name,halfhour_in_pf=halfhour_in_pf,halfhour_out_pf=halfhour_out_pf,
                                          anhour_in_pf=anhour_in_pf,anhour_out_pf=anhour_out_pf,aday_in_pf=aday_in_pf,aday_out_pf=aday_out_pf)
        all.append(temp)
    db.session.add_all(all)
    db.session.commit()
    from flask import jsonify
    return jsonify(msg = "单站点预测数据更新成功")


