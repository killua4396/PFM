from database import db
from database import station
from flask_sqlalchemy import SQLAlchemy

sta = station.query.all()
for i in sta:
        print(i.Number,i.Station_name,i.Line,i.Administrative_divisions)