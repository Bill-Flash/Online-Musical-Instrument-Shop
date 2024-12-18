import os
import random
import re
import string
from datetime import datetime, timedelta

import cv2
from flask import render_template, url_for, request, jsonify, session, flash
from sqlalchemy import and_
from werkzeug.utils import redirect

from app.utils.sta_tools import *
from config import Config
from . import staff
from .. import db
from ..forms import CreateMIForm, CreateTypeForm, ModifyOrderForm, AddReplyForm, ClosedOrderForm
from ..models import Products, Image, Category, Order, OrderProduct, Chat, State, Answer, User


@staff.route('/')
# index part
@staff.route('/index', methods=['GET', 'POST'])
def index():
    # index of staff
    staff_name = session.get("USERNAME")
    return render_template('staff/staindex.html', title="Staff Index", staffname=staff_name)


@staff.route('/get_new_profit', methods=['POST'])
def get_new_profit():
    today = datetime.today().date()
    orders = Order.query.all()
    sum = 0
    sum_finished = 0
    for e in orders:
        if e.create_time.date() == today:
            sum += e.total_cost
            if e.order_state == "Finished":
                sum_finished += e.total_cost
    if sum == 0:
        percentage = 0
    else:
        percentage = int(sum_finished / sum * 100)
    return jsonify([sum, percentage, percentage / 100])


@staff.route('/get_new_orders', methods=['POST'])
def get_new_orders():
    today = datetime.today().date()
    orders = Order.query.all()
    sum = 0
    sum_finished = 0
    for e in orders:
        if e.create_time.date() == today:
            sum += 1
            if e.order_state == "Finished":
                sum_finished += 1
    if sum == 0:
        percentage = 0
    else:
        percentage = int(sum_finished / sum * 100)
    return jsonify([sum, percentage, percentage / 100])


@staff.route('/get_state', methods=['POST'])
def get_state():
    # get state of physical store
    return State.query.first().state


@staff.route('/change_state', methods=['POST'])
def change_state():
    data = request.get_data(as_text=True)
    state = State.query.first()
    if data == "Open":
        state.state = "Closed"
        orders = Order.query.filter_by(order_state="Paid(picking up)").all()
        for e in orders:
            e.order_state = "Exception"
            e.state_reason = "Due to the epidemic, the physical store is closed."
        return "Closed"
    else:
        state.state = "Open"
        return "Open"


@staff.route('/get_weekly_profits', methods=['POST'])
def get_weekly_profits():
    # get profits in a week
    weekday = datetime.weekday(datetime.today())
    orders = Order.query.all()
    profits = []
    for i in range(0, weekday + 1):
        profit = 0
        mid_day = (datetime.today() + timedelta(-i)).date()
        for e in orders:
            if e.create_time.date() == mid_day:
                profit = profit + e.total_cost
        profits.insert(0, profit)
    for k in range(0, 7 - len(profits)):
        profits.append(0)
    print(profits)
    return jsonify(profits)


@staff.route('get_index_orders', methods=['POST'])
def get_index_orders():
    all = Order.query.filter_by().count()
    process1 = Order.query.filter_by(order_state="Paid(delivery)").count()
    process2 = Order.query.filter_by(order_state="Paid(picking up)").count()
    process3 = Order.query.filter_by(order_state="Delivery").count()
    finished1 = Order.query.filter_by(order_state="Finished").count()
    error1 = Order.query.filter_by(order_state="Canceled").count()
    error2 = Order.query.filter_by(order_state="Exception").count()
    count1 = error1 + error2
    count2 = process1 + process2 + process3
    count3 = finished1
    process = int(count2 / all * 100)
    error = int((error1 + error2) / all * 100)
    finished = int(finished1 / all * 100)
    lis = []
    lis.append(count1)
    lis.append(count2)
    lis.append(count3)
    lis.append(error)
    lis.append(process)
    lis.append(finished)

    print(lis)
    return jsonify(lis)


# base part
@staff.route('/all_search/', methods=['GET', 'POST'])
def all_search():
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        search = request.values.get('comprehensive-search-input')
        print(search)
        if search is not None:
            arr = search.split(" ")
            if arr[0] == "mi":
                search = "#" + arr[1:].join(" ")
            elif arr[0] == "order":
                search = "&" + arr[1:].join(" ")
        return render_template('staff/staallsearch.html', search=search, staffname=staff_name)
    return redirect(url_for('customer.index'))


