import os
import random
import string
from statistics import mean

import cv2
from flask import render_template, abort, request, session, jsonify, views, abort, redirect, url_for, flash
from sqlalchemy import func
from flask_babel import gettext as _

import app
from config import Config
from app.utils.redis_captcha import redis_get
from flask import render_template, abort, request
from flask_mail import Message
from . import main
from app.models import Products, User, Category, Image, Shopping, OrderProduct, Order, Comment, State
from .search import search
from app.utils import random_captcha, redis_captcha, cache
from .. import db, mail
from werkzeug.security import generate_password_hash, check_password_hash

from ..utils.cache import Cache

myCache = Cache()


def check_user():
    if session.get("TYPE") == "user" or session.get("TYPE") == "manager":
        username = session.get("USERNAME")
        user = User.query.filter_by(username=username).first()
        photo_dir = Config.PROFILE_UPLOAD_DIR
        path = os.path.exists(os.path.join(photo_dir, '{}_profile.png'.format(username)))
        print(path)
        session['path'] = path
        return [user, path]
    else:
        return None


@main.app_template_filter('dt')
def change(dt):
    s = str(dt)
    return s[0:19]


@main.app_template_filter('dt_detail')
def change_in_detail(dt):
    result = '{} {} {}'.format(dt.day, dt.strftime('%B'), dt.year)
    return result


@main.app_template_filter('change_lan')
def change_lan(result):
    cookie = request.cookies.get('locale')
    print('cookie in profile {}'.format(cookie))
    if cookie == 'zh_Hans_CN':
        print('result {}'.format(result))
        if result == 'Canceled':
            result = '取消'
        elif result == 'Finished':
            result = '结束'
        elif result == 'Exception':
            result = '异常'
        elif result == 'Paid(delivery)':
            result = '已支付(寄送)'
        elif result == 'Paid(picking up)':
            result = '已支付(自提)'
        elif result == 'Delivery':
            result = '运送中'
    return result


@main.route('/')
# the page for welcome!
def index():
    if request.args.get('find'):
        return redirect(url_for('customer.shop_page', find = request.args.get('find')))
    title = _('Welcome')
    products = Products.query.limit(5)
    # check the state of user, whether a new user or logged in user
    result = check_user()
    if result is not None:
        return render_template('customer.html', title=title, user=result[0], path=result[1], products=products)
    return render_template('customer.html', title=title, products=products)


@main.route('/api/get_user', methods=['POST'])
# the page for welcome!
def get_user():
    # print(session.get("USERNAME"))
    # check the state of user, whether a new user or logged in user
    result = session.get("USERNAME")
    who = session.get("TYPE")
    if result is not None:
        return jsonify({'name': result, 'type': who})
    return jsonify({'name': "Tourist", 'type': "Tourist"})


@main.route('/shop_page')
# the page for shop page shown as box
def shop_page():
    title = _('Shop')
    # follow the last time of style since last time
    isPage = request.args.get('isPage', type=str, default='True')
    # get the request information
    pagination, per_page, name, category, price = search(request, Products, db)
    products = pagination.items
    # image should on shop_page
    # get user
    result = check_user()
    if result is not None:
        return render_template('shop_page.html', title=title, products=products
                               , pagination=pagination, endpoint='.shop_page'
                               , per_page=per_page, category=category
                               , name=name, user=result[0], path=result[1], isPage=isPage
                               , price=price)
    return render_template('shop_page.html', title=title, products=products
                           , pagination=pagination, endpoint='.shop_page'
                           , per_page=per_page, name=name, category=category, isPage=isPage
                           , price=price)


@main.route('/shop_page/region=<region>')
# the page for shop page shown as box
def shop_page_for_region(region):
    text = region
    if request.cookies.get('locale') == 'zh_Hans_CN':
        if region == 'Chinese':
            text = '民族乐器'
        else:
            text = '西洋乐器'
    else:
        text = ''
    title = _("%(region)s product", region=text)
    # follow the last time of style since last time
    isPage = request.args.get('isPage', type=str, default='True')
    # get the request information
    pagination, per_page, name, category, price = search(request, Products, db, region=region)
    products = pagination.items
    # get user
    result = check_user()
    if result is not None:
        return render_template('shop_page.html', title=title, products=products
                               , pagination=pagination, endpoint='.shop_page_for_region'
                               , per_page=per_page, name=name, user=result[0], path=result[1]
                               , category=category, region=region, isPage=isPage
                               , price=price)
    return render_template('shop_page.html', title=title, products=products
                           , pagination=pagination, endpoint='.shop_page_for_region'
                           , per_page=per_page, name=name
                           , region=region, category=category, isPage=isPage
                           , price=price)


