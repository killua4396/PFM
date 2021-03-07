from database import app
from flask import session
import datetime
@app.route("/ControlSystem/init_Time")
def init_Time():
    now = datetime.datetime.now()
    now.
    session["SettingTime"] = [{"all":}]
    return "初始化成功"

@app.route("/ControlSystem/SetTime",methods=["POST","GET"])
def SetTime():
    from flask import jsonify
    from flask import request
    Time = request.get_json()
    project = Time.get("Project")
    SettingTime = Time.get("SettingTime")
    all_seeting = session.get("AllSettingTime")
    all_seeting.append({"project":project,"SettingTime":SettingTime})
    session["AllSettingTime"] = all_seeting
    print(session.get("AllSettingTime"))
    return jsonify(msg="时间设置成功！")




app.run()



# @app.route("/ControlSystem/Transaction_flow_bytime",methods=["GET"])
# def Transaction_flow_bytime():
#     import datetime
#     Time_now = datetime.datetime.now()
#     while True:
#         Time_now