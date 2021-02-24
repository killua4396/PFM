from flask import render_template, request, redirect, url_for, flash, get_flashed_messages
from dataclasses import dataclass
from . import user
from .forms import *
from .. import db
from ..models import *
from ..auth_blueprint import login_required_with_level


@user.route('/dispalluser/')
@login_required_with_level([1,2,3,4])
def dispalluser():
    return render_template('dispalluser.html', users = selectAll())


@user.route('/newuser/', methods=['GET', 'POST'])
@login_required_with_level([1])
def newuser():
    if request.method =="POST":
        form = NewUserForm(formdata=request.form)
        if form.validate():
            curuser = User()
            curuser.name = request.form['username']
            curuser.email = request.form['email']
            curuser.passwd = 'hellowold'
            curuser.demo = request.form['demo']
            curuser.unit = request.form['unit']
            curuser.level = request.form['level']
            db.session.add(curuser)
            db.session.commit()
            flash('当前用户添加成功！')
            return redirect(url_for('.dispAllUser'))
        else:
            return render_template('newuser.html', form=form)
    return render_template('newuser.html', form=NewUserForm())


@user.route('/modifyuser/<userid>/', methods = ['GET', 'POST'])
@login_required_with_level([1])
def modifyuser(userid):
    form = ModifyUserForm()
    curuser = db.session.query(User).filter_by(id=userid).one()
    if request.method == 'POST':
        if form.validate():
            curuser.name = request.form['username']
            curuser.email = request.form['email']
            curuser.demo = request.form['demo']
            curuser.unit = request.form['unit']
            curuser.level = request.form['level']

            if request.form['passwd'] == '1':
                curuser.passwd = 'hellowold'
            db.session.commit()
            flash("用户修改完成！")
            return redirect(url_for('.dispAllUser'))
    return render_template('modifyuser.html', form=form)


@user.route('/deleteuser/<userid>', methods = ['GET', 'POST'])
@login_required_with_level([1])
def deleteuser(userid):
    db.session.query(User).filter_by(id=userid).delete()
    db.session.commit()
    return redirect(url_for('.dispAllUser'))














