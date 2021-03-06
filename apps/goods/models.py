# -*-coding:utf-8-*-
from sqlalchemy.orm import relationship

from utils.extentions import db


class GoodsType(db.Model):
    """商品类型模型类"""
    __tablename__ = 'df_goods_type'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20))
    logo = db.Column(db.String(20))
    image = db.Column(db.String(255))

    def __str__(self):
        return self.name


class GoodsSKU(db.Model):
    """商品SKU模型类"""
    __tablename__ = 'df_goods_sku'
    status_choices = (
        (0, '下线'),
        (1, '上线')
    )
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.Integer, db.ForeignKey('df_goods_type.id', ondelete='CASCADE'))
    goods = db.Column(db.Integer, db.ForeignKey('df_goods.id', ondelete='CASCADE'))
    name = db.Column(db.String(20))
    desc = db.Column(db.String(256))
    price = db.Column(db.DECIMAL)
    unite = db.Column(db.String(20))
    image = db.Column(db.String(255))
    stock = db.Column(db.Integer)
    sales = db.Column(db.Integer, default=0)
    status = db.Column(db.SmallInteger, default=1)

    _goods_type = relationship('GoodsType', backref='good_sku')
    _goods = relationship('GoodsModel', backref='good_sku')


class GoodsModel(db.Model):
    """商品SPU模型类"""
    __tablename__ = 'df_goods'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # name = models.CharField(max_length=20, verbose_name='商品SPU名称')
    name = db.Column(db.String(20))
    # 富文本类型：带有格式的文本
    # detail = HTMLField(blank=True, verbose_name='商品详情')
    detail = db.Column(db.Text)

    def __str__(self):
        return self.name


class GoodsImage(db.Model):
    """商品图片模型类"""
    __tablename__ = 'df_goods_image'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # sku = models.ForeignKey('GoodsSKU', on_delete=models.CASCADE, verbose_name='商品')
    sku = db.Column(db.ForeignKey('df_goods_sku.id', ondelete='CASCADE'))
    # image = models.ImageField(upload_to='goods', verbose_name='图片路径')
    image = db.Column(db.String(255))

    _sku = relationship('GoodsSKU', backref='goods_image')


class IndexGoodsBanner(db.Model):
    """首页轮播商品展示模型类"""
    __tablename__ = 'df_index_banner'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # sku = models.ForeignKey('GoodsSKU', on_delete=models.CASCADE, verbose_name='商品')
    sku = db.Column(db.ForeignKey('df_goods_sku.id', ondelete='CASCADE'))
    # image = models.ImageField(upload_to='banner', verbose_name='图片')
    image = db.Column(db.String(255))
    # index = models.SmallIntegerField(default=0, verbose_name='展示顺序')
    index = db.Column(db.SmallInteger, default=0)

    _sku = relationship('GoodsSKU', backref='index_goods_banner')

#
#     class Meta:
#         db_table = 'df_index_banner'
#         verbose_name = '首页轮播商品'
#         verbose_name_plural = verbose_name
#
#     def __str__(self):
#         return self.sku.name
#
#
class IndexTypeGoodsBanner(db.Model):
    """首页分类商品展示模型类"""
    DISPLAY_TYPE_CHOICES = (
        (0, '标题'),
        (1, '图片')
    )
    __tablename__ = 'df_index_type_goods'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # type = models.ForeignKey('GoodsType', on_delete=models.CASCADE, verbose_name='商品类型')
    type = db.Column(db.ForeignKey('df_goods_type.id', ondelete='CASCADE'))
    # sku = models.ForeignKey('GoodsSKU', on_delete=models.CASCADE, verbose_name='商品SKU')
    sku = db.Column(db.ForeignKey('df_goods_sku.id', ondelete='CASCADE'))
    # display_type = models.SmallIntegerField(default=1, choices=DISPLAY_TYPE_CHOICES, verbose_name='展示类型')
    display_type = db.Column(db.SmallInteger, default=1)
    # index = models.SmallIntegerField(default=1, verbose_name='展示顺序')
    index = db.Column(db.SmallInteger, default=1)
#
    _type = relationship('GoodsType', backref='index_type_goods_banner')
    _sku = relationship('GoodsSKU', backref='index_type_goods_banner')
#     class Meta:
#         db_table = 'df_index_type_goods'
#         verbose_name = '主页分类展示商品'
#         verbose_name_plural = verbose_name
#
#     def __str__(self):
#         return self.sku.name
#
#
class IndexPromotionBanner(db.Model):
    """首页促销活动模型类"""
    __tablename__ = 'df_index_promotion'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # name = models.CharField(max_length=20, verbose_name='活动名称')
    name = db.Column(db.String(20))
    # url = models.CharField(max_length=256, verbose_name='活动链接')
    url = db.Column(db.String(255))
    # image = models.ImageField(upload_to='banner', verbose_name='活动图片')
    image = db.Column(db.String(255))
    # index = models.SmallIntegerField(default=0, verbose_name='展示顺序')
    index = db.Column(db.SmallInteger, default=1)
#
#     class Meta:
#         db_table = 'df_index_promotion'
#         verbose_name = '主页促销活动'
#         verbose_name_plural = verbose_name
#
#     def __str__(self):
#         return self.name