# musical instrument part
@staff.route('/addmi', methods=['GET', 'POST'])
def addmi():
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        form = CreateMIForm()
        categories = Category.query.filter_by().all()
        form.type2.choices = [(e.category_name, e.category_name) for e in categories]
        return render_template('staff/staaddmi.html', form=form, title="Add Musical Instrument", staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/get_types', methods=['POST'])
def get_types():
    region = request.get_data(as_text=True)
    print(region)
    if region == "":
        types = Category.query.filter_by().all()
    else:
        types = Category.query.filter_by(category_language=region).all()
    lis = []
    for e in types:
        lis.append(e.category_name)
    print(lis)
    return jsonify(lis)


@staff.route('/mis', methods=['GET', 'POST'])
# the page for showing musical instruments
def mis():
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        products = Products.query.order_by(db.desc(Products.product_price)).all()
        return render_template('staff/stamis.html', products=products, title="Musical Instruments",
                               staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/get_max_mis', methods=['POST'])
def get_max_mis():
    num = int(request.form.get("num"))
    type = request.form.get("type")
    search = request.form.get("search")
    print(num)
    print(search.count("#"))
    if search != "null":
        if search.count("#") != 0:
            mis_source = Products.query.filter_by().all()
            mis = []
            for mi in mis_source:
                if re.match(search, mi.product_id) is not None:
                    mis.append(mi)
        else:
            print(search)
            if type == "all":
                mis_source = Products.query.filter_by().all()
                mis = []
                for mi in mis_source:
                    if re.search(search, mi.product_name, flags=re.I) is not None:
                        mis.append(mi)
                    else:
                        if re.search(search, mi.product_id, flags=re.I) is not None:
                            mis.append(mi)
            else:
                mis_source = Products.query.filter_by(product_classification=type).all()
                mis = []
                for mi in mis_source:
                    if re.search(search, mi.product_name, flags=re.I) is not None:
                        mis.append(mi)
                    else:
                        if re.search(search, mi.product_id, flags=re.I) is not None:
                            mis.append(mi)
    else:
        if type == "all":
            mis = Products.query.filter_by().all()
        else:
            mis = Products.query.filter_by(product_classification=type).all()
    a = len(mis) / num
    pages = int(a)
    if pages < len(mis) / num:
        pages = pages + 1
    return str(pages)


@staff.route('/get_mis', methods=['POST'])
def get_mis():
    max_num = int(request.form.get("max"))
    page = int(request.form.get("page"))
    type = request.form.get("type")
    search = request.form.get("search")
    rank = request.form.get("rank")
    print(max_num)
    print(page)
    if search != "null":
        if search.count("#") != 0:
            if type == "all":
                mis_source = Products.query.filter_by().all()
                mis = []
                for mi in mis_source:
                    if re.match(search, mi.product_id) is not None:
                        mis.append(mi)
            else:
                mis_source = Products.query.filter_by(product_classification=type).all()
                mis = []
                for mi in mis_source:
                    if re.match(search, mi.product_id) is not None:
                        mis.append(mi)
        else:
            if type == "all":
                mis_source = Products.query.filter_by().all()
                mis = []
                for mi in mis_source:
                    print(mi.product_name)
                    print(re.match(search, mi.product_name, flags=re.I))
                    if re.search(search, mi.product_name, flags=re.I) is not None:
                        mis.append(mi)
                    else:
                        if re.search(search, mi.product_id, flags=re.I) is not None:
                            mis.append(mi)
            else:
                mis_source = Products.query.filter_by(product_classification=type).all()
                mis = []
                for mi in mis_source:
                    if re.search(search, mi.product_name, flags=re.I) is not None:
                        mis.append(mi)
                    else:
                        if re.search(search, mi.product_id, flags=re.I) is not None:
                            mis.append(mi)
    else:
        if type == "all":
            mis = Products.query.filter_by().all()
        else:
            mis = Products.query.filter_by(product_classification=type).all()
    sorted_mis = []
    if rank == "price-up":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_price > smi.product_price:
                    k += 1
            sorted_mis.insert(k, mi)
    elif rank == "price-down":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_price < smi.product_price:
                    k += 1
            sorted_mis.insert(k, mi)
    elif rank == "name-up":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_name > smi.product_name:
                    k += 1
            sorted_mis.insert(k, mi)
    elif rank == "name-down":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_name < smi.product_name:
                    k += 1
            sorted_mis.insert(k, mi)
    elif rank == "category-up":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_classification > smi.product_classification:
                    k += 1
            sorted_mis.insert(k, mi)
    elif rank == "category-down":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_classification < smi.product_classification:
                    k += 1
            sorted_mis.insert(k, mi)
    elif rank == "inventory-up":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_inventory > smi.product_inventory:
                    k += 1
            sorted_mis.insert(k, mi)
    elif rank == "inventory-down":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_inventory < smi.product_inventory:
                    k += 1
            sorted_mis.insert(k, mi)
    elif rank == "status-up":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_state > smi.product_state:
                    k += 1
            sorted_mis.insert(k, mi)
    elif rank == "status-down":
        for mi in mis:
            k = 0
            for smi in sorted_mis:
                if mi.product_state < smi.product_state:
                    k += 1
            sorted_mis.insert(k, mi)
    else:
        sorted_mis = mis
    lis = []
    start_index = (page - 1) * max_num
    final_index = page * max_num
    if final_index <= len(sorted_mis):
        for e in sorted_mis[start_index:final_index]:
            lis.append(prepare_mi(e))
    else:
        for e in sorted_mis[start_index:]:
            lis.append(prepare_mi(e))
    print(lis)
    return jsonify(lis)


@staff.route('/del_mi', methods=['GET', 'POST'])
def del_mi():
    id = request.form['id']
    product = Products.query.filter_by(product_id=id).first()
    orders = OrderProduct.query.filter_by(middleProduct_id=id).all()
    if product is not None:
        db.session.delete(product)
        for i in orders:
            db.session.delete(i)
        db.session.commit()
        return jsonify({'returnValue': 200})
    else:
        return jsonify({'returnValue': 501})


def prepare_mi(item):
    mi = dict()
    mi['product_id'] = item.product_id
    mi['product_name'] = item.product_name
    mi['product_classification'] = item.product_classification
    mi['product_price'] = item.product_price
    mi['product_inventory'] = item.product_inventory
    mi['product_state'] = item.product_state
    return mi


@staff.route('/infomi/<pure_id>', methods=['GET', 'POST'])
# the page for showing a musical instrument
def infomi(pure_id):
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        id = "#" + pure_id
        product_info = Products.query.filter_by(product_id=id).first()
        imgs = Image.query.filter_by(imgProduct_id=id).all()
        product_img = Products.query.filter_by(product_id=id).first().product_path
        print(product_img)
        return render_template('staff/stainfomi.html', product=product_info, imgs=imgs, product_img=product_img,
                               title="Infomration " + id, staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/get_pics', methods=['Get', 'POST'])
def get_pics():
    id = request.form.get("id")
    pics = Image.query.filter_by(imgProduct_id=id).all()
    lis = []
    for p in pics:
        lis.append(display_pic(p))
    print(lis)
    return jsonify(lis)


@staff.route('/modmi/<pure_id>', methods=['GET', 'POST'])
def modmi(pure_id):
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        id = "#" + pure_id
        form = CreateMIForm()
        categories = Category.query.filter_by().all()
        form.type2.choices = [(e.category_name, e.category_name) for e in categories]
        if request.method == 'GET':
            form.proname.data = Products.query.filter_by(product_id=id).first().product_name
            form.proname2.data = Products.query.filter_by(product_id=id).first().name_chinese
            form.description.data = Products.query.filter_by(product_id=id).first().product_description
            form.description2.data = Products.query.filter_by(product_id=id).first().description_chinese
            imgs = Image.query.filter_by(imgProduct_id=id).all()
            form.state.data = Products.query.filter_by(product_id=id).first().product_state
            form.type1.data = Products.query.filter_by(product_id=id).first().product_region
            form.type2.data = Products.query.filter_by(product_id=id).first().product_classification
            form.price.data = Products.query.filter_by(product_id=id).first().product_price
            form.inventory.data = Products.query.filter_by(product_id=id).first().product_inventory
            poster = Products.query.filter_by(product_id=id).first().product_path
            product = Products.query.filter_by(product_id=id).first()
            # print(product_img)
        if request.method == 'POST':
            proname = request.form.get('proname')
            proname2 = request.form.get('proname2')
            description = request.form.get('description')
            description2 = request.form.get('description2')
            state = request.form.get('state')
            type1 = request.form.get('type1')
            type2 = request.form.get('type2')
            price = request.form.get('price')
            poster = request.files.get('poster')
            inventory = request.form.get('inventory')
            video = request.files.get('video')
            form = CreateMIForm(proname=proname, proname2=proname2, description=description, description2=description2,
                                state=state, type1=type1, type2=type2,
                                price=price, inventory=inventory, video=video, poster=poster)
            print("modify", poster)
            categories = Category.query.filter_by().all()
            form.type2.choices = [(e.category_name, e.category_name) for e in categories]
            if form.validate():
                product_changed = Products.query.filter_by(product_id=id).first()
                product_changed.product_name = proname
                product_changed.name_chinese = proname2
                product_changed.product_description = description
                product_changed.description_chinese = description2
                product_changed.product_price = price
                product_changed.product_inventory = inventory
                product_changed.product_region = type1
                product_changed.product_classification = type2
                if poster is not None:
                    poster_name = pure_id + '.jpg'
                    file_path1 = os.path.join(Config.PRODUCT_PIC_POSTER, poster_name)
                    poster.save(file_path1)
                    product_changed.product_path = poster_name
                if video is not None:
                    v_name = pure_id + '.mp4'
                    file_path2 = os.path.join(Config.PRODUCT_VIDEO, v_name)
                    video.save(file_path2)
                    product_changed.product_video = v_name
                db.session.commit()
                return {"id": 'success'}
            else:
                print(form.errors)
                return {"id": 'error'}

        return render_template('staff/stamodmi.html', form=form, imgs=imgs, poster=poster, id=pure_id, product=product,
                               title="Edit " + id, staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/get_type', methods=['GET', 'POST'])
def get_type():
    id = request.get_data(as_text=True)
    type1 = Products.query.filter_by(product_id=id).first().product_region
    type2 = Products.query.filter_by(product_id=id).first().product_classification
    return jsonify([type1, type2])


# type part
@staff.route('/addtype', methods=['GET', 'POST'])
def addtype():
    # the page of add instrument information
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        form = CreateTypeForm()
        if form.validate_on_submit():
            category = Category(category_language=form.type.data,
                                category_name=form.caname.data,
                                category_chinese=form.chiname.data)
            db.session.add(category)
            db.session.commit()
            return redirect(url_for('staff.addtype'))
        return render_template('staff/staaddtype.html', form=form, title="Add Categories", staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/deltype', methods=['GET', 'POST'])
def deltype():
    # the page of deleting categories
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        return render_template('staff/stadeltype.html', title="Delete Categories", staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/del_type', methods=['GET', 'POST'])
def del_type():
    # the function to delete categories in database
    type = request.get_data(as_text=True)
    category = Category.query.filter_by(category_name=type).first()
    if len(Products.query.filter_by(product_classification=type).all()) > 0:
        return "Unsuccessfully delete this category, because there are some musical instruments, whose type is " + type + "."
    db.session.delete(category)
    db.session.commit()
    return "Successfully"


# order part
@staff.route('/orders', methods=['GET', 'POST'])
# the page for showing orders
def orders():
    # products = Products.query.order_by(db.desc(Products.product_price)).all()
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        return render_template('staff/staorders.html', title="Orders", staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/get_max_orders', methods=['POST'])
def get_max_orders():
    num = int(request.form.get("num"))
    search = request.form.get("search")
    print(num)
    if search != "null":
        if search.count("&") != 0:
            orders_source = Order.query.filter_by().all()
            orders = []
            for order in orders_source:
                if re.match(search, order.order_id) is not None:
                    orders.append(order)
                else:
                    if re.search(search, order.order_id, flags=re.I) is not None:
                        orders.append(order)

        else:
            orders_source = Order.query.filter_by().all()
            orders = []
            for order in orders_source:
                if re.search(search, order.order_user.username, flags=re.I) is not None:
                    orders.append(order)
                else:
                    if re.search(search, order.order_id, flags=re.I) is not None:
                        orders.append(order)
    else:
        orders = Order.query.filter_by().all()
    a = len(orders) / num
    pages = int(a)
    if pages < len(orders) / num:
        pages = pages + 1
    return str(pages)


@staff.route('/get_orders', methods=['POST'])
def get_orders():
    max_num = int(request.form.get("max"))
    page = int(request.form.get("page"))
    search = request.form.get("search")
    rank = request.form.get("rank")
    print(max_num)
    print(page)
    print(search + " search")
    pri_orders = []
    normal_orders = []
    if search != "null":
        if re.match("&", search, re.I):
            orders = Order.query.all()
            # pri_orders = Order.query.filter_by(priority='Yes').all()
            # normal_orders = Order.query.filter_by(priority='No').all()
            for order in orders:
                if re.match(search, order.order_id) is not None:
                    if order.priority == 'Yes':
                        pri_orders.append(order)
                    else:
                        normal_orders.append(order)

            # for order in pri_orders:
            #     if re.match(search, order.order_id) is not None:
            #         orders.append(order)
            #     else:
            #         if re.search(search, order.order_id, flags=re.I) is not None:
            #             orders.append(order)
            # for order in normal_orders:
            #     if re.match(search, order.order_id) is not None:
            #         orders.append(order)
            #     else:
            #         if re.search(search, order.order_id, flags=re.I) is not None:
            #             orders.append(order)
        else:
            # pri_orders = Order.query.filter_by(priority='Yes').all()
            # normal_orders = Order.query.filter_by(priority='No').all()
            orders = Order.query.all()
            for order in orders:
                if re.search(search, order.order_user.username, flags=re.I) is not None \
                        or re.search(search, order.order_id, flags=re.I) is not None:
                    if order.priority == 'Yes':
                        pri_orders.append(order)
                    else:
                        normal_orders.append(order)
            # for order in pri_orders:
            #     if re.search(search, order.order_user.username, flags=re.I) is not None:
            #         orders.append(order)
            #     else:
            #         if re.search(search, order.order_id, flags=re.I) is not None:
            #             orders.append(order)
            # for order in normal_orders:
            #     if re.search(search, order.order_user.username, flags=re.I) is not None:
            #         orders.append(order)
            #     else:
            #         if re.search(search, order.order_id, flags=re.I) is not None:
            #             orders.append(order)
    else:
        pri_orders = Order.query.filter_by(priority='Yes').all()
        normal_orders = Order.query.filter_by(priority='No').all()
        # for order in pri_orders:
        #     orders.append(order)
        # for order in normal_orders:
        #     orders.append(order)
    sorted_pri_orders = []
    sorted_normal_orders = []
    if rank == "time-up":
        for order in pri_orders:
            k = 0
            for sorder in sorted_pri_orders:
                if order.create_time > sorder.create_time:
                    k += 1
            sorted_pri_orders.insert(k, order)
        for order in normal_orders:
            k = 0
            for sorder in sorted_normal_orders:
                if order.create_time > sorder.create_time:
                    k += 1
            sorted_normal_orders.insert(k, order)
    elif rank == "time-down":
        for order in pri_orders:
            k = 0
            for sorder in sorted_pri_orders:
                if order.create_time < sorder.create_time:
                    k += 1
            sorted_pri_orders.insert(k, order)
        for order in normal_orders:
            k = 0
            for sorder in sorted_normal_orders:
                if order.create_time < sorder.create_time:
                    k += 1
            sorted_normal_orders.insert(k, order)
    elif rank == "total-cost-up":
        for order in pri_orders:
            k = 0
            for sorder in sorted_pri_orders:
                if order.total_cost > sorder.total_cost:
                    k += 1
            sorted_pri_orders.insert(k, order)
        for order in normal_orders:
            k = 0
            for sorder in sorted_normal_orders:
                if order.total_cost > sorder.total_cost:
                    k += 1
            sorted_normal_orders.insert(k, order)
    elif rank == "total-cost-down":
        for order in pri_orders:
            k = 0
            for sorder in sorted_pri_orders:
                if order.total_cost < sorder.total_cost:
                    k += 1
            sorted_pri_orders.insert(k, order)
        for order in normal_orders:
            k = 0
            for sorder in sorted_normal_orders:
                if order.total_cost < sorder.total_cost:
                    k += 1
            sorted_normal_orders.insert(k, order)
    elif rank == "status-up":
        for order in pri_orders:
            k = 0
            for sorder in sorted_pri_orders:
                if order.order_state > sorder.order_state:
                    k += 1
            sorted_pri_orders.insert(k, order)
        for order in normal_orders:
            k = 0
            for sorder in sorted_normal_orders:
                if order.order_state > sorder.order_state:
                    k += 1
            sorted_normal_orders.insert(k, order)
    elif rank == "status-down":
        for order in pri_orders:
            k = 0
            for sorder in sorted_pri_orders:
                if order.order_state < sorder.order_state:
                    k += 1
            sorted_pri_orders.insert(k, order)
        for order in normal_orders:
            k = 0
            for sorder in sorted_normal_orders:
                if order.order_state < sorder.order_state:
                    k += 1
            sorted_normal_orders.insert(k, order)
    elif rank == "customer-name-up":
        for order in pri_orders:
            k = 0
            for sorder in sorted_pri_orders:
                if order.order_user.username > sorder.order_user.username:
                    k += 1
            sorted_pri_orders.insert(k, order)
        for order in normal_orders:
            k = 0
            for sorder in sorted_normal_orders:
                if order.order_user.username > sorder.order_user.username:
                    k += 1
            sorted_normal_orders.insert(k, order)
    elif rank == "customer-name-down":
        for order in pri_orders:
            k = 0
            for sorder in sorted_pri_orders:
                if order.order_user.username < sorder.order_user.username:
                    k += 1
            sorted_pri_orders.insert(k, order)
        for order in normal_orders:
            k = 0
            for sorder in sorted_normal_orders:
                if order.order_user.username < sorder.order_user.username:
                    k += 1
            sorted_normal_orders.insert(k, order)
    else:
        sorted_pri_orders = pri_orders
        sorted_normal_orders = normal_orders
    sorted_orders = []
    for order in sorted_pri_orders:
        sorted_orders.append(order)
    for order in sorted_normal_orders:
        sorted_orders.append(order)
    lis = []
    start_index = (page - 1) * max_num
    final_index = page * max_num
    if final_index <= len(sorted_orders):
        for e in sorted_orders[start_index:final_index]:
            lis.append(prepare_order(e))
    else:
        for e in sorted_orders[start_index:]:
            lis.append(prepare_order(e))
    print(lis)
    return jsonify(lis)


def prepare_order(item):
    order = dict()
    order['order_id'] = item.order_id
    order['create_time'] = item.create_time
    order['total_cost'] = item.total_cost
    order['orderUser_id'] = item.orderUser_id
    order['orderUser_username'] = item.order_user.username
    order['order_state'] = item.order_state
    order['order_priority'] = item.priority
    middle = item.products.all()
    lis = []
    for m in middle:
        lis.append(m.product.product_name)
    order['product_name'] = lis

    return order


@staff.route('/del_order', methods=['GET', 'POST'])
def del_order():
    id = request.form['id']
    orders = OrderProduct.query.filter_by(middleOrder_id=id).all()
    order = Order.query.filter_by(order_id=id).first()
    if orders is not None:
        for o in orders:
            db.session.delete(o)
            db.session.delete(order)
            db.session.commit()
        return jsonify({'returnValue': 200})
    else:
        return jsonify({'returnValue': 501})


@staff.route('/infoorder/<pure_id>', methods=['GET', 'POST'])
# the page for showing a musical instrument
def infoorder(pure_id):
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        id = "&" + pure_id
        order_info = Order.query.filter_by(order_id=id).first()
        buyer = order_info.order_user
        products = order_info.products.all()
        return render_template('staff/stainfoorder.html', order=order_info, buyer=buyer, products=products,
                               title="Information " + id, staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/modorder/<pure_id>', methods=['GET', 'POST'])
def modorder(pure_id):
    state = State.query.first()
    if state.state == "Open":
        form = ModifyOrderForm()
    else:
        form = ClosedOrderForm()
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        if request.method == 'GET':
            id = '&' + pure_id
            order_info = Order.query.filter_by(order_id=id).first()
            buyer = order_info.order_user
            products = order_info.products.all()
            form.state.data = order_info.order_state
            form.address.data = order_info.order_address
            form.phone_number.data = order_info.order_phone
            form.rec_name.data = order_info.order_consignee
            form.reason.data = order_info.state_reason
            form.priority.data = order_info.priority

            return render_template('staff/stamodorder.html', form=form, order=order_info, buyer=buyer,
                                   products=products,
                                   title="Edit " + pure_id, staffname=staff_name, store_state=State.query.first().state)
        if form.validate_on_submit():
            id = pure_id
            order_info = Order.query.filter_by(order_id=id).first()
            buyer = order_info.order_user
            products = order_info.products.all()
            order_info.order_state = form.state.data
            order_info.order_address = form.address.data
            order_info.order_phone = form.phone_number.data
            order_info.order_consignee = form.rec_name.data
            order_info.state_reason = form.reason.data
            order_info.priority = form.priority.data
            db.session.commit()
            return redirect(url_for('staff.orders'))

    flash("you are not a manager")
    return redirect(url_for('customer.index'))


# reply part
@staff.route('/addreply', methods=['GET', 'POST'])
def addreply():
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        form = AddReplyForm()
        if form.validate_on_submit():
            answer = Answer(question=form.question.data,
                            answer=form.answer.data)
            db.session.add(answer)
            db.session.commit()
            return redirect(url_for('staff.addreply'))
        return render_template('staff/staaddreply.html', form=form, title="Add Reply", staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/replys', methods=['GET', 'POST'])
# the page for showing musical instruments
def replys():
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        return render_template('staff/stareplys.html', title="Replys",
                               staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/get_max_replys', methods=['POST'])
def get_max_replys():
    num = int(request.form.get("num"))
    search = request.form.get("search")
    print(num)
    if search != "null":
        replys_source = Answer.query.filter_by().all()
        replys = []
        for reply in replys_source:
            if re.search(search, reply.question, flags=re.I) is not None\
                    or re.search(search, str(reply.answer_id), flags=re.I)\
                    or re.search(search, str(reply.answer), flags=re.I):
                replys.append(reply)
    else:
        replys = Answer.query.filter_by().all()
    # orders = Order.query.filter_by().all()
    a = len(replys) / num
    pages = int(a)
    if pages < len(replys) / num:
        pages = pages + 1
    return str(pages)


@staff.route('/get_replys', methods=['POST'])
def get_replys():
    max_num = int(request.form.get("max"))
    page = int(request.form.get("page"))
    search = request.form.get("search")
    print(max_num)
    print(page)
    if search != "null":
        replys_source = Answer.query.filter_by().all()
        replys = []
        for reply in replys_source:
            if re.search(search, reply.question, flags=re.I) is not None \
                    or re.search(search, str(reply.answer_id), flags=re.I) \
                    or re.search(search, str(reply.answer), flags=re.I):
                replys.append(reply)
    else:
        replys = Answer.query.filter_by().all()
    lis = []
    start_index = (page - 1) * max_num
    final_index = page * max_num
    if final_index <= len(replys):
        for e in replys[start_index:final_index]:
            lis.append(prepare_reply(e))
    else:
        for e in replys[start_index:]:
            lis.append(prepare_reply(e))
    print(lis)
    return jsonify(lis)


def prepare_reply(item):
    reply = dict()
    reply['answer_id'] = item.answer_id
    reply['question'] = item.question
    reply['answer'] = item.answer

    return reply


@staff.route('/del_reply', methods=['GET', 'POST'])
def del_reply():
    id = request.form['id']
    reply = Answer.query.filter_by(answer_id=id).first()
    if reply is not None:
        db.session.delete(reply)
        db.session.commit()
        return jsonify({'returnValue': 200})
    else:
        return jsonify({'returnValue': 501})


@staff.route('/inforeply/<id>', methods=['GET', 'POST'])
# the page for showing a musical instrument
def inforeply(id):
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        reply_info = Answer.query.filter_by(answer_id=id).first()
        return render_template('staff/stainforeply.html', reply=reply_info,
                               title="Information " + id, staffname=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/modreply/<id>', methods=['GET', 'POST'])
def modreply(id):
    form = AddReplyForm()
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        reply_info = Answer.query.filter_by(answer_id=id).first()
        if request.method == 'GET':
            form.question.data = reply_info.question
            form.answer.data = reply_info.answer
        if form.validate_on_submit():
            reply_info.question = form.question.data
            reply_info.answer = form.answer.data
            db.session.commit()
            return redirect(url_for('staff.index'))

        return render_template('staff/stamodreply.html', form=form, reply=reply_info,
                               title="Edit " + id, staff_name=staff_name)
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


def display_pic(item):
    pic = dict()
    pic['img_path'] = item.img_path
    return pic


@staff.route('/chat')
def chat_index():
    if session.get('TYPE') == 'manager':
        staff_name = session.get("USERNAME")
        rooms = Chat.query.with_entities(Chat.chatroom).distinct().all()
        photo_dir = Config.PROFILE_UPLOAD_DIR
        photo_paths = dict()
        not_read = dict()
        for r in rooms:
            photo_path = os.path.join(photo_dir, '{}_profile.png'.format(r.chatroom))
            path = os.path.exists(photo_path)
            if path:
                photo_paths[r.chatroom] = 1
            else:
                photo_paths[r.chatroom] = 0

            not_read[r.chatroom] = Chat.query.filter(and_(Chat.chatroom == r.chatroom, Chat.read == 0)).count()
        return render_template('staff/staChat.html', room='Please choose a customer', path=0, chooseuser=0, rooms=rooms,
                               title="Chat", photo_path=photo_paths, not_read=not_read, staffname=staff_name)

    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/chat/<roomname>')
def chat(roomname):
    if session.get('TYPE') == 'manager':
        if 'USERNAME' in session:
            staff_name = session.get("USERNAME")
            rooms = Chat.query.with_entities(Chat.chatroom).distinct().all()
            username = session['USERNAME']
            room = roomname[2:-3]
            path = 0
            photo_dir = Config.PROFILE_UPLOAD_DIR
            photo_paths = dict()
            not_read = dict()
            for r in rooms:
                photo_path = os.path.join(photo_dir, '{}_profile.png'.format(r.chatroom))
                p = os.path.exists(photo_path)
                if p:
                    photo_paths[r.chatroom] = 1
                    if r.chatroom == room:
                        path = 1
                else:
                    photo_paths[r.chatroom] = 0
                    if r.chatroom == room:
                        path = 0

                if room == r.chatroom:
                    not_read[r.chatroom] = 0
                    nr = Chat.query.filter(and_(Chat.chatroom == r.chatroom, Chat.read == 0)).all()
                    for nri in nr:
                        nri.read = 1
                        db.session.add(nri)
                        db.session.commit()
                else:
                    not_read[r.chatroom] = Chat.query.filter(and_(Chat.chatroom == r.chatroom, Chat.read == 0)).count()
            message = Chat.query.filter_by(chatroom=room).all()
            message_product = 1
            product = Products.query.first()
            pros = {}
            for msg in message:
                if msg.message_type == 0:
                    pro_in_db = Products.query.filter(Products.product_id == msg.chat_message).first()
                    pros[pro_in_db.product_id] = pro_in_db
            print(path)
            return render_template('staff/staChat.html', username=username, room=room, chooseuser=1, rooms=rooms,
                                   messages=message, message_prodect=message_product, product=product, pros=pros,
                                   title=room, photo_path=photo_paths, path=path, not_read=not_read,
                                   staffname=staff_name)
        else:
            flash("you need login first")
            return redirect(url_for('main.confirm_login'))
    flash("you are not a manager")
    return redirect(url_for('customer.index'))


@staff.route('/newmi', methods=['GET', 'POST'])
def newmi():
    proname = request.form.get('proname')
    proname2 = request.form.get('proname2')
    description = request.form.get('description')
    description2 = request.form.get('description2')
    state = request.form.get('state')
    type1 = request.form.get('type1')
    type2 = request.form.get('type2')
    price = request.form.get('price')
    poster = request.files.get('poster')
    inventory = request.form.get('inventory')
    video = request.files.get('video')
    final_id = request.form.get('final_id')
    print("myid" + final_id)

    form = CreateMIForm(proname=proname, description=description, description2=description2, state=state, type1=type1,
                        type2=type2,
                        price=price, inventory=inventory, video=video, poster=poster, proname2=proname2)
    print("jjjjjj", poster)
    categories = Category.query.filter_by().all()
    form.type2.choices = [(e.category_name, e.category_name) for e in categories]
    if form.validate():
        poster_name = None
        v_name = None
        if poster is not None:
            poster_name = final_id[1:] + '.jpg'
            file_path1 = os.path.join(Config.PRODUCT_PIC_POSTER, poster_name)
            poster.save(file_path1)
        if video is not None:
            v_name = final_id[1:] + '.mp4'
            file_path2 = os.path.join(Config.PRODUCT_VIDEO, v_name)
            video.save(file_path2)

        instrument = Products(product_id=final_id,
                              product_name=proname,
                              name_chinese=proname2,
                              product_region=type1,
                              product_state=state,
                              product_classification=type2,
                              product_price=price,
                              product_description=description,
                              description_chinese=description2,
                              product_inventory=inventory,
                              product_path=poster_name,
                              product_video=v_name
                              )
        db.session.add(instrument)
        db.session.commit()
        return {"id": 'success'}
    else:
        print(form.errors)
        return {"id": 'error'}


@staff.route('/get_id', methods=['POST'])
def get_id():
    pre_id = produce_id()
    final_id_flag = False
    same_num = 0
    while final_id_flag != True:
        final_id = pre_id + str(same_num)
        if Products.query.filter_by(product_id=final_id).first() is None:
            final_id_flag = True
            final_id = final_id
        else:
            same_num += 1
    print(final_id)
    return {"id": final_id}


@staff.route('/newImages', methods=['GET', 'POST'])
def newImages():
    if request.method == 'POST':
        print("iii")
        images = request.files.values()
        name = request.form.get('id')
        print("=======================")
        product_id = name
        pic = name[1:]
        pic_dir = Config.PRODUCT_PIC_IMG
        curtime = int(datetime.now().strftime('%H%M%S%f')[: -3])
        # num = Image.query.filter_by(imgProduct_id=product_id).count()
        print(images)
        for i in images:
            print(i)
            filename = pic + '_{}.jpg'.format(curtime)
            i.save(os.path.join(pic_dir, filename))
            print(os.path.join(pic_dir, filename))

            im = cv2.imread(os.path.join(pic_dir, filename))
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
            cv2.imwrite(os.path.join(pic_dir, filename), im)

            # print(os.path.exists(os.path.abspath(os.path.join(pic_dir, filename))))
            img = Image(imgProduct_id=product_id, img_path=filename)
            db.session.add(img)
            db.session.commit()
        return jsonify({'success': 0})


@staff.route('/uploadImages', methods=['GET', 'POST'])
def uploadImages():
    if request.method == 'POST':
        print("000000")
        images = request.files.values()
        name = request.form.get('productID')
        product_id = '#' + name
        pic_dir = Config.PRODUCT_PIC_IMG
        curtime = int(datetime.now().strftime('%H%M%S%f')[: -3])
        # num = Image.query.filter_by(imgProduct_id=product_id).count()
        print(images)
        for i in images:
            print(i)
            filename = name + '_{}.jpg'.format(curtime)
            i.save(os.path.join(pic_dir, filename))
            print(os.path.join(pic_dir, filename))

            im = cv2.imread(os.path.join(pic_dir, filename))
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
            cv2.imwrite(os.path.join(pic_dir, filename), im)

            # print(os.path.exists(os.path.abspath(os.path.join(pic_dir, filename))))
            img = Image(imgProduct_id=product_id, img_path=filename)
            db.session.add(img)
            db.session.commit()
        return jsonify({'success': 0})


@staff.route('/deleteImages', methods=['GET', 'POST'])
def deleteImages():
    if request.method == 'POST':
        img_path = str(request.form.get('id')).split('/')[-1]
        name = re.findall('20.*', img_path)[0]
        id = re.findall('20.*?_', img_path)[0]
        product_id = '#' + id[:-1]
        print(product_id)
        print(name)
        img = Image.query.filter_by(imgProduct_id=product_id, img_path=name).first()
        db.session.delete(img)
        db.session.commit()
        path = os.path.join(Config.PRODUCT_PIC_IMG, img_path)
        # print(img_path)
        os.remove(path)
    return jsonify({'success': 0})


@staff.route('/verification_code')
def verification_code():
    random_code = string.ascii_lowercase + string.digits
    r = ''.join(random.sample(random_code, 6))
    orders = Order.query.all()
    code = []
    for i in orders:
        code.append(i.delivery)
    print(code)
    while r in code:
        r = ''.join(random.sample(random_code, 6))
    print(r)