@main.route('/api/get_language',methods=['POST'])
def get_language():
    if request.cookies.get('locale') == 'zh_Hans_CN':
        return jsonify({'lan': "ch"})
    else:
        return jsonify({'lan': "en"})


@main.route('/shop_page/category=<cate>')
# the page for shop page shown as box
def shop_page_for_category(cate):
    text = cate
    if request.cookies.get('locale') == 'zh_Hans_CN':
        text = Category.query.filter(Category.category_name == cate).first().category_chinese

    title = _("%(category)s product", category=text)
    # follow the last time of style since last time
    isPage = request.args.get('isPage', type=str, default='True')
    # get the request information
    pagination, per_page, name, category, price = search(request, Products, db, category=cate)
    products = pagination.items
    # get user
    result = check_user()
    if result is not None:
        return render_template('shop_page.html', title=title, products=products
                               , pagination=pagination, endpoint='.shop_page_for_category'
                               , per_page=per_page, name=name, user=result[0], path=result[1]
                               , category=category, cate=cate, isPage=isPage
                               , price=price)
    return render_template('shop_page.html', title=title, products=products
                           , pagination=pagination, endpoint='.shop_page_for_category'
                           , per_page=per_page, name=name
                           , cate=cate, category=category, isPage=isPage
                           , price=price)


@main.route('/get_photo', methods=['POST'])
def getPhoto():
    # get the file from formData
    result = request.files['img']
    # save with the name
    user = session.get("USERNAME")
    type = session.get("TYPE")
    if type == "user":
        photo_filename = user + '_profile.png'
    else:
        photo_filename = user + '_shopProfile.png'
    photo_dir = Config.PROFILE_UPLOAD_DIR
    result.save(os.path.join(photo_dir, photo_filename))

    im = cv2.imread(os.path.join(photo_dir, photo_filename))
    width = im.shape[0]
    height = im.shape[1]
    print(width)
    print(height)
    r = width / height
    if r > 1:
        w = height
        wcut = int((width - w) / 2)
        im = im[wcut:width - wcut, 0:height]
    elif r < 1:
        h = width
        hcut = int((height - h) / 2)
        im = im[0:width, hcut:height - hcut]
    cv2.imwrite(os.path.join(photo_dir, photo_filename), im)

    path = os.path.abspath(os.path.join(photo_dir, photo_filename))
    success = os.path.exists(path)
    if success:
        return jsonify({'returnValue': 0,
                        'name': user,
                        'type': type})
    else:
        return jsonify({'returnValue': 1})


@main.route('/updateAddress', methods=['POST'])
def updateAddress():
    state = request.form.get("state")
    city = request.form.get("city")
    address = request.form.get("address")
    zip_code = request.form.get("zip")
    phone = request.form.get("phone")
    username = session.get("USERNAME")
    user = User.query.filter_by(username=username).first()
    user.state = state
    user.city = city
    user.address = address
    user.zip = zip_code
    user.phone = phone
    db.session.commit()
    return jsonify({'returnValue': 1})


@main.route('/updatePayment', methods=['POST'])
def updatePayment():
    cardname = request.form.get("cardname")
    cardnumber = request.form.get("cardnumber")
    expiredate = request.form.get("expiredate")
    cvv = request.form.get("cvv")
    username = session.get("USERNAME")
    user = User.query.filter_by(username=username).first()
    db.session.commit()
    return jsonify({'returnValue': 1})


@main.route('/change_password', methods=['POST'])
def change_password():
    oldPassword = request.form.get("old")
    newPassword = request.form.get("new")
    username = session.get("USERNAME")
    user = User.query.filter_by(username=username).first()
    if check_password_hash(user.password, oldPassword):
        password_hash = generate_password_hash(newPassword)
        user.password = password_hash
        db.session.commit()
        return jsonify({'returnValue': 1})
    else:
        return jsonify({'returnValue': 0})


