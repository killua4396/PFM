from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config

app = Flask(__name__)
app.secret_key = "S11"
app.config.from_object(config)
db = SQLAlchemy(app)

#站点信息
class station(db.Model):
    __tablename__ = "station"
    Number = db.Column(db.String(5),nullable=False,primary_key=True)
    Station_name = db.Column(db.String(10),nullable=False)
    Line = db.Column(db.String(5),nullable=False)
    Administrative_divisions = db.Column(db.String(10),nullable=False)
    def __init__(self,Number=None,Station_name=None,Line=None,Administrative_divisions=None):
        self.data = (Number,Station_name,Line,Administrative_divisions)

#模型参数信息
class model_parameter(db.Model):
    __tablename__ = "model_parameter"
    id = db.Column(db.Integer,primary_key=True)
    model  = db.Column(db.String(50),nullable=False)
    parameter = db.Column(db.String(50),nullable=False)
    value = db.Column(db.DECIMAL(15),nullable=False)
    def __init__(self,id=None,model=None,parameter=None,value=None):
        self.data(id,model,parameter,value)

#预测月客流信息
class predict_monthinfo(db.Model):
    __tablename__ = "predict_monthinfo"
    Month = db.Column(db.String(10),primary_key=True)
    Month_PassengerFlow = db.Column(db.Integer)
    # def __init__(self,Month=None,Month_PassengerFlow=None):
    #     self.data(Month,Month_PassengerFlow)

#预测明日客流信息
class predict_nextday_info(db.Model):
    __tablename__ = "predict_nextday_info"
    id = db.Column(db.Integer,primary_key=True)
    Station_name = db.Column(db.String(10))
    Timeslot = db.Column(db.String(50),nullable=False)
    InNums = db.Column(db.Integer)
    OutNums = db.Column(db.Integer)
    def __init__(self,id=None,Station_name=None,Timeslot=None,InNums=None,OutNums=None):
        self.data(id,Station_name,Timeslot,InNums,OutNums)
    def __init__(self,Station_name,Timeslot,InNums,OutNums):
        self.Station_name = Station_name
        self.Timeslot = Timeslot
        self.InNums = InNums
        self.OutNums = OutNums

#预测OD信息
class predict_OD_info(db.Model):
    __tablename__ = "predict_OD_info"
    id = db.Column(db.Integer,primary_key=True)
    Timeslot = db.Column(db.String(50),nullable=False)
    Starting_station = db.Column(db.String(10),nullable=False)
    Ending_station = db.Column(db.String(10),nullable=False)
    OD_pf =db.Column(db.Integer)
    def __init__(self,id=None,Timeslot=None,Starting_station=None,Ending_station=None,OD_pf=None):
        self.data(id,Timeslot,Starting_station,Ending_station,OD_pf)
    def __init__(self,Timeslot,Starting_station,Ending_station,OD_pf):
        self.Timeslot = Timeslot
        self.Starting_station = Starting_station
        self.Ending_station = Ending_station
        self.OD_pf = OD_pf

#预测早晚高峰客流信息
class predict_rushhour_info(db.Model):
    __tablename__ = "predict_rushhour_info"
    id = db.Column(db.Integer,primary_key = True)
    Next_weekday = db.Column(db.String(30),nullable=False)
    Station_name = db.Column(db.String(10),nullable=False)
    Morning_rushhour_pf = db.Column(db.Integer)
    Evening_rushhour_pf = db.Column(db.Integer)
    # def __init__(self,id=None,Next_weekday=None,Station_name=None,Morning_rushhour_pf=None,Evening_rushhour_pf=None):
    #     self.data(id,Next_weekday,Station_name,Morning_rushhour_pf,Evening_rushhour_pf)

#预测单站点客流信息
class predict_singlestation_info(db.Model):
    __tablename__ = "predict_singlestation_info"
    id = db.Column(db.Integer,primary_key=True)
    Station_name = db.Column(db.String(10),nullable=False)
    halfhour_in_pf = db.Column(db.Integer)
    halfhour_out_pf = db.Column(db.Integer)
    anhour_in_pf = db.Column(db.Integer)
    anhour_out_pf = db.Column(db.Integer)
    aday_in_pf = db.Column(db.Integer)
    aday_out_pf = db.Column(db.Integer)
    def __init__(self,id=None,Station_name=None,halfhour_in_pf=None,halfhour_out_pf=None,anhour_in_pf=None,anhour_out_pf=None,aday_in_pf=None,aday_out_pf=None):
        self.data(id,Station_name,halfhour_in_pf,halfhour_out_pf,anhour_in_pf,anhour_out_pf,aday_in_pf,aday_out_pf)

#预测一周信息
class predict_weekinfo(db.Model):
    __tablename__ = "predict_weekinfo"
    Week = db.Column(db.String(10),primary_key=True)
    Weekday_PassengerFlow = db.Column(db.Integer)
    Weekend_PassengerFlow = db.Column(db.Integer)
    # def __init__(self,Week=None,Weekday_PassengerFlow=None,Weekend_PassengerFlow=None):
    #     self.data(Week,Weekday_PassengerFlow,Weekend_PassengerFlow)


#系统用户信息
class system_users(db.Model):
    __tablename__ = "system_users"
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(10),nullable=False)
    password_hash = db.Column(db.String(15),nullable=False)
    def __init__(self,id=None,username=None,password_hash=None):
        self.data(id,username,password_hash)

#行程数据
class trips(db.Model):
    __tablename__ = "trips"
    id = db.Column(db.Integer,primary_key=True)
    User_id = db.Column(db.String(255),nullable=False)
    In_station_name = db.Column(db.String(10),nullable=False)
    In_station_time = db.Column(db.String(30),nullable=False)
    Out_station_name = db.Column(db.String(10),nullable=False)
    Out_station_time = db.Column(db.String(30),nullable=False)
    Channel_number = db.Column(db.String(5),nullable=False)
    Price = db.Column(db.Integer,nullable=False)
    def __init__(self,id=None,User_id=None,In_station_name=None,In_station_time=None,Out_station_name=None,Out_station_time=None,Channel_number=None,Price=None):
        self.data(id,User_id,In_station_name,In_station_time,Out_station_name,Out_station_time,Channel_number,Price)

#地铁乘客信息
class users(db.Model):
    __tablename__ = "users"
    User_id = db.Column(db.String(255),primary_key=True)
    Region = db.Column(db.String(10),nullable=False)
    Birthday = db.Column(db.String(5),nullable=False)
    Gender = db.Column(db.String(2),nullable=False)
    def __init__(self,User_id=None,Region=None,Birthday=None,Gender=None):
        self.data(User_id,Region,Birthday,Gender)

#2020日期信息
class workdays2020(db.Model):
    __tablename__ = "workdays2020"
    Date = db.Column(db.String(10),primary_key=True)
    Date_type = db.Column(db.String(2),nullable=False)
    Dayofyear = db.Column(db.Integer,nullable=False)
    def __init__(self,Date=None,Date_type=None,Dayofyear=None):
        self.data(Date,Date_type,Dayofyear)

if __name__ == '__main__':
    db.create_all()