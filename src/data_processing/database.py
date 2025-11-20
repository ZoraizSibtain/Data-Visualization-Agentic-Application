import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# Database Connection URL
# Using default postgres credentials for local development as per plan
# In a real scenario, these would be environment variables
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "robot_vacuum_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

Base = declarative_base()

class Manufacturer(Base):
    __tablename__ = 'Manufacturer'
    ManufacturerID = Column(String, primary_key=True)
    ManufacturerName = Column(String, nullable=False)
    ReliabilityScore = Column(Float)

class Product(Base):
    __tablename__ = 'Product'
    ProductID = Column(String, primary_key=True)
    ProductName = Column(String, nullable=False)
    ProductDescription = Column(Text)
    ModelNumber = Column(String)
    ManufacturerID = Column(String, ForeignKey('Manufacturer.ManufacturerID'))
    ProductPrice = Column(Float)
    
    manufacturer = relationship("Manufacturer")

class Customer(Base):
    __tablename__ = 'Customer'
    CustomerID = Column(String, primary_key=True)
    CustomerName = Column(String, nullable=False)
    CustomerEmail = Column(String)
    CustomerZipCode = Column(String)
    CustomerAddress = Column(String)
    Segment = Column(String)

class Warehouse(Base):
    __tablename__ = 'Warehouse'
    WarehouseID = Column(String, primary_key=True)
    WarehouseStreetAddress = Column(String)
    WarehouseZipCode = Column(String)
    WarehouseCapacity = Column(Integer)

class DistributionCenter(Base):
    __tablename__ = 'DistributionCenter'
    DistributionCenterID = Column(String, primary_key=True)
    DistributionCenterStreetAddress = Column(String)
    DistributionCenterZipCode = Column(String)
    FleetSize = Column(Integer)

class Order(Base):
    __tablename__ = 'Order'
    OrderID = Column(String, primary_key=True)
    OrderDate = Column(DateTime)
    CustomerID = Column(String, ForeignKey('Customer.CustomerID'))
    ProductID = Column(String, ForeignKey('Product.ProductID'))
    DeliveryStatus = Column(String)
    DeliveryAddress = Column(String)
    DeliveryZipCode = Column(String)
    ShippingCost = Column(Float)
    ShippingCarrier = Column(String)
    TotalAmount = Column(Float)
    TaxAmount = Column(Float)
    DiscountAmount = Column(Float)
    Quantity = Column(Integer)
    PaymentMethod = Column(String)
    ExpectedDeliveryDate = Column(DateTime)
    ActualDeliveryDate = Column(DateTime)
    
    customer = relationship("Customer")
    product = relationship("Product")

class Review(Base):
    __tablename__ = 'Review'
    ReviewID = Column(String, primary_key=True)
    OrderID = Column(String, ForeignKey('Order.OrderID'))
    ReviewRating = Column(Integer)
    ReviewText = Column(Text)
    ReviewDate = Column(DateTime)
    ReviewSentiment = Column(String)
    
    order = relationship("Order")

class WarehouseProductStock(Base):
    __tablename__ = 'WarehouseProductStock'
    WarehouseID = Column(String, ForeignKey('Warehouse.WarehouseID'), primary_key=True)
    ProductID = Column(String, ForeignKey('Product.ProductID'), primary_key=True)
    StockLevel = Column(Integer)
    RestockThreshold = Column(Integer)
    LastRestockDate = Column(DateTime)
    
    warehouse = relationship("Warehouse")
    product = relationship("Product")

class WarehouseDistributionCenter(Base):
    __tablename__ = 'WarehouseDistributionCenter'
    WarehouseID = Column(String, ForeignKey('Warehouse.WarehouseID'), primary_key=True)
    DistributionCenterID = Column(String, ForeignKey('DistributionCenter.DistributionCenterID'), primary_key=True)
    LeadTimeDays = Column(Integer)
    
    warehouse = relationship("Warehouse")
    distribution_center = relationship("DistributionCenter")

def get_engine():
    return create_engine(DATABASE_URL)

def get_session_factory(engine):
    return sessionmaker(bind=engine)

def create_tables(engine):
    Base.metadata.create_all(engine)
