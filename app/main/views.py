import datetime
import os
import random
import requests

from flask_socketio import join_room, leave_room
from flask_babel import gettext as _

from sqlalchemy import null

import app
from flask import render_template, request, jsonify, url_for, session, redirect, views, abort, flash, make_response
from werkzeug.utils import secure_filename
from app.utils.redis_captcha import redis_get
from app.models import User, Products, Chat, Answer
from config import Config
from flask_mail import Message
from flask_babel import gettext as _, refresh

from . import main
from .. import db, mail, babel
from app.forms import CreateMIForm
from app.utils import random_captcha, redis_captcha
from werkzeug.security import generate_password_hash, check_password_hash

from ..utils.cache import Cache

myCache = Cache()


@main.route('/chat')
def chat():
    if session.get('TYPE') == 'user':
        if 'USERNAME' in session:
            username = session['USERNAME']
            room = session['USERNAME']
            message = Chat.query.filter_by(chatroom=username).all()
            message_product = 1
            product = Products.query.first()
            product_name = product.product_name
            product_price = product.product_price
            product_id = product.product_id
            product_img = url_for('static', filename='img/product/food-catigory-2.png')
            pros = {}
            for msg in message:
                if msg.message_type == 0:
                    pro_in_db = Products.query.filter(Products.product_id == msg.chat_message).first()
                    pros[pro_in_db.product_id] = pro_in_db
            answers = Answer.query.all()
            return render_template('chat.html', username=username, room=room, messages=message,
                                   message_prodect=message_product, product_name=product_name,
                                   product_price=product_price, product_id=product_id, product_img=product_img,
                                   pros=pros, answers=answers, path=session.get('path'))
        else:
            flash(_("you need login first"))
            return redirect(url_for('main.confirm_login'))
    flash(_("You are not a customer."))
    return redirect(url_for('customer.index'))


@main.route('/chat/id=<pro_id>')
def chat_product(pro_id):
    if session.get('TYPE') == 'user':
        if 'USERNAME' in session:
            username = session['USERNAME']
            room = session['USERNAME']
            message = Chat.query.filter_by(chatroom=username).all()
            message_product = 0
            product = Products.query.filter(Products.product_id == pro_id).first()
            product_name = product.product_name
            product_price = product.product_price
            product_id = url_for('customer.product_detail', pro_id=product.product_id)
            if product.product_imgs.first():
                product_img = url_for('static', filename='img/product/pic/{}'.format(product.product_imgs.first().img_path))
            else:
                product_img = url_for('static', filename='img/product/food-catigory-2.png')
            message_type = 0
            user = User.query.filter_by(username=username).first()
            user_id = user.id
            time = datetime.datetime.now()
            read = 0
            chatm = Chat(message_type=message_type, chat_message=product.product_id, chat_time=time, chatroom=room,
                         read=read, chatUser_id=user_id)
            db.session.add(chatm)
            db.session.commit()
            pros = {}
            for msg in message:
                if msg.message_type == 0:
                    pro_in_db = Products.query.filter(Products.product_id == msg.chat_message).first()
                    pros[pro_in_db.product_id] = pro_in_db
            answers = Answer.query.all()
            return render_template('chat.html', username=username, room=room, messages=message,
                                   message_product=message_product, product_name=product_name,
                                   product_price=product_price, product_id=product_id, product_img=product_img,
                                   pros=pros, answers=answers, path=session.get('path'))
        else:
            flash("you need login first")
            return redirect(url_for('main.confirm_login'))
    flash(_("You are not a customer."))
    return redirect(url_for('customer.index'))


# @app.route('/logout/')
# def logout():
#     if 'username' in session:
#         session.clear()
#     return redirect(url_for('index'))


@main.route('/api/getAnswer', methods=['POST'])
# ajax for getting answer
def getAnswer():
    q_id = request.form['question_id']
    print(q_id)
    question_id = q_id[6:]
    print(question_id)
    answer_in_db = Answer.query.filter(Answer.answer_id == question_id).first()
    print(answer_in_db)
    # if no product here
    if not answer_in_db:
        return jsonify(
            {'question': None, 'answer': None, 'questions_id': None, 'questions_question': None, 'returnValue': 1})
    else:
        length = Answer.query.count()
        qs = random.sample(range(1, length + 1), 3)
        questions_id = []
        questions_question = []
        for q in qs:
            a = Answer.query.filter(Answer.answer_id == q).first()
            if a:
                questions_id.append(a.answer_id)
                questions_question.append(a.question)
        return jsonify({'question': answer_in_db.question, 'answer': answer_in_db.answer, 'questions_id': questions_id,
                        'questions_question': questions_question, 'returnValue': 0})