@main.route('/product_detail/id=<pro_id>')
# the page for the product details
def product_detail(pro_id):
    # get the related product
    product = Products.query.filter(Products.product_id == pro_id).first()
    text = product.product_name
    if request.cookies.get('locale') == 'zh_Hans_CN':
        text = product.name_chinese
    title = _("%(name)s's Detail", name=text)
    result = check_user()
    # get comments
    comments = Comment.query.filter_by(commentProduct_id=pro_id).all()
    for c in comments:
        if c.level == '':
            c.level=0
    score = round(float(mean([comment.level for comment in comments])), 2) if comments != [] else 5.0
    print(score)
    if result is not None:
        return render_template('product_detail.html', title=title, product=product, user=result[0], path=result[1], comments=comments, score=score)
    else:
        return render_template('product_detail.html', title=title, product=product, comments=comments,score=score)


@main.route('/addToCart', methods=['POST'])
def addToCart():
    username = request.form.get("username")
    id = request.form.get("productID")
    num = request.form.get("num")
    if username == session.get("USERNAME"):
        product = Products.query.filter_by(product_id=id).first()
        if product is not None:
            user = User.query.filter_by(username=username).first()
            success = user.add_to_cart(product, num)
            if success:
                db.session.commit()
                # success add to shopping
                return jsonify({'returnValue': 0})
            else:
                # already in the shopping cart
                return jsonify({'returnValue': 1})
        else:
            return jsonify({'returnValue': 2})
    else:
        return jsonify({'returnValue': 3})


@main.route('/changeNumberInCart', methods=['POST'])
def changeNum():
    id = '#' + request.form.get("productID")
    num = request.form.get("num")
    user = User.query.filter_by(username=session.get('USERNAME')).first()
    # get the shopping by user
    shopping = user.shopping_product.filter_by(shoppingProduct_id=id).first()
    shopping.number = num
    db.session.commit()
    return jsonify({'returnValue': 0, 'num': num, 'price': shopping.shopping_product.product_price})


@main.route('/deleteShopping', methods=['POST'])
def deleteShopping():
    result = request.form.getlist("productID")
    type = request.form.get('type')
    user = User.query.filter_by(username=session.get('USERNAME')).first()
    if type == 'single':
        id = '#' + result[0]
        shopping = user.shopping_product.filter_by(shoppingProduct_id=id).first()
        db.session.delete(shopping)
    else:
        for i in result:
            shopping = user.shopping_product.filter_by(shoppingProduct_id=i).first()
            db.session.delete(shopping)
    db.session.commit()
    return jsonify({'returnValue': 0})


@main.route('/shopping_cart', methods=['POST', 'GET'])
# the page for the shopping cart
def shopping_cart():
    # order = OrderProduct.query.filter_by().first()
    # print(order.product.query.all())
    # print(order)
    result = session.get('TYPE')
    if result == 'user':
        session['dic'] = {}
        title = _("%(username)s's Shopping Cart", username=session.get("USERNAME"))
        shoppings = Shopping.query.filter_by(shoppingUser_id=session.get("ID")).all()
        re = check_user()
        return render_template('shopping_cart.html', title=title, shoppings=shoppings, user=re[0],
                               path=re[1])
    else:
        flash(_("You are not a customer."))
        return redirect(url_for('customer.index'))


@main.route('/writeDetails', methods=['POST'])
def write():
    dic = request.form.to_dict()
    session['dic'] = dic
    # print("session:{}.".format(session.get('dic')))
    return jsonify(success=1)


