import polars as pl
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import ProgrammingError
import os
from datetime import datetime
from .database import (
    Base, Manufacturer, Product, Customer, Warehouse, DistributionCenter,
    Order, Review, WarehouseProductStock, WarehouseDistributionCenter,
    DATABASE_URL, DB_NAME
)

def create_database_if_not_exists():
    # Connect to default 'postgres' db to create the target db
    default_url = DATABASE_URL.rsplit('/', 1)[0] + '/postgres'
    engine = create_engine(default_url, isolation_level='AUTOCOMMIT')
    
    try:
        with engine.connect() as conn:
            # Check if db exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'"))
            if not result.fetchone():
                print(f"Creating database {DB_NAME}...")
                conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
            else:
                print(f"Database {DB_NAME} already exists.")
    except Exception as e:
        print(f"Warning: Could not check/create database. It might already exist or credentials might be wrong. Error: {e}")

def clean_date(date_str):
    if date_str is None:
        return None
    try:
        # Attempt to parse date with time
        return datetime.strptime(date_str, '%m/%d/%Y %H:%M')
    except ValueError:
        try:
            # Attempt to parse date without time
            return datetime.strptime(date_str, '%m/%d/%Y')
        except ValueError:
            return None

def load_data(csv_path):
    print(f"Loading data from {csv_path}...")
    df = pl.read_csv(csv_path, ignore_errors=True)
    
    # Convert to pandas for easier iteration/handling if needed, or use polars directly
    # For this size, pandas is fine after polars load
    pdf = df.to_pandas()
    
    # Connect to the target database
    engine = create_engine(DATABASE_URL)
    print("Resetting database schema...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Manufacturers
        print("Processing Manufacturers...")
        manufacturers = pdf[['ManufacturerID', 'ManufacturerName', 'ReliabilityScore']].drop_duplicates(subset=['ManufacturerID'])
        for _, row in manufacturers.iterrows():
            session.merge(Manufacturer(
                ManufacturerID=row['ManufacturerID'],
                ManufacturerName=row['ManufacturerName'],
                ReliabilityScore=row['ReliabilityScore']
            ))
        
        # 2. Products
        print("Processing Products...")
        products = pdf[['ProductID', 'ProductName', 'ProductDescription', 'ModelNumber', 'ManufacturerID', 'ProductPrice']].drop_duplicates(subset=['ProductID'])
        for _, row in products.iterrows():
            session.merge(Product(
                ProductID=row['ProductID'],
                ProductName=row['ProductName'],
                ProductDescription=row['ProductDescription'],
                ModelNumber=row['ModelNumber'],
                ManufacturerID=row['ManufacturerID'],
                ProductPrice=row['ProductPrice']
            ))
            
        # 3. Customers
        print("Processing Customers...")
        customers = pdf[['CustomerID', 'CustomerName', 'CustomerEmail', 'CustomerZipCode', 'CustomerAddress', 'Segment']].drop_duplicates(subset=['CustomerID'])
        for _, row in customers.iterrows():
            session.merge(Customer(
                CustomerID=row['CustomerID'],
                CustomerName=row['CustomerName'],
                CustomerEmail=row['CustomerEmail'],
                CustomerZipCode=str(row['CustomerZipCode']),
                CustomerAddress=row['CustomerAddress'],
                Segment=row['Segment']
            ))
            
        # 4. Warehouses
        print("Processing Warehouses...")
        warehouses = pdf[['WarehouseID', 'WarehouseStreetAddress', 'WarehouseZipCode', 'WarehouseCapacity']].drop_duplicates(subset=['WarehouseID'])
        for _, row in warehouses.iterrows():
            session.merge(Warehouse(
                WarehouseID=row['WarehouseID'],
                WarehouseStreetAddress=row['WarehouseStreetAddress'],
                WarehouseZipCode=str(row['WarehouseZipCode']),
                WarehouseCapacity=row['WarehouseCapacity']
            ))
            
        # 5. DistributionCenters
        print("Processing DistributionCenters...")
        dcs = pdf[['DistributionCenterID', 'DistributionCenterStreetAddress', 'DistributionCenterZipCode', 'FleetSize']].drop_duplicates(subset=['DistributionCenterID'])
        for _, row in dcs.iterrows():
            session.merge(DistributionCenter(
                DistributionCenterID=row['DistributionCenterID'],
                DistributionCenterStreetAddress=row['DistributionCenterStreetAddress'],
                DistributionCenterZipCode=str(row['DistributionCenterZipCode']),
                FleetSize=row['FleetSize']
            ))
            
        # 6. Orders
        print("Processing Orders...")
        orders = pdf[['OrderID', 'OrderDate', 'CustomerID', 'ProductID', 'DeliveryStatus', 'DeliveryAddress', 'DeliveryZipCode', 'ShippingCost', 'ShippingCarrier', 'TotalAmount', 'TaxAmount', 'DiscountAmount', 'Quantity', 'PaymentMethod', 'ExpectedDeliveryDate', 'ActualDeliveryDate']].drop_duplicates(subset=['OrderID'])
        for _, row in orders.iterrows():
            session.merge(Order(
                OrderID=row['OrderID'],
                OrderDate=clean_date(row['OrderDate']),
                CustomerID=row['CustomerID'],
                ProductID=row['ProductID'],
                DeliveryStatus=row['DeliveryStatus'],
                DeliveryAddress=row['DeliveryAddress'],
                DeliveryZipCode=str(row['DeliveryZipCode']),
                ShippingCost=row['ShippingCost'],
                ShippingCarrier=row['ShippingCarrier'],
                TotalAmount=row['TotalAmount'],
                TaxAmount=row['TaxAmount'],
                DiscountAmount=row['DiscountAmount'],
                Quantity=row['Quantity'],
                PaymentMethod=row['PaymentMethod'],
                ExpectedDeliveryDate=clean_date(row['ExpectedDeliveryDate']),
                ActualDeliveryDate=clean_date(row['ActualDeliveryDate'])
            ))
            
        # 7. Reviews
        print("Processing Reviews...")
        reviews = pdf[['ReviewID', 'OrderID', 'ReviewRating', 'ReviewText', 'ReviewDate', 'ReviewSentiment']].dropna(subset=['ReviewID']).drop_duplicates(subset=['ReviewID'])
        for _, row in reviews.iterrows():
            session.merge(Review(
                ReviewID=row['ReviewID'],
                OrderID=row['OrderID'],
                ReviewRating=row['ReviewRating'],
                ReviewText=row['ReviewText'],
                ReviewDate=clean_date(row['ReviewDate']),
                ReviewSentiment=row['ReviewSentiment']
            ))
            
        # 8. WarehouseProductStock
        print("Processing WarehouseProductStock...")
        stock = pdf[['WarehouseID', 'ProductID', 'StockLevel', 'RestockThreshold', 'LastRestockDate']].drop_duplicates(subset=['WarehouseID', 'ProductID'])
        for _, row in stock.iterrows():
            session.merge(WarehouseProductStock(
                WarehouseID=row['WarehouseID'],
                ProductID=row['ProductID'],
                StockLevel=row['StockLevel'],
                RestockThreshold=row['RestockThreshold'],
                LastRestockDate=clean_date(row['LastRestockDate'])
            ))
            
        # 9. WarehouseDistributionCenter
        print("Processing WarehouseDistributionCenter...")
        # Assuming the relationship is defined by the unique pairs in the dataset
        wdc = pdf[['WarehouseID', 'DistributionCenterID', 'LeadTimeDays']].drop_duplicates(subset=['WarehouseID', 'DistributionCenterID'])
        for _, row in wdc.iterrows():
            session.merge(WarehouseDistributionCenter(
                WarehouseID=row['WarehouseID'],
                DistributionCenterID=row['DistributionCenterID'],
                LeadTimeDays=row['LeadTimeDays']
            ))
            
        session.commit()
        print("Data loading complete!")
        
    except Exception as e:
        session.rollback()
        print(f"Error loading data: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    create_database_if_not_exists()
    load_data("/Users/zibtain/Downloads/Assignment_3/RobotVacuumDepot_MasterData.csv")
