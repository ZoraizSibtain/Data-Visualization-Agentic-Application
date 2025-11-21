import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from config.settings import DATABASE_URL
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_engine():
    return create_engine(DATABASE_URL)

def create_schema(engine):
    """Create the database schema and tables."""
    logger.info("Creating schema and tables...")
    
    with engine.connect() as conn:
        # Drop schema if exists
        conn.execute(text("DROP SCHEMA IF EXISTS robot_vacuum_depot CASCADE;"))
        conn.execute(text("CREATE SCHEMA robot_vacuum_depot;"))
        
        # Create Tables
        
        # Customer
        conn.execute(text("""
            CREATE TABLE robot_vacuum_depot."Customer"(
                "CustomerID" VARCHAR(40) PRIMARY KEY,
                "CustomerName" VARCHAR(120),
                "CustomerEmail" VARCHAR(120),
                "CustomerStreetAddress" VARCHAR(200),
                "CustomerZipCode" VARCHAR(20),
                "BillingZipCode" VARCHAR(20),
                "Segment" VARCHAR(60)
            );
        """))
        
        # Manufacturer
        conn.execute(text("""
            CREATE TABLE robot_vacuum_depot."Manufacturer"(
                "ManufacturerID" VARCHAR(40) PRIMARY KEY,
                "ManufacturerName" VARCHAR(120),
                "Country" VARCHAR(60),
                "LeadTimeDays" NUMERIC(10,2),
                "ReliabilityScore" NUMERIC(10,4)
            );
        """))
        
        # Product
        conn.execute(text("""
            CREATE TABLE robot_vacuum_depot."Product"(
                "ProductID" VARCHAR(40) PRIMARY KEY,
                "ProductName" VARCHAR(160),
                "ModelNumber" VARCHAR(80),
                "ManufacturerID" VARCHAR(40) REFERENCES robot_vacuum_depot."Manufacturer"("ManufacturerID"),
                "UnitPrice" NUMERIC(12,2),
                "ProductDescription" TEXT
            );
        """))
        
        # Warehouse
        conn.execute(text("""
            CREATE TABLE robot_vacuum_depot."Warehouse"(
                "WarehouseID" VARCHAR(40) PRIMARY KEY,
                "WarehouseStreetAddress" VARCHAR(200),
                "WarehouseZipCode" VARCHAR(20),
                "WarehouseCapacity" INT
            );
        """))
        
        # DistributionCenter
        conn.execute(text("""
            CREATE TABLE robot_vacuum_depot."DistributionCenter"(
                "DistributionCenterID" VARCHAR(40) PRIMARY KEY,
                "Region" VARCHAR(60),
                "DistributionCenterStreetAddress" VARCHAR(200),
                "DistributionCenterZipCode" VARCHAR(20),
                "FleetSize" INT
            );
        """))
        
        # WarehouseDistributionCenter
        conn.execute(text("""
            CREATE TABLE robot_vacuum_depot."WarehouseDistributionCenter"(
                "WarehouseID" VARCHAR(40) REFERENCES robot_vacuum_depot."Warehouse"("WarehouseID"),
                "DistributionCenterID" VARCHAR(40) REFERENCES robot_vacuum_depot."DistributionCenter"("DistributionCenterID"),
                PRIMARY KEY ("WarehouseID", "DistributionCenterID")
            );
        """))
        
        # WarehouseProductStock
        conn.execute(text("""
            CREATE TABLE robot_vacuum_depot."WarehouseProductStock"(
                "WarehouseID" VARCHAR(40) REFERENCES robot_vacuum_depot."Warehouse"("WarehouseID"),
                "ProductID" VARCHAR(40) REFERENCES robot_vacuum_depot."Product"("ProductID"),
                "StockLevel" INT,
                "RestockThreshold" INT,
                "LastRestockDate" TIMESTAMP,
                "LastUpdateDate" TIMESTAMP,
                PRIMARY KEY ("WarehouseID", "ProductID")
            );
        """))
        
        # Order
        conn.execute(text("""
            CREATE TABLE robot_vacuum_depot."Order"(
                "OrderID" VARCHAR(40) PRIMARY KEY,
                "CustomerID" VARCHAR(40) REFERENCES robot_vacuum_depot."Customer"("CustomerID"),
                "ProductID" VARCHAR(40) REFERENCES robot_vacuum_depot."Product"("ProductID"),
                "WarehouseID" VARCHAR(40) REFERENCES robot_vacuum_depot."Warehouse"("WarehouseID"),
                "DistributionCenterID" VARCHAR(40) REFERENCES robot_vacuum_depot."DistributionCenter"("DistributionCenterID"),
                "Quantity" INT,
                "UnitPrice" NUMERIC(12,2),
                "DiscountAmount" NUMERIC(12,2),
                "PromoCode" VARCHAR(80),
                "TaxAmount" NUMERIC(12,2),
                "ShippingCost" NUMERIC(12,2),
                "CostOfGoods" NUMERIC(12,2),
                "TotalAmount" NUMERIC(14,2),
                "OrderDate" TIMESTAMP,
                "ExpectedDeliveryDate" TIMESTAMP,
                "ActualDeliveryDate" TIMESTAMP,
                "DeliveryStatus" VARCHAR(40),
                "PaymentMethod" VARCHAR(20),
                "CardNumber" VARCHAR(30),
                "CardBrand" VARCHAR(40),
                "BillingZipCode" VARCHAR(20),
                "DeliveryStreetAddress" VARCHAR(200),
                "DeliveryZipCode" VARCHAR(20),
                "ShippingCarrier" VARCHAR(80)
            );
        """))
        
        # Review
        conn.execute(text("""
            CREATE TABLE robot_vacuum_depot."Review"(
                "ReviewID" VARCHAR(40) PRIMARY KEY,
                "OrderID" VARCHAR(40) REFERENCES robot_vacuum_depot."Order"("OrderID"),
                "CustomerID" VARCHAR(40) REFERENCES robot_vacuum_depot."Customer"("CustomerID"),
                "ProductID" VARCHAR(40) REFERENCES robot_vacuum_depot."Product"("ProductID"),
                "ProductRating" INT,
                "ReviewText" TEXT,
                "ReviewDate" TIMESTAMP,
                "ReviewSentiment" VARCHAR(20)
            );
        """))
        
        # Indexes
        logger.info("Creating indexes...")
        conn.execute(text('CREATE INDEX "idx_order_customer" ON robot_vacuum_depot."Order"("CustomerID");'))
        conn.execute(text('CREATE INDEX "idx_order_date" ON robot_vacuum_depot."Order"("OrderDate");'))
        conn.execute(text('CREATE INDEX "idx_order_status" ON robot_vacuum_depot."Order"("DeliveryStatus");'))
        conn.execute(text('CREATE INDEX "idx_review_product" ON robot_vacuum_depot."Review"("ProductID");'))
        conn.execute(text('CREATE INDEX "idx_product_manufacturer" ON robot_vacuum_depot."Product"("ManufacturerID");'))
        
        conn.commit()
        logger.info("Schema creation complete.")