@main.route('/api/make_comment', methods=['POST'])
def make_comment():
    dic = request.form.to_dict()
    print(dic)
    user = User.query.filter_by(username=session.get("USERNAME")).first()
    for i in dic.keys():
        if len(i.split("_")) != 2:
            pid = i.split("*")[0]
            body = dic[i]
            star = dic[i+'_star']
            if body != "":
                new_comment = Comment(commentProduct_id=pid,commentUser_id=user.id,level=star,content=body)
            else:
                if star == '0':
                    new_comment = Comment(commentProduct_id=pid, commentUser_id=user.id, level=star, content="horrible purchasing experience")
                elif star== '1':
                    new_comment = Comment(commentProduct_id=pid, commentUser_id=user.id, level=star, content="awful product")
                elif star == '2':
                    new_comment = Comment(commentProduct_id=pid, commentUser_id=user.id, level=star, content="it is not worth")
                elif star == '3':
                    new_comment = Comment(commentProduct_id=pid, commentUser_id=user.id, level=star, content="just SOSO")
                elif star == '4':
                    new_comment = Comment(commentProduct_id=pid, commentUser_id=user.id, level=star, content="good product")
                else:
                    new_comment = Comment(commentProduct_id=pid, commentUser_id=user.id, level=star, content="perfect product")
            db.session.add(new_comment)
    db.session.commit()
    return jsonify({'returnValue': 0})


@main.route('/writeID', methods=['POST'])
def viewAll():
    id = request.form.get('orderID')
    session['orderID'] = id
    print(session.get('orderID'))
    return jsonify(success=1)


@main.route('/mark_received', methods=['POST'])
def received():
    id = request.form.get('orderID')
    order = Order.query.filter_by(order_id=id).first()
    order.order_state = 'Finished'
    db.session.commit()
    return jsonify(success=1)


@main.route('/api/make_order', methods=['GET', 'POST'])
def make_order():
    phone = request.form.get('phone')
    address = request.form.get('address')
    state = request.form.get('state')
    delivery = request.form.get('delivery')
    my_map = session.get('dic')
    cost = my_map.get('total').strip("$")
    user = User.query.filter_by(username=session.get("USERNAME")).first()
    number = Order.query.all()[-1]
    current_id = number.order_id
    next_id = int(current_id[1:])
    if int(delivery) == 1:
        random_code = string.ascii_lowercase + string.digits
        r = ''.join(random.sample(random_code, 6))
        orders = Order.query.all()
        code = []
        for i in orders:
            code.append(i.delivery)
        while r in code:
            r = ''.join(random.sample(random_code, 6))
        print(r)
    else:
        r = ''
    print('next_id: {}'.format(next_id))
    new_order = Order(order_id='&' + str(next_id + 1), total_cost=cost, orderUser_id=user.id, order_state=state,
                      order_address=address, order_phone=phone, order_consignee='wait',
                      state_reason='wait', delivery=r)
    user = User.query.filter_by(username=session.get("USERNAME")).first()
    title = _("%(username)s's Order", username=user.username)
    keys = my_map.keys()
    for i in keys:
        if i == 'total':
            pass
        else:
            prototype = Products.query.filter_by(product_id=i).first()
            if prototype.product_state != "Published":
                db.session.rollback()
                return jsonify({'returnValue': 1})
            elif float(my_map[i]) > float(prototype.product_inventory) :
                db.session.rollback()
                return jsonify({'returnValue': 2})
            else:
                print(new_order.order_id)
                link = OrderProduct(middleProduct_id=i, middleOrder_id=new_order.order_id,
                                    number=my_map[i])
                shopping = Shopping.query.filter_by(shoppingUser_id=session.get('ID'), shoppingProduct_id=i).first()
                if shopping is not None:
                    db.session.delete(shopping)
                db.session.add(link)
    db.session.add(new_order)
    db.session.commit()
    session['dic'] = {}
    return jsonify(returnValue=0)


@main.route('/cancel_order', methods=['POST'])
def cancel_order():
    id = request.form.get('orderID')
    reason = request.form.get('reason')
    order = Order.query.filter_by(order_id=id).first()
    order.order_state = 'Exception'
    order.state_reason = reason
    db.session.commit()
    return jsonify(success=0)


@main.route('/delete_order', methods=['POST'])
def delete_order():
    id = request.form.get('orderID')
    order = Order.query.filter_by(order_id=id).first()
    db.session.delete(order)
    db.session.commit()
    return jsonify(success=0)


