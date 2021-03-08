from database import app



@app.route("/ControlSystem/ChangeParameter",methods=["POST","GET"])
def ChangeParameter():
    from flask import request
    from database import db
    from flask import jsonify
    info = request.get_json()
    id = info.get("id")
    value = info.get("value")
    from database import model_parameter
    model_P = model_parameter.query.filter(model_parameter.id == id).update({"value":value})
    db.session.commit()
    return jsonify("模型参数更新成功")


