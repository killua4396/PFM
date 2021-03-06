from database import app

@app.route("/predict/predict_month_info")
def predict_month_info():
    import numpy as np
    import pandas as pd
    import xgboost as xgb
    import datetime
    from flask import jsonify
    from database import model_parameter
    parameter = model_parameter.query.filter(model_parameter.model == 'predict_day')
    other_params = {}
    for i in parameter:
        if i.parameter == "n_estimators" or i.parameter == "max_depth" or i.parameter == "min_child_weight" \
                or i.parameter == "seed" or i.parameter == "reg_lambda":
            temp = {i.parameter: int(i.value)}
        else:
            temp = {i.parameter: float(i.value)}
        other_params.update(temp)

    # 用于提取时间戳中的日期
    def To_day(x):
        return x.date()

    # 转化成星期
    def ToDayofWeek(x):
        return x.dayofweek

    # 将时间字符串转化为时间戳
    def Totimestamp(x):
        return pd.to_datetime(x)

    # 将日期转化为日期类型
    def Day_to_DateType(x):
        return transform[x.dayofyear]

    # 获取昨日信息
    def get_Yesterday_info(df):
        return df.loc[df.shape[0] - 1]

    # 获取今日信息
    def get_Today(df):
        yesterday_info = get_Yesterday_info(df)
        timestamp = yesterday_info.date
        return timestamp + datetime.timedelta(days=1)

    # 获取昨日客流
    def get_pre_date_flow(df):
        return get_Yesterday_info(df)[1]

    # 获取MA5数据
    def get_MA5(df):
        y5_info = df.loc[df.shape[0] - 5:df.shape[0] - 2]
        y5_info = y5_info.reset_index(drop=True)
        y5_info = y5_info["pf"]
        sum = 0
        for i in range(4):
            sum = sum + y5_info[i]
        return sum / 4

    # 获取MA10数据
    def get_MA10(df):
        y10_info = df.loc[df.shape[0] - 10:df.shape[0] - 2]
        y10_info = y10_info.reset_index(drop=True)
        y10_info = y10_info["pf"]
        sum = 0
        for i in range(9):
            sum = sum + y10_info[i]
        return sum / 9

    # 获取星期信息
    def get_isMonday(df):
        today = get_Today(df)
        return int(today.dayofweek == 0)

    def get_isTuesday(df):
        today = get_Today(df)
        return int(today.dayofweek == 1)

    def get_isWednesday(df):
        today = get_Today(df)
        return int(today.dayofweek == 2)

    def get_isThursday(df):
        today = get_Today(df)
        return int(today.dayofweek == 3)

    def get_isFriday(df):
        today = get_Today(df)
        return int(today.dayofweek == 4)

    def get_isSaturday(df):
        today = get_Today(df)
        return int(today.dayofweek == 5)

    def get_isSunday(df):
        today = get_Today(df)
        return int(today.dayofweek == 6)

    # 获取日期类型信息
    def get_isWorkday(df):
        today = get_Today(df)
        today_type = int(transform[today.dayofyear])
        if (today_type == 1):
            return 1
        else:
            return 0

    def get_isWeekend(df):
        today = get_Today(df)
        today_type = int(transform[today.dayofyear])
        if (today_type == 2):
            return 1
        else:
            return 0

    def get_isHoliday(df):
        today = get_Today(df)
        today_type = int(transform[today.dayofyear])
        if (today_type == 2):
            return 1
        else:
            return 0

    # 获取今日的dataframe(一行)
    def get_today_df(df, arr, pf):
        return [get_Today(df), pf, get_dayofweek(arr), get_dateT(arr), get_pre_date_flow(df), get_MA5(df), get_MA10(df),
                get_isMonday(df),
                get_isTuesday(df), get_isWednesday(df), get_isThursday(df), get_isFriday(df),
                get_isSaturday(df), get_isSunday(df), get_isWorkday(df), get_isWeekend(df), get_isHoliday(df)]

    # 获取星期信息
    def get_dayofweek(arr):
        if arr[:, 3] == 1:
            return 0
        if arr[:, 4] == 1:
            return 1
        if arr[:, 5] == 1:
            return 2
        if arr[:, 6] == 1:
            return 3
        if arr[:, 7] == 1:
            return 4
        if arr[:, 8] == 1:
            return 5
        if arr[:, 9] == 1:
            return 6
        else:
            return -1

    # 获取日期类型
    def get_dateT(arr):
        if arr[:, 10] == 1:
            return 1
        if arr[:, 11] == 1:
            return 2
        if arr[:, 12] == 1:
            return 2

    # 获取今日信息
    def get_today_info(df):
        return [get_pre_date_flow(df), get_MA5(df), get_MA10(df), get_isMonday(df),
                get_isTuesday(df), get_isWednesday(df), get_isThursday(df), get_isFriday(df),
                get_isSaturday(df), get_isSunday(df), get_isWorkday(df), get_isWeekend(df), get_isHoliday(df)]

    # 获取今日的dataframew(完整)
    def get_today_df_cp(df, standscaler, model, today_info):
        # 进行标准化
        today_info = np.array([today_info])
        today_info_stand = standscaler.transform(today_info)
        # 预测今日的客流
        today_pf = round(model.predict(today_info_stand)[0])
        # 获取今日的dataframe(一行)
        today_df = get_today_df(df, today_info, today_pf)
        # 转化为np.array类型
        today_df = np.array([today_df])
        # 将今日信息写入字典
        today = {}
        for i in range(17):
            today.update({df.columns[i]: today_df[0, i]})
        return df.append(today, ignore_index=True)

    # 获取未来几日的信息dataframe
    def get_few_day(day, df, standscaler, model, today_info):
        for i in range(day):
            df = get_today_df_cp(df, standscaler, model, today_info)
            today_info = get_today_info(df)
        return df

    from dateutil.relativedelta import relativedelta
    # 获取需要预测的步长
    def get_days_need_predict(df):
        nowday = df.loc[df.shape[0] - 1, 'date']
        T_days_in_month = nowday.days_in_month
        temp1 = T_days_in_month - nowday.day
        temp2 = (nowday + relativedelta(month=nowday.month + 1)).days_in_month
        return (temp1 + temp2), nowday.days_in_month, temp2

    # 获取结果
    def get_Nmonth_pf(df, d1, d2):
        Nm_pf = 0
        for i in df.loc[df.shape[0] - d2:df.shape[0] - 1]['pf'].to_list():
            Nm_pf += i
        return Nm_pf

    def get_Tmonth_pf(df, d1, d2):
        Tm_pf = 0
        for i in df.loc[df.shape[0] - d2 - d1:df.shape[0] - d2 - 1]['pf'].to_list():
            Tm_pf += i
        return Tm_pf

    # 获取数据库数据
    from database import trips
    from database import workdays2020
    from database import db
    data1 = db.session.query(trips).all()
    trips = pd.DataFrame([(d.id, d.User_id, d.In_station_name, d.In_station_time, d.Out_station_name,
                           d.Out_station_time, d.Channel_number, d.Price) for d in data1],
                         columns=["id", "User_id", "In_station_name", "In_station_time",
                                  "Out_station_name", "Out_station_time", "Channel_number", "Price"])
    data2 = db.session.query(workdays2020).all()
    workdays = pd.DataFrame([(d.Date, d.Date_type, d.Dayofyear) for d in data2],
                            columns=["Date", "Date_type", "Dayofyear"])
    del trips["id"]

    # 将进站时间字符串转化成进站时间时间戳
    trips['in_timestamp'] = trips['In_station_time'].apply(lambda x: pd.to_datetime(x))

    # 添加一列日期数据
    trips["date"] = trips["in_timestamp"].apply(To_day)

    # 将每日的客流统计出来存入到dataframe中
    EachDay_pf = pd.DataFrame(trips["date"].value_counts())
    EachDay_pf["pf"] = EachDay_pf["date"]
    EachDay_pf["date"] = EachDay_pf.index

    # 将原来的时间字符串数据转化为时间戳数据
    EachDay_pf["date"] = EachDay_pf["date"].apply(Totimestamp)

    # 根据时间顺序排序
    EachDay_pf = EachDay_pf.sort_values(by="date")

    # 重置index列
    EachDay_pf = EachDay_pf.reset_index(drop=True)

    # 添加一列Week特征
    EachDay_pf["dayofweek"] = EachDay_pf["date"].apply(ToDayofWeek)

    # 定义一个日期类型转化字典
    transform = {}
    for i in range(366):
        temp = {workdays.loc[i, "Dayofyear"]: workdays.loc[i, "Date_type"]}
        transform.update(temp)

    # 添加一列日期类型特征
    EachDay_pf["date_type"] = EachDay_pf["date"].apply(Day_to_DateType)

    # 添加三列特征，分别是前一日客流量，前五日平均客流量，前十日平均客流量
    EachDay_pf['pre_date_flow'] = EachDay_pf.loc[:, ['pf']].shift(1)
    EachDay_pf['MA5'] = EachDay_pf['pf'].rolling(5).mean()
    EachDay_pf['MA10'] = EachDay_pf['pf'].rolling(10).mean()

    # 去掉非2020年的数据行（开头几日的数据过少，明显不正常）
    for index, row in EachDay_pf.iterrows():
        if row.date.year != 2020:
            EachDay_pf = EachDay_pf.drop(index=index)
        if row.date.year == 2020:
            break

    # 去除空值
    EachDay_pf = EachDay_pf.dropna(subset=['MA10'])
    EachDay_pf = EachDay_pf.reset_index(drop=True)

    # 对离散变量做独热编码处理
    one_hot = pd.get_dummies(EachDay_pf["dayofweek"][:])
    one_hot.columns = ["isMonday", "isTuesday", "isWednesday", "isThursday", "isFriday", "isSaturday", "isSunday"]
    EachDay_pf = EachDay_pf.join(one_hot)
    one_hot = pd.get_dummies(EachDay_pf["date_type"][:])
    one_hot.columns = ["isWorkday", "isWeekend", "isHoliday"]
    EachDay_pf = EachDay_pf.join(one_hot)

    # 将data和target分开
    X = EachDay_pf.drop(columns=["date", "pf", "dayofweek", "date_type"])
    y = EachDay_pf['pf']

    # 划分训练与测试数据集
    X_length = X.shape[0]
    split = int(X_length * 0.9)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # 进行归一化
    from sklearn.preprocessing import StandardScaler
    standscaler = StandardScaler()
    standscaler.fit(X_train, y_train)
    X_train_stand = standscaler.transform(X_train)
    X_test_stand = standscaler.transform(X_test)

    # 进行模型训练
    model = xgb.XGBRegressor(**other_params)
    model.fit(X_train_stand, y_train)

    # 获取需要预测的步长并进行预测
    days_need_predict, d1, d2 = get_days_need_predict(EachDay_pf)
    EachDay_pf = get_few_day(days_need_predict, EachDay_pf, standscaler, model, get_today_info(EachDay_pf))

    Nm_pf = get_Nmonth_pf(EachDay_pf, d1, d2)
    Tm_pf = get_Tmonth_pf(EachDay_pf, d1, d2)

    # 写入数据库
    from database import predict_monthinfo
    db.session.query(predict_monthinfo).delete()
    db.session.commit()
    predict_M1 = predict_monthinfo(Month="This_M", Month_PassengerFlow=Tm_pf)
    predict_M2 = predict_monthinfo(Month="Next_M", Month_PassengerFlow=Nm_pf)
    db.session.add_all([predict_M1, predict_M2])
    db.session.commit()

    return jsonify(msg="月客流预测数据更新成功！")


if __name__ == '__main__':
    app.run()