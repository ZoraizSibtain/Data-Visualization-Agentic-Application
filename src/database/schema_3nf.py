from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Manufacturer(Base):
    __tablename__ = 'manufacturer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    country = Column(String(100))

    products = relationship("Product", back_populates="manufacturer")


class Product(Base):
    __tablename__ = 'product'

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    price = Column(Float)
    cost = Column(Float)
    manufacturer_id = Column(Integer, ForeignKey('manufacturer.id'))

    manufacturer = relationship("Manufacturer", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    inventory = relationship("Inventory", back_populates="product")


class Warehouse(Base):
    __tablename__ = 'warehouse'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    location = Column(String(200))
    capacity = Column(Integer)

    inventory = relationship("Inventory", back_populates="warehouse")
    shipments = relationship("Shipment", back_populates="warehouse")


class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('product.id'))
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'))
    quantity = Column(Integer, default=0)
    restock_threshold = Column(Integer, default=10)

    product = relationship("Product", back_populates="inventory")
    warehouse = relationship("Warehouse", back_populates="inventory")


class Customer(Base):
    __tablename__ = 'customer'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(200), unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(50))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    __tablename__ = 'order'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey('customer.id'))
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float)
    status = Column(String(50))

    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")
    shipment = relationship("Shipment", back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = 'order_item'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('order.id'))
    product_id = Column(Integer, ForeignKey('product.id'))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)
    discount = Column(Float, default=0)

    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class Shipment(Base):
    __tablename__ = 'shipment'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('order.id'), unique=True)
    warehouse_id = Column(Integer, ForeignKey('warehouse.id'))
    carrier = Column(String(100))
    tracking_number = Column(String(100))
    ship_date = Column(DateTime)
    delivery_date = Column(DateTime)
    delivery_status = Column(String(50))
    shipping_cost = Column(Float)

    order = relationship("Order", back_populates="shipment")
    warehouse = relationship("Warehouse", back_populates="shipments")


class Review(Base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('product.id'))
    customer_id = Column(Integer, ForeignKey('customer.id'))
    rating = Column(Integer)
    review_text = Column(Text)
    review_date = Column(DateTime, default=datetime.utcnow)
