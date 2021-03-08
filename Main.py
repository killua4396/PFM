from database import app
from predict.predict_month_info import predict_month_info
from predict.predict_OD_info import predict_OD_info
from predict.predict_rush_hour import predict_rushhour_info
from predict.predict_single_station import predict_single_station
from predict.predict_week_info import predict_week_info
from ControlSystem import ChangeParameter
from ControlSystem import Transaction_flow_bytime

if __name__ == "__main__":
    app.run(host="0.0.0.0")