@main.route('/api/getTranslate', methods=['POST'])
# ajax for getting translation
def getTranslate():
    original = request.form['original']
    print(original)
    original.strip(" ")

    url = 'http://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule'
    data = {'i': original,
            'from': 'AUTO',
            'to': 'AUTO',
            'smartresult': 'dict',
            'client': 'fanyideskweb',
            'doctype': 'json',
            'version': '2.1',
            'keyfrom': 'fanyi.web',
            'action': 'FY_BY_REALTIME',
            'typoResult': 'false'}
    # 将需要post的内容，以字典的形式记录在data内。
    r = requests.post(url, data=data)
    # post需要输入两个参数，一个url，一个是data，返回的是一个Response对象
    answer = r.json()
    result = ""
    print(answer['translateResult'])
    for an in answer['translateResult']:
        for item in an:
            result = result + " " + item['tgt']
    print(result)
    print('"' + original + '"的翻译结果：' + result + '\n')

    if not result:
        return jsonify(
            {'trans': None, 'returnValue': 1})
    else:
        return jsonify(
            {'trans': result, 'returnValue': 0})


# connect
@app.socketio.on('connect')
def handle_connect():
    username = session.get('USERNAME')
    # online_user.append(username)
    print('connect info:  ' + f'{username}  connect')
    # print(online_user)
    # socketio.emit('connect info', f'{username}  connect')


# disconnect
@app.socketio.on('disconnect')
def handle_disconnect():
    username = session.get('USERNAME')
    # username = session.get('username')
    print('connect info:  ' + f'{username}  disconnect')
    # socketio.emit('connect info', f'{username}  disconnect')



@app.socketio.on('send msg')
def handle_message(data):
    print('sendMsg' + str(data))
    # room = session.get('room')
    message_type = 1
    data['message'] = data.get('message').replace('<', '&lt;').replace('>', '&gt;')
    print(data)
    room = data.get('room')
    user = User.query.filter_by(username=data.get('user')).first()
    user_id = user.id
    time = datetime.datetime.now()
    if user.username == room:
        read = 0
    else:
        read = 1
    chatm = Chat(message_type=message_type, chat_message=data['message'], chat_time=time, chatroom=room, read=read,
                 chatUser_id=user_id)
    db.session.add(chatm)
    db.session.commit()
    app.socketio.emit('send msg', data, to=room)


@app.socketio.on('join')
def on_join(data):
    username = data.get('username')
    room = data.get('room')

    join_room(room)
    print('join room:  ' + str(data))
    # print(room_user)
    data['connect'] = username + _(' enters the room')
    app.socketio.emit('connect info', data, to=room)


@app.socketio.on('leave')
def on_leave(data):
    username = data.get('username')
    room = data.get('room')

    leave_room(room)
    print('leave room   ' + str(data))
    # print(room_user)
    data['connect'] = username + ' leaves the room'
    app.socketio.emit('connect info', data, to=room)


@main.context_processor
def context_processor():
    user = session.get("USERNAME")
    user_type = session.get("TYPE")
    if user:
        return {'current_user': user, 'current_type': user_type}
    # if logged in, return username and user type
    return {}
    # if not logged in return none


@main.route("/login", methods=['GET', 'POST'])
def confirm_login():
    if session.get('USERNAME') is None:
        title = _("Login/Register")
        name = request.form.get("name")
        password = request.form.get("password")
        classification = request.form.get("type")
        # if log in by username
        # print(name, password, classification)
        if name is not None:
            if int(classification) == 0:
                user_in_db = User.query.filter_by(username=name).first()
            # log in by email
            else:
                user_in_db = User.query.filter_by(email=name).first()
            if not user_in_db:
                # no such user return 1
                return jsonify({'returnValue': 1})
            print(user_in_db.username)

            if check_password_hash(user_in_db.password, password):
                session["USERNAME"] = user_in_db.username
                session["ID"] = user_in_db.id
                if user_in_db.authority == 0:
                    session["TYPE"] = "user"
                else:
                    session["TYPE"] = "manager"
                session.permanent = True
                # stay logged in
                flash(_("login successfully"))
                return jsonify({'returnValue': 0})
            else:
                return jsonify({'returnValue': 2})
        print(1)
        return render_template('user/login_register.html', login='1', title=title)
    else:
        flash(_("You have logged in"))
        return redirect(url_for('customer.index'))


