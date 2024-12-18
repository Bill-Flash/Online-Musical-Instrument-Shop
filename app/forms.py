import re

from flask import request
from wtforms import Form
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FileField, IntegerField, \
    SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp

class CreateMIForm(Form):
    proname = StringField('proname', validators=[DataRequired()])
    proname2 = StringField('proname2', validators=[DataRequired()])
    description = TextAreaField('description')
    description2 = TextAreaField('description2')
    states = [("Published", "Published"), ("Removed", "Removed")]
    state = SelectField('state', validators=[DataRequired()], choices=states)
    types1 = [("Western", "Western"), ("Chinese", "Chinese")]
    type1 = SelectField('type1', validators=[DataRequired()], choices=types1)
    type2 = SelectField('type2', validators=[DataRequired()])
    price = StringField('price', validators=[DataRequired()])
    inventory = StringField('inventory', validators=[DataRequired()])
    poster = FileField('poster', render_kw={"class": "input"})
    video = FileField('video')

    submit = SubmitField('Create', render_kw={"class": "createButton"})
    def validate_inventory(form, field):
        num = field.data
        if re.match('0',num) and len(num)>1:
            print('false inventory')
            raise ValidationError("false inventory")
class CreateTypeForm(FlaskForm):
    caname = StringField('caname', validators=[DataRequired()])
    chiname = StringField('chiname', validators=[DataRequired()])
    types = [("Western", "Western"), ["Chinese", "Chinese"]]
    type = SelectField('type', validators=[DataRequired()], choices=types)
    submit = SubmitField('Create', render_kw={"class": "createButton"})

class DeleteTypeForm(FlaskForm):
    types = [("Piano", "Piano"), ("Guitar", "Guitar")]
    type = SelectField('type', validators=[DataRequired()], choices=types)
    submit = SubmitField('Create', render_kw={"class": "createButton"})

class ModifyOrderForm(FlaskForm):
    rec_name = StringField('rec_name', validators=[DataRequired()])
    phone_number = StringField('phone_number', validators=[DataRequired()])
    address = StringField('address', validators=[DataRequired()])
    states = [("Paid(delivery)","Paid(delivery)"),("Paid(picking up)","Paid(picking up)"),
              ("Delivery","Delivery"),("Canceled","Canceled"),
              ("Exception","Exception"),("Finished","Finished")]
    state = SelectField('type2',choices=states)
    priorities = [("Yes","Yes"),("No","No")]
    priority = SelectField('priority', validators=[DataRequired()],choices=priorities)
    reason = TextAreaField('reason')
    submit = SubmitField('Modify')

class ClosedOrderForm(FlaskForm):
    rec_name = StringField('rec_name', validators=[DataRequired()])
    phone_number = StringField('phone_number', validators=[DataRequired()])
    address = StringField('address', validators=[DataRequired()])
    states = [("Paid(delivery)","Paid(delivery)"),
              ("Delivery","Delivery"),("Canceled","Canceled"),
              ("Exception","Exception"),("Finished","Finished")]
    state = SelectField('type2',validators=[DataRequired()], choices=states)
    priorities = [("Yes","Yes"),("No","No")]
    priority = SelectField('priority', validators=[DataRequired()],choices=priorities)
    reason = TextAreaField('reason')
    submit = SubmitField('Modify')

class AddReplyForm(FlaskForm):
    question = StringField('question', validators=[DataRequired()])
    answer = StringField('answer', validators=[DataRequired()])
    submit = SubmitField('Create', render_kw={"class": "createButton"})