@main.route('/order', methods=['POST', 'GET'])
# the page for user who want to put order
def order():
    result = check_user()
    cost = 0
    state = State.query.first().state
    if result is not None:
        dic = session.get('dic')
        print('dic: {}'.format(dic))
        if dic.get('total') is not None:
            keys = dic.keys()
            products = []
            for i in keys:
                if i == 'total':
                    cost = dic.get('total')
                else:
                    product = Shopping.query.filter_by(shoppingUser_id=session.get('ID'), shoppingProduct_id=i).first()
                    products.append(product)
            user = User.query.filter_by(username=session.get("USERNAME")).first()
            title = _("%(username)s's Order", username=user.username)
            return render_template('order.html', title=title, user=result[0],
                                   shoppings=products, path=result[1], userInfo=user, cost=cost, state=state)
        return redirect(url_for('customer.shopping_cart'))
    else:
        flash(_("You are not a customer."))
        return redirect(url_for('customer.index'))


@main.route("/displayOrder", methods=['POST', 'GET'])
def display():
    result = check_user()
    if result is not None:
        id = session.get('orderID')
        if id != 0:
            user = User.query.filter_by(username=session.get("USERNAME")).first()
            order = Order.query.filter_by(order_id=id).first()
            print('selected order: {}'.format(order))
            if order.delivery is not None:
                if len(order.delivery) > 1:
                    return render_template('display_order.html', order=order, user=result[0], path=result[1], userInfo=user,
                                           isDelivery=True)
                else:
                    return render_template('display_order.html', order=order, user=result[0], path=result[1],
                                           userInfo=user,
                                           isDelivery=False)
            else:
                return render_template('display_order.html', order=order, user=result[0], path=result[1], userInfo=user,
                                       isDelivery=False)
        else:
            flash("your order has been deleted by the staff for some reasons")
            return redirect(url_for('customer.userinfo'))


@main.route("/userinfo", methods=['GET', 'POST'])
def userInfo():
    # personal information page
    if session.get('TYPE') == 'user':
        result = check_user()
        if result is not None:
            session['orderID'] = 0
            user = User.query.filter_by(username=session.get("USERNAME")).first()
            title = _("%(username)s's Profile", username=user.username)
            page = request.args.get('page', 1, type=int)
            pagination = Order.query.filter_by(orderUser_id=user.id) \
                .order_by(db.desc(Order.create_time)) \
                .paginate(page, 2, error_out=False)
            orders = pagination.items
            # orders = Order.query.filter_by(orderUser_id=user.id).all()
            print(orders)
            for i in orders:
                print('Order {} contains {}'.format(i.order_id, i.products.all()))
                for j in i.products.all():
                    print('products in order {}'.format(j.product))
            cookie = 1 # 1 stands for English
            if request.cookies.get('locale') is not None:
                cookie = 0
            return render_template('customerProfile.html', orders=orders, user=result[0],
                                   pagination=pagination, path=result[1], title=title, endpoint='.userInfo', cookie=cookie)
        flash("You need log in to see personal information")
        return redirect(url_for('customer.index'))
    flash(_("You are not a customer."))
    return redirect(url_for('customer.index'))


@main.route("/requestProductName", methods=['POST'])
def requestProductName():
    id = request.form.get('orderID')
    orders = OrderProduct.query.filter_by(middleOrder_id=id).all()
    products = {}
    for order in orders:
        if request.cookies.get('locale') == 'zh_Hans_CN':
            products[order.product.product_id] = order.product.name_chinese
        else:
            products[order.product.product_id] = order.product.product_name
    print(products)
    return jsonify(result=str(products))


@main.route("/api/buy_good", methods=['GET', 'POST'])
def buy_good():
    my_map = request.form.get('map')
    product_map = eval(my_map)
    cost = float(request.form.get('cost').strip("$"))
    user = User.query.filter_by(username=session.get("USERNAME")).first()
    number = db.session.query(func.max(Order.order_id)).scalar()
    new_order = Order(order_id=number + 1, total_cost=cost, orderUser_id=user.id, order_state='wait',
                      order_address='wait', order_phone='wait', order_consignee='wait',
                      state_reason='wait', delivery=r)
    i = 0
    while i < len(product_map):
        prototype = Products.query.filter_by(product_id=product_map[i]).first()
        if prototype.product_state != "Published":
            db.session.rollback()
            return jsonify({'returnValue': 1})
        elif float(product_map[i + 1]) > float(prototype.product_inventory):
            db.session.rollback()
            return jsonify({'returnValue': 2})
        else:
            link = OrderProduct(middleProduct_id=product_map[i], middleOrder_id=new_order.order_id,
                                number=product_map[i + 1])
            db.session.add(link)
        i = i + 2
    db.session.add(new_order)
    db.session.commit()

    return jsonify({'returnValue': 0})





