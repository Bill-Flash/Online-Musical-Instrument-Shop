import re

from sqlalchemy import or_

from app.models import Category


def search(request, Products, db, region=None, category=None):
    """
    :param request: the context
    :param Products: the Product
    :param db: the database
    :param region: default is for all product
                    Western or Chinese
    :param category: default is for all product
                    the different categories we have
    :return: the pagination, the number of product for every page and the name they want to search
    """
    # Search Product by name
    name = request.args.get('find')
    # Search Product by price
    price = request.args.get('price')
    if price is not None:
        price = list(map(int,re.findall(r'\d+', price)))
        if len(price) < 2:
            price=[200,1000]
        if price[0] > price[1]:
            a = price[0]
            price[0] = price[1]
            price[1] = a

    # for pagination, default = 1
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 3, type=int)
    pagination = Products.query.order_by(db.desc(Products.product_price)).paginate(
        page, per_page, error_out=False
    )
    if region is None and category is None:
        if name and price:
            pagination = Products.query.filter(or_(Products.product_name.like('%' + name + '%'),Products.name_chinese.like('%' + name + '%')),
                                               Products.product_price >= price[0],
                                               Products.product_price <= price[1],
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
        elif name:
            pagination = Products.query.filter(or_(Products.product_name.like('%' + name + '%'),Products.name_chinese.like('%' + name + '%')),
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
        elif price:
            pagination = Products.query.filter(Products.product_price >= price[0],
                                               Products.product_price <= price[1],
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
        else:
            pagination = Products.query.filter(Products.product_state == 'Published')\
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
    elif region is not None:
        if name and price:
            pagination = Products.query.filter(or_(Products.product_name.like('%' + name + '%'),Products.name_chinese.like('%' + name + '%')),
                                               Products.product_price >= price[0],
                                               Products.product_price <= price[1],
                                               Products.product_region == region,
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
        elif name:
            pagination = Products.query.filter(or_(Products.product_name.like('%' + name + '%'),Products.name_chinese.like('%' + name + '%'))
                                               ,Products.product_region == region,
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
        elif price:
            pagination = Products.query.filter(Products.product_price >= price[0],
                                               Products.product_price <= price[1],
                                               Products.product_region == region,
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
        else:
            pagination = Products.query.filter(Products.product_region == region,
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
    elif category is not None:
        if name and price:
            pagination = Products.query.filter(or_(Products.product_name.like('%' + name + '%'),Products.name_chinese.like('%' + name + '%'))
                                               ,Products.product_price >= price[0]
                                               ,Products.product_price <= price[1]
                                               ,Products.product_classification == category,
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
        elif name:
            pagination = Products.query.filter(or_(Products.product_name.like('%' + name + '%'),Products.name_chinese.like('%' + name + '%'))
                                               , Products.product_classification == category,
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
        elif price:
            pagination = Products.query.filter(Products.product_price >= price[0]
                                               , Products.product_price <= price[1]
                                               , Products.product_classification == category,
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
        else:
            pagination = Products.query.filter(Products.product_classification == category,
                                               Products.product_state == 'Published') \
                .order_by(db.desc(Products.product_price)) \
                .paginate(page, per_page, error_out=False)
    # get category information
    category_W = Category.query.filter(Category.category_language == 'Western').all()
    category_C = Category.query.filter(Category.category_language == 'Chinese').all()
    category = {'Western': category_W, 'Chinese': category_C}
    price = request.args.get('price')
    return pagination, per_page, name, category, price