def ingest_data(engine, csv_path):
    """Ingest data from CSV into the database."""
    logger.info(f"Reading CSV from {csv_path}...")
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return

    logger.info(f"Loaded {len(df)} rows. Processing data...")

    # Helper to clean and map columns
    def clean_col(col):
        return col.strip().lower()
    
    df.columns = [clean_col(c) for c in df.columns]
    
    # Date parsing
    date_cols = ['lastrestockdate', 'lastupdated', 'orderdate', 'expecteddeliverydate', 'actualdeliverydate', 'reviewdate']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Replace NaN with None for SQL insertion
    df = df.replace({np.nan: None})

    # Ensure all expected columns exist (some might be missing in CSV)
    expected_cols = [
        'country', 'costofgoods'
    ]
    for col in expected_cols:
        if col not in df.columns:
            logger.warning(f"Column '{col}' missing in CSV, filling with None")
            df[col] = None


    with engine.connect() as conn:
        # 1. Customer
        logger.info("Processing Customer table...")
        customer_cols = {
            'customerid': 'CustomerID',
            'customername': 'CustomerName',
            'customeremail': 'CustomerEmail',
            'customeraddress': 'CustomerStreetAddress',
            'customerzipcode': 'CustomerZipCode',
            'billingzipcode': 'BillingZipCode',
            'segment': 'Segment'
        }
        customers = df[list(customer_cols.keys())].rename(columns=customer_cols).drop_duplicates('CustomerID')
        customers.to_sql('Customer', conn, schema='robot_vacuum_depot', if_exists='append', index=False, method='multi', chunksize=1000)

        # 2. Manufacturer
        logger.info("Processing Manufacturer table...")
        mfg_cols = {
            'manufacturerid': 'ManufacturerID',
            'manufacturername': 'ManufacturerName',
            'country': 'Country',
            'leadtimedays': 'LeadTimeDays',
            'reliabilityscore': 'ReliabilityScore'
        }
        manufacturers = df[list(mfg_cols.keys())].rename(columns=mfg_cols).drop_duplicates('ManufacturerID')
        manufacturers.to_sql('Manufacturer', conn, schema='robot_vacuum_depot', if_exists='append', index=False, method='multi', chunksize=1000)

        # 3. Product
        logger.info("Processing Product table...")
        prod_cols = {
            'productid': 'ProductID',
            'productname': 'ProductName',
            'modelnumber': 'ModelNumber',
            'manufacturerid': 'ManufacturerID',
            'productprice': 'UnitPrice',
            'productdescription': 'ProductDescription'
        }
        products = df[list(prod_cols.keys())].rename(columns=prod_cols).drop_duplicates('ProductID')
        products.to_sql('Product', conn, schema='robot_vacuum_depot', if_exists='append', index=False, method='multi', chunksize=1000)

        # 4. Warehouse
        logger.info("Processing Warehouse table...")
        wh_cols = {
            'warehouseid': 'WarehouseID',
            'warehousestreetaddress': 'WarehouseStreetAddress',
            'warehousezipcode': 'WarehouseZipCode',
            'warehousecapacity': 'WarehouseCapacity'
        }
        warehouses = df[list(wh_cols.keys())].rename(columns=wh_cols).drop_duplicates('WarehouseID')
        warehouses.to_sql('Warehouse', conn, schema='robot_vacuum_depot', if_exists='append', index=False, method='multi', chunksize=1000)

        # 5. DistributionCenter
        logger.info("Processing DistributionCenter table...")
        dc_cols = {
            'distributioncenterid': 'DistributionCenterID',
            'region': 'Region',
            'distributioncenterstreetaddress': 'DistributionCenterStreetAddress',
            'distributioncenterzipcode': 'DistributionCenterZipCode',
            'fleetsize': 'FleetSize'
        }
        dcs = df[list(dc_cols.keys())].rename(columns=dc_cols).drop_duplicates('DistributionCenterID')
        dcs.to_sql('DistributionCenter', conn, schema='robot_vacuum_depot', if_exists='append', index=False, method='multi', chunksize=1000)

        # 6. WarehouseDistributionCenter
        logger.info("Processing WarehouseDistributionCenter table...")
        wdc_cols = {
            'warehouseid': 'WarehouseID',
            'distributioncenterid': 'DistributionCenterID'
        }
        wdc = df[list(wdc_cols.keys())].rename(columns=wdc_cols).drop_duplicates(['WarehouseID', 'DistributionCenterID'])
        wdc = wdc.dropna(subset=['WarehouseID', 'DistributionCenterID'])
        wdc.to_sql('WarehouseDistributionCenter', conn, schema='robot_vacuum_depot', if_exists='append', index=False, method='multi', chunksize=1000)

        # 7. WarehouseProductStock
        logger.info("Processing WarehouseProductStock table...")
        wps_cols = {
            'warehouseid': 'WarehouseID',
            'productid': 'ProductID',
            'stocklevel': 'StockLevel',
            'restockthreshold': 'RestockThreshold',
            'lastrestockdate': 'LastRestockDate',
            'lastupdated': 'LastUpdateDate'
        }
        wps = df[list(wps_cols.keys())].rename(columns=wps_cols).drop_duplicates(['WarehouseID', 'ProductID'])
        wps = wps.dropna(subset=['WarehouseID', 'ProductID'])
        wps.to_sql('WarehouseProductStock', conn, schema='robot_vacuum_depot', if_exists='append', index=False, method='multi', chunksize=1000)

        # 8. Order
        logger.info("Processing Order table...")
        order_cols = {
            'orderid': 'OrderID',
            'customerid': 'CustomerID',
            'productid': 'ProductID',
            'warehouseid': 'WarehouseID',
            'distributioncenterid': 'DistributionCenterID',
            'quantity': 'Quantity',
            'unitprice': 'UnitPrice',
            'discountamount': 'DiscountAmount',
            'promocode': 'PromoCode',
            'taxamount': 'TaxAmount',
            'shippingcost': 'ShippingCost',
            'costofgoods': 'CostOfGoods',
            'totalamount': 'TotalAmount',
            'orderdate': 'OrderDate',
            'expecteddeliverydate': 'ExpectedDeliveryDate',
            'actualdeliverydate': 'ActualDeliveryDate',
            'deliverystatus': 'DeliveryStatus',
            'paymentmethod': 'PaymentMethod',
            'cardnumber': 'CardNumber',
            'cardbrand': 'CardBrand',
            'billingzipcode': 'BillingZipCode',
            'deliveryaddress': 'DeliveryStreetAddress',
            'deliveryzipcode': 'DeliveryZipCode',
            'shippingcarrier': 'ShippingCarrier'
        }
        orders = df[list(order_cols.keys())].rename(columns=order_cols).drop_duplicates('OrderID')
        orders.to_sql('Order', conn, schema='robot_vacuum_depot', if_exists='append', index=False, method='multi', chunksize=1000)

        # 9. Review
        logger.info("Processing Review table...")
        review_cols = {
            'reviewid': 'ReviewID',
            'orderid': 'OrderID',
            'customerid': 'CustomerID',
            'productid': 'ProductID',
            'reviewrating': 'ProductRating',
            'reviewtext': 'ReviewText',
            'reviewdate': 'ReviewDate',
            'reviewsentiment': 'ReviewSentiment'
        }
        # Filter for rows where ReviewID is present
        reviews = df[df['reviewid'].notna()][list(review_cols.keys())].rename(columns=review_cols).drop_duplicates('ReviewID')
        reviews.to_sql('Review', conn, schema='robot_vacuum_depot', if_exists='append', index=False, method='multi', chunksize=1000)

        conn.commit()
        logger.info("Data ingestion complete!")

def main():
    engine = get_engine()
    
    # Path to CSV - located in src/RobotVacuumDepot_MasterData.csv
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "RobotVacuumDepot_MasterData.csv")
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found at {csv_path}")
        return

    create_schema(engine)
    ingest_data(engine, csv_path)

if __name__ == "__main__":
    main()