@main.route('/change_email', methods=['POST'])
# the page for the shopping cart
def change_email():
    email = request.form.get("email")
    username = session.get("USERNAME")
    user = User.query.filter_by(username=username).first()
    user.email = email
    db.session.commit()
    return jsonify({'returnValue': 1})


@main.route('/about_us')
# the page for the about us page
def about_us():
    title=_('About Us')
    # check the state of user, whether a new user or logged in user
    result = check_user()
    if result is not None:
        return render_template('about_us.html', title=title, user=result[0], path=result[1])
    return render_template('about_us.html', title=title)


class VerifyCode(views.MethodView):
    def get(self):
        return render_template('customerProfile.html')  # 返回到修改邮箱页面url

    def post(self):
        username = session.get("USERNAME")
        user = User.query.filter_by(username=username).first()
        email = user.email
        captcha = request.form.get("captcha")
        # redis_captcha = redis_get(email)
        store_captcha = myCache.get(email)
        if not store_captcha or captcha.lower() != store_captcha.lower():  # 不区分大小写
            return '邮箱验证码错误'
        return jsonify({'code': 200})


@main.route('/api/getImage', methods=['POST'])
# ajax for getting paint in shop page
def getImages():
    pro_id = request.form['pro_id']
    pro_in_db = Products.query.filter(Products.product_id == pro_id).first()
    # if no product here
    if not pro_in_db:
        return jsonify({'pathes': None, 'name': None, 'returnValue': 1})
    else:
        pathes = Image.query.filter(Image.imgProduct_id == pro_in_db.product_id).all()[1:]
        imgs = []
        for path in pathes:
            if path.img_path != 'default.png':
                imgs.append('/static/img/product/pic/{}'.format(path.img_path))
        return jsonify({'pathes': imgs, 'name': pro_in_db.product_name, 'returnValue': 0})


@main.route('/api/getCategoryNumber', methods=['POST'])
# ajax for getting the number of each category
def getCategoryNumber():
    categories = Category.query.all()
    result = {}
    for category in categories:
        result[category.category_name] = Products.query.filter(
            Products.product_classification == category.category_name,
                                               Products.product_state == 'Published').count()
    return jsonify({'numbers': result, 'returnValue': 0})

@main.route('/api/getVideo', methods=['POST'])
# ajax for getting the display video
def getVideo():
    product_id = "#"+request.form.get('pro_id')
    src = Products.query.filter(Products.product_id == product_id).first().product_video
    # src = '/static/img/product/pic/{}'.format(src)
    src = url_for('static', filename = 'video/{}'.format(src))
    if src is not None:
        return jsonify({'src': src, 'returnValue': 0})
    abort(400)
    return jsonify({'src': src, 'returnValue': 1})

class EmailCaptcha(views.MethodView):
    def get(self):  # 根据resetemail.js中的ajax方法来写函数，不需要post请求
        username = session.get("USERNAME")
        user = User.query.filter_by(username=username).first()
        email = user.email
        # 发送邮件，内容为一个验证码：4、6位数字英文组合
        captcha = random_captcha.get_random_captcha(4)  # 生成4位验证码
        message = Message('very琴行更改邮箱验证码', recipients=[email], body='您的验证码是：%s' % captcha)

        # 异常处理
        try:
            mail.send(message)
        except:
            return "服务器错误，邮件验证码未发送！"  # 发送异常，服务器错误
        myCache.set(email,captcha,300)
        # redis_captcha.redis_set(key=email, value=captcha)  # redis中都是键值对类型，存储验证码
        # 验证码保存，一般有时效性，且频繁请求变化，所以保存在Redis中
        return jsonify({'code': 200})


main.add_url_rule("/verify_code/", view_func=VerifyCode.as_view('verify_code'))
main.add_url_rule("/email_captcha_change/", view_func=EmailCaptcha.as_view('email_captcha_change'))

