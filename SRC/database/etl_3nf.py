import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL
from .schema_3nf import Base, Manufacturer, Product, Warehouse, Inventory, Customer, Order, OrderItem, Shipment, Review


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
        """Transform denormalized CSV data into 3NF tables."""
        df = pd.read_csv(csv_path)

        # Clean column names - lowercase with underscores
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        print(f"Loaded {len(df)} rows from CSV")
        print(f"Columns: {list(df.columns)}")

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

    def _load_manufacturers(self, df: pd.DataFrame):
        """Extract unique manufacturers and load to database."""
        if 'manufacturername' not in df.columns:
            print("No manufacturername column found")
            return

        manufacturers = df[['manufacturername']].drop_duplicates()
        manufacturers.columns = ['name']
        manufacturers['country'] = None
        manufacturers = manufacturers.dropna(subset=['name'])

        print(f"Loading {len(manufacturers)} manufacturers")
        manufacturers.to_sql('manufacturer', self.engine, if_exists='append', index=False)

    def _load_warehouses(self, df: pd.DataFrame):
        """Extract unique warehouses and load to database."""
        if 'warehouseid' not in df.columns:
            print("No warehouseid column found")
            return

        warehouse_cols = ['warehouseid', 'warehousestreetaddress', 'warehousezipcode', 'warehousecapacity']
        available_cols = [c for c in warehouse_cols if c in df.columns]

        warehouses = df[available_cols].drop_duplicates(subset=['warehouseid'])

        col_mapping = {
            'warehouseid': 'name',
            'warehousestreetaddress': 'location',
            'warehousecapacity': 'capacity'
        }
        warehouses = warehouses.rename(columns=col_mapping)
        warehouses = warehouses[['name', 'location', 'capacity']].dropna(subset=['name'])

        print(f"Loading {len(warehouses)} warehouses")
        warehouses.to_sql('warehouse', self.engine, if_exists='append', index=False)

    def _load_products(self, df: pd.DataFrame):
        """Extract unique products and load to database."""
        if 'productid' not in df.columns:
            print("No productid column found")
            return

        product_cols = ['productid', 'productname', 'productprice', 'unitprice']
        available_cols = [c for c in product_cols if c in df.columns]

        products = df[available_cols + ['manufacturername']].drop_duplicates(subset=['productid'])

        # Get manufacturer IDs
        mfr_map = pd.read_sql("SELECT id, name FROM manufacturer", self.engine)
        mfr_map = dict(zip(mfr_map['name'], mfr_map['id']))

        products['manufacturer_id'] = products['manufacturername'].map(mfr_map)

        # Rename columns
        products = products.rename(columns={
            'productid': 'sku',
            'productname': 'name',
            'productprice': 'price',
            'unitprice': 'cost'
        })

        products = products[['sku', 'name', 'price', 'cost', 'manufacturer_id']].dropna(subset=['sku'])

        print(f"Loading {len(products)} products")
        products.to_sql('product', self.engine, if_exists='append', index=False)

    def _load_inventory(self, df: pd.DataFrame):
        """Load inventory data."""
        if 'productid' not in df.columns or 'warehouseid' not in df.columns:
            print("Missing productid or warehouseid columns")
            return

        inv_cols = ['productid', 'warehouseid', 'stocklevel', 'restockthreshold']
        available_cols = [c for c in inv_cols if c in df.columns]

        inventory = df[available_cols].drop_duplicates(subset=['productid', 'warehouseid'])

        # Get product and warehouse IDs
        prod_map = pd.read_sql("SELECT id, sku FROM product", self.engine)
        prod_map = dict(zip(prod_map['sku'], prod_map['id']))

        wh_map = pd.read_sql("SELECT id, name FROM warehouse", self.engine)
        wh_map = dict(zip(wh_map['name'], wh_map['id']))

        inventory['product_id'] = inventory['productid'].map(prod_map)
        inventory['warehouse_id'] = inventory['warehouseid'].map(wh_map)

        inventory = inventory.rename(columns={
            'stocklevel': 'quantity',
            'restockthreshold': 'restock_threshold'
        })

        inventory = inventory[['product_id', 'warehouse_id', 'quantity', 'restock_threshold']].dropna()

        print(f"Loading {len(inventory)} inventory records")
        inventory.to_sql('inventory', self.engine, if_exists='append', index=False)

    def _load_customers(self, df: pd.DataFrame):
        """Extract unique customers and load to database."""
        if 'customeremail' not in df.columns:
            print("No customeremail column found")
            return

        customer_cols = ['customeremail', 'customername', 'customeraddress', 'customerzipcode']
        available_cols = [c for c in customer_cols if c in df.columns]

        customers = df[available_cols].drop_duplicates(subset=['customeremail'])

        # Split customer name into first/last
        if 'customername' in customers.columns:
            names = customers['customername'].str.split(' ', n=1, expand=True)
            customers['first_name'] = names[0]
            customers['last_name'] = names[1] if len(names.columns) > 1 else ''

        customers = customers.rename(columns={
            'customeremail': 'email',
            'customeraddress': 'address',
            'customerzipcode': 'zip_code'
        })

        # Extract city and state from address (format: "Street, City, ST ZIP")
        if 'address' in customers.columns:
            # Parse address to extract city - assumes format like "123 Main St, Chicago, IL 60601"
            address_parts = customers['address'].str.extract(r',\s*([^,]+),\s*([A-Z]{2})\s*\d+')
            customers['city'] = address_parts[0]
            customers['state'] = address_parts[1]

        customers = customers[['email', 'first_name', 'last_name', 'address', 'city', 'state', 'zip_code']].dropna(subset=['email'])

        print(f"Loading {len(customers)} customers")
        customers.to_sql('customer', self.engine, if_exists='append', index=False)

    def _load_orders(self, df: pd.DataFrame):
        """Extract unique orders and load to database."""
        if 'orderid' not in df.columns:
            print("No orderid column found")
            return

        order_cols = ['orderid', 'customeremail', 'orderdate', 'totalamount', 'deliverystatus']
        available_cols = [c for c in order_cols if c in df.columns]

        orders = df[available_cols].drop_duplicates(subset=['orderid'])

        # Get customer IDs
        cust_map = pd.read_sql("SELECT id, email FROM customer", self.engine)
        cust_map = dict(zip(cust_map['email'], cust_map['id']))

        orders['customer_id'] = orders['customeremail'].map(cust_map)

        orders = orders.rename(columns={
            'orderid': 'order_number',
            'orderdate': 'order_date',
            'totalamount': 'total_amount',
            'deliverystatus': 'status'
        })

        if 'order_date' in orders.columns:
            orders['order_date'] = pd.to_datetime(orders['order_date'], errors='coerce')

        orders = orders[['order_number', 'customer_id', 'order_date', 'total_amount', 'status']].dropna(subset=['order_number'])

        print(f"Loading {len(orders)} orders")
        orders.to_sql('order', self.engine, if_exists='append', index=False)

    def _load_order_items(self, df: pd.DataFrame):
        """Load order items data."""
        if 'orderid' not in df.columns or 'productid' not in df.columns:
            print("Missing orderid or productid columns")
            return

        item_cols = ['orderid', 'productid', 'quantity', 'unitprice', 'discountamount']
        available_cols = [c for c in item_cols if c in df.columns]

        items = df[available_cols].copy()

        # Get order and product IDs
        order_map = pd.read_sql('SELECT id, order_number FROM "order"', self.engine)
        order_map = dict(zip(order_map['order_number'], order_map['id']))

        prod_map = pd.read_sql("SELECT id, sku FROM product", self.engine)
        prod_map = dict(zip(prod_map['sku'], prod_map['id']))

        items['order_id'] = items['orderid'].map(order_map)
        items['product_id'] = items['productid'].map(prod_map)

        items = items.rename(columns={
            'unitprice': 'unit_price',
            'discountamount': 'discount'
        })

        # Fill defaults
        if 'quantity' not in items.columns:
            items['quantity'] = 1
        if 'discount' not in items.columns:
            items['discount'] = 0

        items = items[['order_id', 'product_id', 'quantity', 'unit_price', 'discount']].dropna(subset=['order_id', 'product_id'])

        print(f"Loading {len(items)} order items")
        items.to_sql('order_item', self.engine, if_exists='append', index=False)

    def _load_shipments(self, df: pd.DataFrame):
        """Load shipment data."""
        if 'orderid' not in df.columns:
            print("No orderid column found")
            return

        ship_cols = ['orderid', 'warehouseid', 'shippingcarrier', 'shippingcost',
                     'expecteddeliverydate', 'actualdeliverydate', 'deliverystatus']
        available_cols = [c for c in ship_cols if c in df.columns]

        shipments = df[available_cols].drop_duplicates(subset=['orderid'])

        # Get order and warehouse IDs
        order_map = pd.read_sql('SELECT id, order_number FROM "order"', self.engine)
        order_map = dict(zip(order_map['order_number'], order_map['id']))

        wh_map = pd.read_sql("SELECT id, name FROM warehouse", self.engine)
        wh_map = dict(zip(wh_map['name'], wh_map['id']))

        shipments['order_id'] = shipments['orderid'].map(order_map)
        shipments['warehouse_id'] = shipments['warehouseid'].map(wh_map)

        shipments = shipments.rename(columns={
            'shippingcarrier': 'carrier',
            'shippingcost': 'shipping_cost',
            'expecteddeliverydate': 'ship_date',
            'actualdeliverydate': 'delivery_date',
            'deliverystatus': 'delivery_status'
        })

        # Convert dates
        for col in ['ship_date', 'delivery_date']:
            if col in shipments.columns:
                shipments[col] = pd.to_datetime(shipments[col], errors='coerce')

        shipments = shipments[['order_id', 'warehouse_id', 'carrier', 'shipping_cost', 'ship_date', 'delivery_date', 'delivery_status']].dropna(subset=['order_id'])

        print(f"Loading {len(shipments)} shipments")
        shipments.to_sql('shipment', self.engine, if_exists='append', index=False)

    def _load_reviews(self, df: pd.DataFrame):
        """Load review data if available."""
        if 'reviewrating' not in df.columns:
            print("No reviewrating column found")
            return

        review_cols = ['productid', 'customeremail', 'reviewrating', 'reviewtext', 'reviewdate']
        available_cols = [c for c in review_cols if c in df.columns]

        reviews = df[available_cols].dropna(subset=['reviewrating'])

        # Get product and customer IDs
        prod_map = pd.read_sql("SELECT id, sku FROM product", self.engine)
        prod_map = dict(zip(prod_map['sku'], prod_map['id']))

        cust_map = pd.read_sql("SELECT id, email FROM customer", self.engine)
        cust_map = dict(zip(cust_map['email'], cust_map['id']))

        reviews['product_id'] = reviews['productid'].map(prod_map)
        reviews['customer_id'] = reviews['customeremail'].map(cust_map)

        reviews = reviews.rename(columns={
            'reviewrating': 'rating',
            'reviewtext': 'review_text',
            'reviewdate': 'review_date'
        })

        if 'review_date' in reviews.columns:
            reviews['review_date'] = pd.to_datetime(reviews['review_date'], errors='coerce')

        reviews = reviews[['product_id', 'customer_id', 'rating', 'review_text', 'review_date']].dropna(subset=['product_id'])

        print(f"Loading {len(reviews)} reviews")
        reviews.to_sql('review', self.engine, if_exists='append', index=False)

    def close(self):
        """Close the database session."""
        self.session.close()
