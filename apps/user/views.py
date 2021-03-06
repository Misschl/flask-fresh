import time

from flask.views import MethodView
from flask import session, render_template, url_for, redirect, Response
from sqlalchemy import desc

from apps.goods.models import GoodsSKU
from apps.order.models import OrderInfo, OrderGoods
from utils.extentions import db
from utils.tools import get_redis_connection
from .models import User, Address
from itsdangerous import JSONWebSignatureSerializer as Serializer, BadSignature
import re
from config import SECRET_KEY
from utils.tasks import send_register_mail
from utils.auth import login, logout, request, login_required


class RegisterView(MethodView):
    def get(self):
        return render_template('register.html')

    def post(self):
        username = request.form.get('username')
        password = request.form.get('pwd')
        email = request.form.get('email')

        if not all([username, password, email]):
            return render_template('register.html', errmsg='数据不完整!')

        allow = request.form.get('allow')
        if allow != 'on':
            return render_template('register.html', **{'errmsg': '请同意协议!'})

        reg = "[\w!#$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?"
        if not re.match(reg, email):
            return render_template('register.html', **{'errmsg': '邮箱不合法!'})

        if db.session.query(User).filter(User.username == username).first():
            return render_template('register.html', **{'errmsg': '用户名已被注册!'})

        if db.session.query(User).filter(User.email == email).first():
            return render_template('register.html', **{'errmsg': '邮箱已被注册!'})

        user = User(username=username, password=password, email=email)
        db.session.add(user)
        db.session.commit()

        serializer = Serializer(SECRET_KEY)
        data = {'id': user.id, 'time': time.time()}
        token = serializer.dumps(data).decode()

        send_register_mail(email, username, token)

        return redirect(url_for('user.login'))


class LoginView(MethodView):
    def get(self):
        username = request.cookies.get('username', '')

        checked = 'checked' if username else ''

        return render_template('login.html', **{'username': username, 'checked': checked})

    def post(self):
        username = request.form.get('username')
        password = request.form.get('pwd')
        if not all([username, password]):
            return render_template('login.html', **{'errmsg': '数据不完整!'})

        user = User.authenticated(username=username, password=password)

        if not user:
            return render_template('login.html', **{'errmsg': '用户名或密码错误!'})

        if user.active is False:
            return render_template('login.html', **{'errmsg': '用户未激活!'})

        login(user)

        next_url = request.args.get('next', url_for('goods.index'))

        response = redirect(next_url)

        remember = request.form.get('remember')

        if remember == 'on':
            response.set_cookie('username', username, max_age=7 * 24 * 3600)
        else:
            response.delete_cookie('username')

        return response


class ActiveView(MethodView):

    def get(self, token):
        serializer = Serializer(SECRET_KEY)
        try:
            data = serializer.loads(token.encode())
            user_id = data.get('id')
            user = db.session.query(User).filter(User.id == user_id).first()
            user.active = True
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('user.login'))
        except BadSignature:
            return Response('错误的请求链接!', status=403)


class LogoutView(MethodView):
    def get(self):
        logout()
        return redirect(url_for('user.login'))


class AddressView(MethodView):
    decorators = [login_required]

    def get(self):
        # 获取用户的默认收货地址
        user = request.user

        # address = db.session.query(Address).filter(Address._user == user, Address.is_default == True).first()
        address = Address.query.filter(Address._user == user, Address.is_default == True).first()

        return render_template('user_center_site.html', **{'page': 'address', 'address': address, 'user': user})

    def post(self):
        '''地址的添加'''
        # 接受数据
        receiver = request.form.get('receiver')
        addr = request.form.get('addr')
        zip_code = request.form.get('zip_code')
        phone = request.form.get('phone')
        # 校验数据
        if not all([receiver, addr, phone]):
            return render_template('user_center_site.html', errmsg="数据不完整!")
        reg = '1([38][0-9]|4[579]|5[0-3,5-9]|6[6]|7[0135678]|9[89])\d{8}'
        if not re.match(reg, phone):
            return render_template('user_center_site.html', **{'page': 'address', 'errmsg': '手机号码格式错误!'})
        # 业务处理 地址添加
        user = request.user
        address = db.session.query(Address).filter(Address._user == user, Address.is_default == True).first()
        # 查询有没有默认地址，没有就将当前的数据添加为默认收货地址
        is_default = False if address else True

        course = Address(addr=addr, phone=phone, receiver=receiver, is_default=is_default, zip_code=zip_code)
        course._user = user
        db.session.add(course)
        db.session.commit()
        # 返回应答
        return redirect(url_for('user.address'))


class UserInfoView(MethodView):
    decorators = [login_required]

    def get(self):
        # 获取个人信息
        # address = Address.objects.get_default_address(request.user)
        address = db.session.query(Address).filter(Address.is_default == True, Address._user == request.user).first()
        # 获取浏览记录
        conn = get_redis_connection()

        history_key = 'history_%d' % request.user.id

        sku_ids = conn.lrange(history_key, 0, 4)

        goods_list = []

        # 历史浏览记录排序
        for sku_id in sku_ids:
            # goods = GoodsSKU.objects.get(pk=sku_id)
            goods = db.session.query(GoodsSKU).filter(GoodsSKU.id == sku_id).first()
            goods_list.append(goods)

        context = {
            'page': 'user',
            'address': address,
            'goods_list': goods_list,
            'user': request.user
        }
        conn.close()
        return render_template('user_center_info.html', **context)


class UserOrderView(MethodView):
    decorators = [login_required]

    def get(self, page):
        # 获取用户的订单信息
        user = request.user

        # orders = OrderInfo.objects.filter(user=user).order_by('-create_time')
        orders = OrderInfo.query.filter(OrderInfo._user == user).order_by(desc(OrderInfo.id)).all()
        print(orders)
        for order in orders:
            # order_skus = OrderGoods.objects.filter(order_id=order.order_id)
            order_skus = OrderGoods.query.filter(OrderGoods._order == order).all()
            print(order_skus)
            for order_sku in order_skus:
                amount = order_sku.count * order_sku.price
                order_sku.amount = amount
                print(order_sku.amount)

            order.order_skus = order_skus
            order.status_name = OrderInfo.ORDER_STATUS[order.order_status]
        """ 分页先放置
        paginator = orders.paginate(page, 8, False)

        # 对页码进行容错处理
        try:
            page = int(page)
        except Exception:
            page = 1

        if page > paginator.pages:
            pages = paginator.pages

        order_page = paginator.items

        # TODO 页码控制
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages + 1)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)
        """

        context = {
            'order_page': orders,
            # 'pages': pages,
            'page': 'order',
            'user': user
        }

        return render_template('user_center_order.html', **context)
