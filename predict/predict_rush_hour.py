from database import app


@app.route("/predict/predict_rushhour_info")
def predict_rushhour_info():
    from database import db
    import numpy as np
    import pandas as pd
    from database import predict_nextday_info
    from database import station
    data3 = db.session.query(predict_nextday_info)
    nextday = pd.DataFrame([(d.id, d.Station_name, d.Timeslot, d.InNums, d.OutNums) for d in data3],
                           columns=["id", "Station_name", "Timeslot", "InNums", "OutNums"])
    data4 = db.session.query(station).all()
    station = pd.DataFrame([(d.Number, d.Station_name, d.Line, d.Administrative_divisions) for d in data4],
                           columns=["Number", "Station_name", "Line", "Administrative_divisions"])

    del nextday["id"]

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
    from database import predict_rushhour_info
    db.session.query(predict_rushhour_info).delete()
    db.session.commit()
    all = []
    for row in rushhour_pf.iterrows():
        Day = "NextWeekDay1"
        Station_name = row[1][2]
        Morning_rushhour_pf = row[1][0]
        Evening_rushhour_pf = row[1][1]
        temp = predict_rushhour_info(Next_weekday=Day,Station_name=Station_name,Morning_rushhour_pf=Morning_rushhour_pf,
                                     Evening_rushhour_pf = Evening_rushhour_pf)
        all.append(temp)
    db.session.add_all(all)
    db.session.commit()
    from flask import jsonify
    return jsonify(msg = "早晚高峰预测数据更新成功")


