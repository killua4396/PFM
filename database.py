from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)

class station(db.Model):
    __tablename__ = "station"
    Number = db.Column(db.String(5),nullable=False,primary_key=True)
    Station_name = db.Column(db.String(10),nullable=False)
    Line = db.Column(db.String(5),nullable=False)
    Administrative_divisions = db.Column(db.String(10),nullable=False)

class model_parameter(db.Model):
    __tablename__ = "model_parameter"
    id = db.Column(db.Integer,primary_key=True)
    model  = db.Column(db.String(50),nullable=False)
    parameter = db.Column(db.String(50),nullable=False)
    value = db.Column(db.DECIMAL(15),nullable=False)

class predict_monthinfo(db.Model):
    __tablename__ = "predict_monthinfo"
    Month = db.Column(db.String(10),primary_key=True)
    Month_PassengerFlow = db.Column(db.Integer)

class predict_nextday_info(db.Model):
    __tablename__ = "predict_nextday_info"
    id = db.Column(db.Integer,primary_key=True)
    Station_name = db.Column(db.String(10))
    Timeslot = db.Column(db.String(50),nullable=False)
    InNums = db.Column(db.Integer)
    OutNums = db.Column(db.Integer)

class predict_OD_info(db.Model):
    __tablename__ = "predict_OD_info"
    id = db.Column(db.Integer,primary_key=True)
    Timeslot = db.Column(db.String(50),nullable=False)
    Starting_station = db.Column(db.String(10),nullable=False)
    Ending_station = db.Column(db.String(10),nullable=False)
    OD_pf =db.Column(db.Integer)

class predict_rushhour_info(db.Model):
    __tablename__ = "predict_rushhour_info"
    id = db.Column(db.Integer,primary_key = True)
    Next_weekday = db.Column(db.String(30),nullable=False)
    Station_name = db.Column(db.String(10),nullable=False)
    Morning_rushhour_pf = db.Column(db.Integer)
    Evening_rushhour_pf = db.Column(db.Integer)

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

class predict_weekinfo(db.Model):
    __tablename__ = "predict_weekinfo"
    Week = db.Column(db.String(10),primary_key=True)
    Weekday_PassengerFlow = db.Column(db.Integer)
    Weekend_PassengerFlow = db.Column(db.Integer)

class system_users(db.Model):
    __tablename__ = "system_users"
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(10),nullable=False)
    password_hash = db.Column(db.String(15),nullable=False)

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

class users(db.Model):
    __tablename__ = "users"
    User_id = db.Column(db.String(255),primary_key=True)
    Region = db.Column(db.String(10),nullable=False)
    Birthday = db.Column(db.String(5),nullable=False)
    Gender = db.Column(db.String(2),nullable=False)

class workdays2020(db.Model):
    __tablename__ = "workdays2020"
    Date = db.Column(db.String(10),primary_key=True)
    Date_type = db.Column(db.String(2),nullable=False)
    Dayofyear = db.Column(db.Integer,nullable=False)

if __name__ == '__main__':
    db.create_all()