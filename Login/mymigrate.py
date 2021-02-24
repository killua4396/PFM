from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_script import Shell
from flask_login import UserMixin
from dataclasses import dataclass


def selectAll():
    db.session.execute("SET @row_number = 0")
    query = db.session.query(User).order_by("id")
    row_number_column = "(@row_number := @row_number + 1) AS row_num"
    query = query.add_column(row_number_column)

    @dataclass
    class user_with_rownum:
        id: int
        name: str
        email: str
        passwd: str
        demo: str
        unit: str
        level: str
        row_num: int

    lst_result = []
    for ipp in query.all():
        tmpuser = user_with_rownum(0, ipp[0].name, ipp[0].email, ipp[0].passwd, ipp[0].demo, ipp[0].unit, ipp[0].level,
                                   ipp[1])
        lst_result.append(tmpuser)
    return lst_result


def make_shell_context():
    return dict(app=app, db=db, User=User)


app = Flask(__name__)
manager = Manager(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/abc?charset=utf8'
manager.add_command("shell", Shell(make_context=make_shell_context))

db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)


class User(UserMixin, db.Model):
    id          = db.Column(db.Integer, primary_key = True)
    name        = db.Column(db.String(100), unique=True)
    email       = db.Column(db.String(100))
    passwd_hash = db.Column(db.String(200))
    demo        = db.Column(db.String(100))
    unit        = db.Column(db.String(100))
    level       = db.Column(db.String(100))


class ModifyUserForm(Form):
    username    = StringField("用户名", [validators.Length(max=10,min=6,message="用户名长度必须大于%(min)d且小于%(max)d")])
    passwd      = RadioField('是否重置密码', choices=[ ('1', '是'), ('0', '否')], default='0', validators=[validators.DataRequired()])
    email       = StringField("邮箱", validators = [validators.Email(message='邮箱格式错误')])
    unit        = SelectField('单位', choices=unitChoice)
    level       = SelectField('等级', choices=levelChoice)
    demo        = TextField("备注")
    submit      = SubmitField("修改")


if __name__ == '__main__':
    manager.run()

manager.add_command('db', MigrateCommand)
