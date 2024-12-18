from datetime import datetime

from sqlalchemy import func

from . import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # used to register an account
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(128))
    address = db.Column(db.String(120))
    city = db.Column(db.String(64))
    state = db.Column(db.String(64))
    country = db.Column(db.String(64))
    zip = db.Column(db.String(46))
    authority = db.Column(db.Integer, default=0)
    # used to show in the profile
    gender = db.Column(db.String(24))
    date_of_birth = db.Column(db.Date)
    phone = db.Column(db.String(24))

    # relationship to those shoppings which are added to a particular user's cart
    shopping_product = db.relationship('Shopping', back_populates='shopping_user', lazy='dynamic')

    # relationship to orders
    orders = db.relationship('Order', backref='order_user', lazy='dynamic')

    # relationship to chat
    chat = db.relationship('Chat', backref='chat_user', lazy='dynamic')

    # relationship to comment
    comments = db.relationship('Comment', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def is_addToCart(self, product):
        shopping = self.shopping_product.filter_by(shoppingProduct_id=product.product_id).first()
        print(shopping)
        if shopping is None:
            return False
        else:
            return True
        # return self.shopping_product.filter_by(
        #     shoppingProduct_id=product.product_id).first() is not None

    def add_to_cart(self, product, num):
        if not self.is_addToCart(product):
            shopping = Shopping(shopping_user=self, shopping_product=product, number=num)
            print("session added")
            db.session.add(shopping)
            return True
        else:
            return False

    def remove_from_cart(self, product):
        shopping = self.shopping_product.filter_by(shoppingProduct_id=product.product_id).first()
        if shopping:
            db.session.delete(shopping)


class Shopping(db.Model):
    __tablename__ = 'shopping'
    # a foreign key to the product which the shopping derive form
    shoppingProduct_id = db.Column(db.String(32), db.ForeignKey('products.product_id'), primary_key=True)
    # a foreign key to the user who makes this shopping
    shoppingUser_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    number = db.Column(db.Integer)
    # whether purchase or not (0 stands for false while 1 stands for true)
    status = db.Column(db.Integer, default=0)
    # relationship between user and shopping
    shopping_user = db.relationship('User', back_populates='shopping_product', lazy='joined')
    shopping_product = db.relationship('Products', back_populates='shopping_user', lazy='joined')

    def __repr__(self):
        return '<Shopping {}, {}>'.format(self.shoppingProduct_id, self.shoppingUser_id)


class Image(db.Model):
    __tablename__ = 'image'
    img_id = db.Column(db.Integer, primary_key=True)
    imgProduct_id = db.Column(db.String(32), db.ForeignKey('products.product_id'))
    img_path = db.Column(db.String(64), default="default.png")

    def __repr__(self):
        return '<Image {}, {}>'.format(self.img_id, self.imgProduct_id)

    def queryFromSecond(self, pro_id):
        return self.query.filter(Image.imgProduct_id == pro_id.product_id).all()[1:]


class OrderProduct(db.Model):
    # 中间表 用于多对多关系
    __tablename__ = 'orderproduct'
    id = db.Column(db.Integer, primary_key=True)
    middleProduct_id = db.Column(db.String(32), db.ForeignKey('products.product_id'))
    middleOrder_id = db.Column(db.String(32), db.ForeignKey('order.order_id'))
    number = db.Column(db.Integer)

    # can add another columns like types of product, color of product......


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    commentProduct_id = db.Column(db.String(32), db.ForeignKey('products.product_id'))
    commentUser_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    level = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String(128), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now())

    def avg(self, pro_id):
        comments = self.query.filter(commentProduct_id=pro_id).with_entities(func.avg(self.level)).all()
        return comments


class Order(db.Model):
    # serial number as primary key to identify a unique order
    order_id = db.Column(db.String(32), primary_key=True)
    create_time = db.Column(db.DateTime, default=datetime.now)
    total_cost = db.Column(db.Float, nullable=False)
    orderUser_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    order_state = db.Column(db.String(32))
    order_address = db.Column(db.String(32))
    order_phone = db.Column(db.String(24))
    order_consignee = db.Column(db.String(64))
    state_reason = db.Column(db.String(64))
    delivery = db.Column(db.String(64))
    priority = db.Column(db.String(64), default='No')

    products = db.relationship('OrderProduct', backref='order', lazy='dynamic')
    # relationship to OrderProduct
    # products = db.relationship('OrderProduct', foreign_keys=[OrderProduct.middleProduct_id],
    #                            backref=db.backref('order', lazy="joined"), lazy='dynamic')


class Products(db.Model):
    product_id = db.Column(db.String(32), primary_key=True)
    product_name = db.Column(db.String(20), index=True)
    name_chinese = db.Column(db.String(20), index=True)
    product_region = db.Column(db.String(64))
    product_classification = db.Column(db.String(64), index=True)
    product_price = db.Column(db.Float, index=True)
    product_description = db.Column(db.String(64))
    description_chinese = db.Column(db.String(64))
    product_path = db.Column(db.String(64))
    product_state = db.Column(db.String(64))
    product_inventory = db.Column(db.Integer)
    product_video = db.Column(db.String(64))

    # relationship to user that has this product in cart 
    shopping_user = db.relationship('Shopping', back_populates='shopping_product', lazy='dynamic')

    # relationship to image that this product has
    product_imgs = db.relationship('Image', backref='product', lazy='dynamic')

    # relationship to order
    orders = db.relationship('OrderProduct', backref='product', lazy='dynamic')

    # relationship to comment
    comments = db.relationship('Comment', backref='product', lazy='dynamic')

    def __repr__(self):
        return '<Products {}>'.format(self.product_name)

    def __count__(self, category):
        return len(Products.query.filter(Products.product_classification == category).all())

    # Goods table (mostly used in adding goods)

    def queryById(self, id):
        product = self.query.filter_by(product_id=id).first()
        if product is not None:
            return product
        else:
            return None


class Category(db.Model):
    category_language = db.Column(db.String(20))
    category_name = db.Column(db.String(20), primary_key=True)
    category_chinese = db.Column(db.String(20))

    def __repr__(self):
        return '{}'.format(self.category_name)


class Chat(db.Model):
    __tablename__ = 'chat'
    chat_id = db.Column(db.Integer, primary_key=True)
    message_type = db.Column(db.Integer, nullable=False)
    chat_message = db.Column(db.String(64), nullable=False)
    chat_time = db.Column(db.DateTime, nullable=False)
    chatroom = db.Column(db.String(32), nullable=False)
    read = db.Column(db.Integer)
    chatUser_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class State(db.Model):
    __tablename__ = 'state'
    state = db.Column(db.String(32), primary_key=True)


class Answer(db.Model):
    __tablename__ = 'answer'
    answer_id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(64), nullable=False)
    answer = db.Column(db.String(64), nullable=False)
    answer_chinese = db.Column(db.String(64), nullable=False)
    question_chinese = db.Column(db.String(64), nullable=False)
