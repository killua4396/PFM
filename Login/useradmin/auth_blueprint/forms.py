from flask_wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import validators


class LoginForm(Form):
    username    = StringField("用户名", [validators.Length(max=60,min=6,message="用户名长度必须大于%(min)d且小于%(max)d")])
    password    = PasswordField('密码', validators=[Required()])
    remember_me = BooleanField('记住我')
    submit      = SubmitField('登录')