from database import app
from flask import session
import datetime
from predict import predict_month_info
from predict import predict_OD_info
from predict import predict_rush_hour
from predict import predict_single_station
from predict import predict_week_info


@app.route("/ControlSystem/init_Time")
def init_Time():
    import pandas as pd
    format_pattern = '%Y-%m-%d %H:%M:%S'
    def changeT_orderby_halfhour(x):
        t = int(x[14:16])
        if t < 30 and t >= 0:
            t = "00"
        elif t >= 30 and t <= 59:
            t = "30"
        return (x[:14] + t + ":00")
    Now = pd.to_datetime(datetime.datetime.now())
    Now = changeT_orderby_halfhour(str(Now))
    Now = pd.to_datetime(Now)+datetime.timedelta(minutes=30)
    Now = datetime.datetime.strptime(str(Now),format_pattern)

    # 对设定时间进行初始化，即在明日0点0分进行所有模型的重新训练，并且更新单站点数据
    now = datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(days=1),'%Y-%m-%d %H:%M:%S')
    Time = datetime.datetime.strptime(now[:10]+" 00:00:00","%Y-%m-%d %H:%M:%S")
    temp = [{"project":"update_single","SettingTime":Now},{"project":"all","SettingTime":Time}]
    temp = sorted(temp, key=lambda x: x["SettingTime"])
    session["AllSettingTime"] = temp
    return "初始化成功"

@app.route("/ControlSystem/SetTime",methods=["POST","GET"])
#设顶模型训练时间
def SetTime():
    from flask import jsonify
    from flask import request
    import datetime
    Time = request.get_json()
    project = Time.get("project")
    format_pattern = '%Y-%m-%d %H:%M:%S'
    SettingTime = Time.get("SettingTime")
    SettingTime = datetime.datetime.strptime(SettingTime,format_pattern)
    all_setting = session.get("AllSettingTime")
    if all_setting == None:
        init_Time()
        all_setting = session.get("AllSettingTime")
    all_setting.append({"project":project,"SettingTime":SettingTime})
    output = []
    for i in all_setting:
        if i not in output:
            output.append(i)
    output = sorted(output,key=lambda x:x["SettingTime"])
    session["AllSettingTime"] = output
    print(session.get("AllSettingTime"))
    return jsonify(msg="时间设置成功！")


@app.route("/clear")
def clear():
    session.clear()
    return "清除成功!"


@app.route("/ControlSystem/Transaction_flow_bytime",methods=["GET"])
def Transaction_flow_bytime():
    import datetime
    import time
    while True:
        Time_now = datetime.datetime.now()
        all_setting = session.get("AllSettingTime")
        temp = all_setting[0]
        project = temp["project"]
        Time = temp["SettingTime"]
        if Time>Time_now:
            time.sleep(120)
        else:
            if project == "predict_month_info":
                predict_month_info.predict_month_info()
            elif project == "predict_OD_info":
                predict_OD_info.predict_OD_info()
            elif project == "predict_rush_hour":
                predict_rush_hour.predict_rushhour_info()
            elif project == "predict_single_station":
                predict_single_station.predict_single_station()
            elif project == "predict_week_info":
                predict_week_info.predict_week_info()
            elif project == "all":
                predict_month_info.predict_month_info()
                predict_week_info.predict_week_info()
                predict_single_station.predict_single_station()
                predict_rush_hour.predict_rushhour_info()
                predict_OD_info.predict_OD_info()
                init_Time()
                continue
            elif project == "update_single":
                predict_single_station.update()
                Time = Time + datetime.timedelta(minutes=30)
                temp = [{"project":"update","SettingTime":Time}]
                all_setting = temp + all_setting[1:]
                all_setting = sorted(all_setting, key=lambda x: x["SettingTime"])
                session["AllSettingTime"] = all_setting
                continue

            all_setting = all_setting[1:]
            session["AllSettingTime"] = all_setting
    return "WrongsHappen"


if __name__ == "__main__":
    app.run()