"""
AutoKey Store - WTForms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, Optional, NumberRange


class RegisterForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[
        DataRequired(message='Vui lòng nhập tên đăng nhập.'),
        Length(min=3, max=80, message='Tên đăng nhập phải từ 3-80 ký tự.'),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Tên đăng nhập chỉ chứa chữ cái, số và dấu gạch dưới.')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Vui lòng nhập email.'),
        Email(message='Email không hợp lệ.'),
        Length(max=120, message='Email không được quá 120 ký tự.')
    ])
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu.'),
        Length(min=8, message='Mật khẩu phải có ít nhất 8 ký tự.'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$',
               message='Mật khẩu phải chứa ít nhất 1 chữ hoa, 1 chữ thường và 1 số.')
    ])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[
        DataRequired(message='Vui lòng xác nhận mật khẩu.'),
        EqualTo('password', message='Mật khẩu xác nhận không khớp.')
    ])
    terms = BooleanField('Đồng ý điều khoản', validators=[
        DataRequired(message='Bạn phải đồng ý với điều khoản sử dụng.')
    ])


class LoginForm(FlaskForm):
    username = StringField('Tên đăng nhập hoặc Email', validators=[
        DataRequired(message='Vui lòng nhập tên đăng nhập hoặc email.')
    ])
    password = PasswordField('Mật khẩu', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu.')
    ])


class ProductForm(FlaskForm):
    name = StringField('Tên sản phẩm', validators=[
        DataRequired(message='Vui lòng nhập tên sản phẩm.'),
        Length(max=200, message='Tên không được quá 200 ký tự.')
    ])
    slug = StringField('Slug (URL)', validators=[
        DataRequired(message='Vui lòng nhập slug.'),
        Length(max=200, message='Slug không được quá 200 ký tự.'),
        Regexp(r'^[a-z0-9-]+$', message='Slug chỉ chứa chữ thường, số và dấu gạch ngang.')
    ])
    description = TextAreaField('Mô tả')
    price = IntegerField('Giá (VND)', validators=[
        DataRequired(message='Vui lòng nhập giá.'),
        NumberRange(min=1000, message='Giá phải lớn hơn 1000 VND.')
    ])
    stock = IntegerField('Số lượng key', validators=[
        DataRequired(message='Vui lòng nhập số lượng.'),
        NumberRange(min=0, message='Số lượng không được âm.')
    ])
    category_id = SelectField('Danh mục', coerce=int, validators=[Optional()])
    is_active = BooleanField('Kích hoạt')


class CategoryForm(FlaskForm):
    name = StringField('Tên danh mục', validators=[
        DataRequired(message='Vui lòng nhập tên danh mục.'),
        Length(max=100, message='Tên không được quá 100 ký tự.')
    ])
    slug = StringField('Slug', validators=[
        DataRequired(message='Vui lòng nhập slug.'),
        Regexp(r'^[a-z0-9-]+$', message='Slug chỉ chứa chữ thường, số và dấu gạch ngang.')
    ])
    description = TextAreaField('Mô tả')
    is_active = BooleanField('Kích hoạt')
    sort_order = IntegerField('Thứ tự', validators=[Optional()])


class KeyAddForm(FlaskForm):
    keys_text = TextAreaField('Danh sách Keys (mỗi key một dòng)', validators=[
        DataRequired(message='Vui lòng nhập ít nhất một key.')
    ])


class ManualOrderForm(FlaskForm):
    user_id = SelectField('Khách hàng', coerce=int, validators=[DataRequired()])
    product_id = SelectField('Sản phẩm', coerce=int, validators=[DataRequired()])


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mật khẩu hiện tại', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu hiện tại.')
    ])
    password = PasswordField('Mật khẩu mới', validators=[
        DataRequired(message='Vui lòng nhập mật khẩu mới.'),
        Length(min=8, message='Mật khẩu mới phải có ít nhất 8 ký tự.'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$',
               message='Mật khẩu mới phải chứa ít nhất 1 chữ hoa, 1 chữ thường và 1 số.')
    ])
    confirm_password = PasswordField('Xác nhận mật khẩu mới', validators=[
        DataRequired(message='Vui lòng xác nhận mật khẩu mới.'),
        EqualTo('password', message='Mật khẩu xác nhận không khớp.')
    ])
