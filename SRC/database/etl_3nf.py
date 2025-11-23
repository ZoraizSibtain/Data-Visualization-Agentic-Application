import polars as pl
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL
from .schema_3nf import Base, Manufacturer, Product, Warehouse, Inventory, Customer, Order, OrderItem, Shipment, Review, DatasetVersion


class ETLPipeline:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(self.database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def create_tables(self):
        """Create all tables defined in schema_3nf."""
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """Drop all tables."""
        Base.metadata.drop_all(self.engine)

    def transform_and_load(self, csv_path: str):
        """Transform denormalized CSV data into 3NF tables using Polars."""
        # Read CSV with Polars
        df = pl.read_csv(csv_path, ignore_errors=True)
        
        # Clean column names - lowercase with underscores
        new_columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
        df.columns = new_columns

        print(f"Loaded {len(df)} rows from CSV using Polars")
        print(f"Columns: {df.columns}")

        # Record dataset version
        self._record_version(csv_path, len(df))

        # Extract and load manufacturers
        self._load_manufacturers(df)

        # Extract and load warehouses
        self._load_warehouses(df)

        # Extract and load products
        self._load_products(df)

        # Extract and load inventory
        self._load_inventory(df)

        # Extract and load customers
        self._load_customers(df)

        # Extract and load orders
        self._load_orders(df)

        # Extract and load order items
        self._load_order_items(df)

        # Extract and load shipments
        self._load_shipments(df)

        # Extract and load reviews
        self._load_reviews(df)

        self.session.commit()
        print("ETL complete!")

    def _record_version(self, csv_path: str, row_count: int):
        """Record the dataset version."""
        version = DatasetVersion(
            filename=os.path.basename(csv_path),
            row_count=row_count,
            description="Initial load"
        )
        self.session.add(version)
        self.session.commit()

    def _load_manufacturers(self, df: pl.DataFrame):
        """Extract unique manufacturers and load to database."""
        if 'manufacturername' not in df.columns:
            print("No manufacturername column found")
            return

        manufacturers = (
            df.select(pl.col('manufacturername').alias('name'))
            .unique()
            .with_columns(pl.lit(None).alias('country'))
            .filter(pl.col('name').is_not_null())
        )

        print(f"Loading {len(manufacturers)} manufacturers")
        # Convert to pandas for SQL insertion (SQLAlchemy compatibility)
        manufacturers.to_pandas().to_sql('manufacturer', self.engine, if_exists='append', index=False)

    def _load_warehouses(self, df: pl.DataFrame):
        """Extract unique warehouses and load to database."""
        if 'warehouseid' not in df.columns:
            print("No warehouseid column found")
            return

        warehouse_cols = ['warehouseid', 'warehousestreetaddress', 'warehousezipcode', 'warehousecapacity']
        available_cols = [c for c in warehouse_cols if c in df.columns]

        warehouses = (
            df.select(available_cols)
            .unique(subset=['warehouseid'])
            .rename({
                'warehouseid': 'name',
                'warehousestreetaddress': 'location',
                'warehousecapacity': 'capacity'
            })
            .select(['name', 'location', 'capacity'])
            .filter(pl.col('name').is_not_null())
        )

        print(f"Loading {len(warehouses)} warehouses")
        warehouses.to_pandas().to_sql('warehouse', self.engine, if_exists='append', index=False)

    def _load_products(self, df: pl.DataFrame):
        """Extract unique products and load to database."""
        if 'productid' not in df.columns:
            print("No productid column found")
            return

        product_cols = ['productid', 'productname', 'productprice', 'unitprice']
        available_cols = [c for c in product_cols if c in df.columns]

        # Get manufacturer IDs
        mfr_map_df = pd.read_sql("SELECT id, name FROM manufacturer", self.engine)
        # Convert to Polars for join
        mfr_map = pl.from_pandas(mfr_map_df).rename({'id': 'manufacturer_id', 'name': 'manufacturername'})

        products = (
            df.select(available_cols + ['manufacturername'])
            .unique(subset=['productid'])
            .join(mfr_map, on='manufacturername', how='left')
            .rename({
                'productid': 'sku',
                'productname': 'name',
                'productprice': 'price',
                'unitprice': 'cost'
            })
            .select(['sku', 'name', 'price', 'cost', 'manufacturer_id'])
            .filter(pl.col('sku').is_not_null())
        )

        print(f"Loading {len(products)} products")
        products.to_pandas().to_sql('product', self.engine, if_exists='append', index=False)

    def _load_inventory(self, df: pl.DataFrame):
        """Load inventory data."""
        if 'productid' not in df.columns or 'warehouseid' not in df.columns:
            print("Missing productid or warehouseid columns")
            return

        inv_cols = ['productid', 'warehouseid', 'stocklevel', 'restockthreshold']
        available_cols = [c for c in inv_cols if c in df.columns]

        # Get IDs
        prod_map = pl.from_pandas(pd.read_sql("SELECT id, sku FROM product", self.engine)).rename({'id': 'product_id', 'sku': 'productid'})
        wh_map = pl.from_pandas(pd.read_sql("SELECT id, name FROM warehouse", self.engine)).rename({'id': 'warehouse_id', 'name': 'warehouseid'})

        inventory = (
            df.select(available_cols)
            .unique(subset=['productid', 'warehouseid'])
            .join(prod_map, on='productid', how='left')
            .join(wh_map, on='warehouseid', how='left')
            .rename({
                'stocklevel': 'quantity',
                'restockthreshold': 'restock_threshold'
            })
            .select(['product_id', 'warehouse_id', 'quantity', 'restock_threshold'])
            .filter(pl.col('product_id').is_not_null() & pl.col('warehouse_id').is_not_null())
        )

        print(f"Loading {len(inventory)} inventory records")
        inventory.to_pandas().to_sql('inventory', self.engine, if_exists='append', index=False)

    def _load_customers(self, df: pl.DataFrame):
        """Extract unique customers and load to database."""
        if 'customeremail' not in df.columns:
            print("No customeremail column found")
            return

        customer_cols = ['customeremail', 'customername', 'customeraddress', 'customerzipcode']
        available_cols = [c for c in customer_cols if c in df.columns]

        customers = (
            df.select(available_cols)
            .unique(subset=['customeremail'])
            .rename({
                'customeremail': 'email',
                'customeraddress': 'address',
                'customerzipcode': 'zip_code'
            })
        )

        # Split name
        if 'customername' in customers.columns:
            customers = customers.with_columns(
                pl.col('customername').str.split(' ').list.get(0).alias('first_name'),
                pl.col('customername').str.split(' ').list.get(1).alias('last_name')
            )

        # Extract city/state
        if 'address' in customers.columns:
            # Regex extraction in Polars
            # Assumes format "..., City, ST ZIP"
            customers = customers.with_columns(
                pl.col('address').str.extract(r',\s*([^,]+),\s*[A-Z]{2}', 1).alias('city'),
                pl.col('address').str.extract(r',\s*([A-Z]{2})\s*\d+', 1).alias('state')
            )

        customers = (
            customers.select(['email', 'first_name', 'last_name', 'address', 'city', 'state', 'zip_code'])
            .filter(pl.col('email').is_not_null())
        )

        print(f"Loading {len(customers)} customers")
        customers.to_pandas().to_sql('customer', self.engine, if_exists='append', index=False)

    def _load_orders(self, df: pl.DataFrame):
        """Extract unique orders and load to database."""
        if 'orderid' not in df.columns:
            print("No orderid column found")
            return

        order_cols = ['orderid', 'customeremail', 'orderdate', 'totalamount', 'deliverystatus']
        available_cols = [c for c in order_cols if c in df.columns]

        # Get customer IDs
        cust_map = pl.from_pandas(pd.read_sql("SELECT id, email FROM customer", self.engine)).rename({'id': 'customer_id', 'email': 'customeremail'})

        orders = (
            df.select(available_cols)
            .unique(subset=['orderid'])
            .join(cust_map, on='customeremail', how='left')
            .rename({
                'orderid': 'order_number',
                'orderdate': 'order_date',
                'totalamount': 'total_amount',
                'deliverystatus': 'status'
            })
        )

        # Date conversion
        if 'order_date' in orders.columns:
            orders = orders.with_columns(
                pl.col('order_date').str.strptime(pl.Datetime, "%Y-%m-%d", strict=False)
            )

        orders = (
            orders.select(['order_number', 'customer_id', 'order_date', 'total_amount', 'status'])
            .filter(pl.col('order_number').is_not_null())
        )

        print(f"Loading {len(orders)} orders")
        orders.to_pandas().to_sql('order', self.engine, if_exists='append', index=False)

    def _load_order_items(self, df: pl.DataFrame):
        """Load order items data."""
        if 'orderid' not in df.columns or 'productid' not in df.columns:
            print("Missing orderid or productid columns")
            return

        item_cols = ['orderid', 'productid', 'quantity', 'unitprice', 'discountamount']
        available_cols = [c for c in item_cols if c in df.columns]

        # Get IDs
        order_map = pl.from_pandas(pd.read_sql('SELECT id, order_number FROM "order"', self.engine)).rename({'id': 'order_id', 'order_number': 'orderid'})
        prod_map = pl.from_pandas(pd.read_sql("SELECT id, sku FROM product", self.engine)).rename({'id': 'product_id', 'sku': 'productid'})

        items = (
            df.select(available_cols)
            .join(order_map, on='orderid', how='left')
            .join(prod_map, on='productid', how='left')
            .rename({
                'unitprice': 'unit_price',
                'discountamount': 'discount'
            })
        )

        # Fill defaults
        if 'quantity' not in items.columns:
            items = items.with_columns(pl.lit(1).alias('quantity'))
        if 'discount' not in items.columns:
            items = items.with_columns(pl.lit(0).alias('discount'))

        items = (
            items.select(['order_id', 'product_id', 'quantity', 'unit_price', 'discount'])
            .filter(pl.col('order_id').is_not_null() & pl.col('product_id').is_not_null())
        )

        print(f"Loading {len(items)} order items")
        items.to_pandas().to_sql('order_item', self.engine, if_exists='append', index=False)

    def _load_shipments(self, df: pl.DataFrame):
        """Load shipment data."""
        if 'orderid' not in df.columns:
            print("No orderid column found")
            return

        ship_cols = ['orderid', 'warehouseid', 'shippingcarrier', 'shippingcost',
                     'expecteddeliverydate', 'actualdeliverydate', 'deliverystatus']
        available_cols = [c for c in ship_cols if c in df.columns]

        # Get IDs
        order_map = pl.from_pandas(pd.read_sql('SELECT id, order_number FROM "order"', self.engine)).rename({'id': 'order_id', 'order_number': 'orderid'})
        wh_map = pl.from_pandas(pd.read_sql("SELECT id, name FROM warehouse", self.engine)).rename({'id': 'warehouse_id', 'name': 'warehouseid'})

        shipments = (
            df.select(available_cols)
            .unique(subset=['orderid'])
            .join(order_map, on='orderid', how='left')
            .join(wh_map, on='warehouseid', how='left')
            .rename({
                'shippingcarrier': 'carrier',
                'shippingcost': 'shipping_cost',
                'expecteddeliverydate': 'ship_date',
                'actualdeliverydate': 'delivery_date',
                'deliverystatus': 'delivery_status'
            })
        )

        # Date conversion
        for col in ['ship_date', 'delivery_date']:
            if col in shipments.columns:
                shipments = shipments.with_columns(
                    pl.col(col).str.strptime(pl.Datetime, "%Y-%m-%d", strict=False)
                )

        shipments = (
            shipments.select(['order_id', 'warehouse_id', 'carrier', 'shipping_cost', 'ship_date', 'delivery_date', 'delivery_status'])
            .filter(pl.col('order_id').is_not_null())
        )

        print(f"Loading {len(shipments)} shipments")
        shipments.to_pandas().to_sql('shipment', self.engine, if_exists='append', index=False)

    def _load_reviews(self, df: pl.DataFrame):
        """Load review data if available."""
        if 'reviewrating' not in df.columns:
            print("No reviewrating column found")
            return

        review_cols = ['productid', 'customeremail', 'reviewrating', 'reviewtext', 'reviewdate']
        available_cols = [c for c in review_cols if c in df.columns]

        # Get IDs
        prod_map = pl.from_pandas(pd.read_sql("SELECT id, sku FROM product", self.engine)).rename({'id': 'product_id', 'sku': 'productid'})
        cust_map = pl.from_pandas(pd.read_sql("SELECT id, email FROM customer", self.engine)).rename({'id': 'customer_id', 'email': 'customeremail'})

        reviews = (
            df.select(available_cols)
            .filter(pl.col('reviewrating').is_not_null())
            .join(prod_map, on='productid', how='left')
            .join(cust_map, on='customeremail', how='left')
            .rename({
                'reviewrating': 'rating',
                'reviewtext': 'review_text',
                'reviewdate': 'review_date'
            })
        )

        if 'review_date' in reviews.columns:
            reviews = reviews.with_columns(
                pl.col('review_date').str.strptime(pl.Datetime, "%Y-%m-%d", strict=False)
            )

        reviews = (
            reviews.select(['product_id', 'customer_id', 'rating', 'review_text', 'review_date'])
            .filter(pl.col('product_id').is_not_null())
        )

        print(f"Loading {len(reviews)} reviews")
        reviews.to_pandas().to_sql('review', self.engine, if_exists='append', index=False)

    def close(self):
        """Close the database session."""
        self.session.close()

