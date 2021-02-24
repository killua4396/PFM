
from flask_login import login_user, logout_user, login_required
from flask import redirect, request, url_for, flash, render_template
from . import auth
from .forms import LoginForm
from ..models import User


@auth.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        curuser = User.query.filter_by(name=form.username.data).first()
        if curuser is not None and curuser.verify_password(form.password.data):
            login_user(curuser, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('user.dispalluser'))
        flash("用户名与密码不正确！")
    return render_template('login.html', form=LoginForm())


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已经退出系统！')
    return redirect(url_for('auth.login'))