@main.route('/logout', methods=['GET', 'POST'])
def logout():
    print("session clear")
    session.clear()
    if request.cookies.get('locale') == 'zh_Hans_CN':
        flash("成功登出")
    else:
        flash("logout successfully")
    return redirect(url_for('customer.index'))
    # clear the session and redirect to the home page


@main.route("/register", methods=['GET', 'POST'])
def register():
    info = request.values.to_dict()
    title = _("Register")
    # print(info)
    # check if got the information from client side
    if "username" in info.keys():
        # if got the information, preserve into the database
        print("have data")
        username = info.get("username")
        email = info.get("email")
        password_hash = generate_password_hash(info.get("password"))
        address = info.get("address")
        city = info.get("city")
        state = info.get("state")
        country = info.get("country")
        zip = info.get("zip")
        user = User(username=username, email=email, password=password_hash, address=address, city=city, state=state,
                    country=country, zip=zip, authority=0)
        db.session.add(user)
        db.session.commit()
        session["USERNAME"] = username
        session["TYPE"] = "user"
        return jsonify({'returnValue': 0})
    # if no information from the client side, just render the html file
    return render_template('user/login_register.html', login='0', title=title)


@main.route("/checkUsername", methods=['POST'])
def checkUsername():
    username = request.form.get("username")
    # check if got the username from client side
    if username != '':
        username_in_db = User.query.filter_by(username=username).first()
    else:
        return jsonify({'returnValue': 1})
    # check if this username is available or not
    if username_in_db is None:
        print("accept")
        return jsonify({'returnValue': 0})
    else:
        print("not accept")
        return jsonify({'returnValue': 1})


@main.route("/checkEmail", methods=['POST'])
def checkEmail():
    email = request.form.get("email")
    # check if got the email address from client side
    if email != '':
        email_in_db = User.query.filter_by(email=email).first()
    else:
        return jsonify({'returnValue': 1})
    # check if this email is available or not
    if email_in_db is None:
        print("accept")
        return jsonify({'returnValue': 0})
    else:
        print("not accept")
        return jsonify({'returnValue': 1})


@main.route("/send_email/")
def send_mail():
    message = Message('邮件发送', recipients=['1467797958@qq.com'], body='测试邮件发送')  # 主题：邮件发送;收件人：recipients;邮件内容：测试邮件发送
    mail.send(message)  # 发送邮件
    return "邮件已发送"


class RegisterEmail(views.MethodView):
    def get(self):
        return render_template('user/login_register.html', login='0')  # 返回到修改邮箱页面url

    def post(self):
        email = request.form.get("email")
        captcha = request.form.get("captcha")
        # redis_captcha = redis_get(email)
        store_captcha = myCache.get(email)
        if not store_captcha or captcha.lower() != store_captcha.lower():  # 不区分大小写
            return '邮箱验证码错误'
        return jsonify({'code': 200})


class EmailCaptcha(views.MethodView):
    def get(self):  # 根据resetemail.js中的ajax方法来写函数，不需要post请求
        email = request.args.get('email')  # 查询email参数是否存在
        if not email:
            return '请传递邮箱参数'

        # 发送邮件，内容为一个验证码：4、6位数字英文组合
        captcha = random_captcha.get_random_captcha(4)  # 生成4位验证码
        message = Message('very MusicShop email verification code', recipients=[email], body='Your code is：%s' % captcha)

        # 异常处理
        try:
            mail.send(message)
        except:
            return "服务器错误，邮件验证码未发送！"  # 发送异常，服务器错误
        myCache.set(email,captcha,300)
        # redis_captcha.redis_set(key=email, value=captcha)  # redis中都是键值对类型，存储验证码
        # 验证码保存，一般有时效性，且频繁请求变化，所以保存在Redis中
        return jsonify({'code': 200})


@main.route('/set_locale/<locale>')
# set the locale
def set_locale(locale):
    if locale:
        response = make_response(redirect(request.referrer))
        response.set_cookie('locale', locale, 60 * 60)
        refresh()
        if locale == 'en':
            locale = 'English'
            flash('Switch to English successfully!')
        else:
            locale = '中文'
            flash('成功切换至中文模式')

    return response


@babel.localeselector
def get_locale():
    cookie = request.cookies.get('locale')
    if cookie:
        return cookie
    else:
        return 'en'


main.add_url_rule("/registeremail/", view_func=RegisterEmail.as_view('registeremail'))
main.add_url_rule("/email_captcha/", view_func=EmailCaptcha.as_view('email_captcha'))
