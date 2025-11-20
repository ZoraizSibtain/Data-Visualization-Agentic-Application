import os
from typing import List, Any
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from config.settings import DATABASE_URL

class DatabaseManager:
    # Class-level cache for schema (shared across instances)
    _schema_cache = None

    def __init__(self):
        # Use connection pooling for better performance
        self.engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True
        )

    def get_schema(self, uuid: str) -> str:
        """Retrieve the database schema."""
        return """
        Tables and Columns:
        
        robot_vacuum_depot.Customer(CustomerID, CustomerName, CustomerEmail, CustomerStreetAddress, CustomerZipCode, BillingZipCode, Segment)
        robot_vacuum_depot.Manufacturer(ManufacturerID, ManufacturerName, Country, LeadTimeDays, ReliabilityScore)
        robot_vacuum_depot.Product(ProductID, ProductName, ModelNumber, ManufacturerID, UnitPrice, ProductDescription)
        robot_vacuum_depot.Warehouse(WarehouseID, WarehouseStreetAddress, WarehouseZipCode, WarehouseCapacity)
        robot_vacuum_depot.DistributionCenter(DistributionCenterID, Region, DistributionCenterStreetAddress, DistributionCenterZipCode, FleetSize)
        robot_vacuum_depot.WarehouseDistributionCenter(WarehouseID, DistributionCenterID)
        robot_vacuum_depot.WarehouseProductStock(WarehouseID, ProductID, StockLevel, RestockThreshold, LastRestockDate, LastUpdateDate)
        robot_vacuum_depot.Order(OrderID, CustomerID, ProductID, WarehouseID, DistributionCenterID, Quantity, UnitPrice, DiscountAmount, PromoCode, TaxAmount, ShippingCost, CostOfGoods, TotalAmount, OrderDate, ExpectedDeliveryDate, ActualDeliveryDate, DeliveryStatus, PaymentMethod, CardNumber, CardBrand, BillingZipCode, DeliveryStreetAddress, DeliveryZipCode, ShippingCarrier)
        robot_vacuum_depot.Review(ReviewID, OrderID, CustomerID, ProductID, ProductRating, ReviewText, ReviewDate, ReviewSentiment)

        Relationships:
        - robot_vacuum_depot.Product.ManufacturerID -> robot_vacuum_depot.Manufacturer.ManufacturerID
        - robot_vacuum_depot.Order.CustomerID -> robot_vacuum_depot.Customer.CustomerID
        - robot_vacuum_depot.Order.ProductID -> robot_vacuum_depot.Product.ProductID
        - robot_vacuum_depot.Order.WarehouseID -> robot_vacuum_depot.Warehouse.WarehouseID
        - robot_vacuum_depot.Order.DistributionCenterID -> robot_vacuum_depot.DistributionCenter.DistributionCenterID
        - robot_vacuum_depot.Review.OrderID -> robot_vacuum_depot.Order.OrderID
        - robot_vacuum_depot.Review.CustomerID -> robot_vacuum_depot.Customer.CustomerID
        - robot_vacuum_depot.Review.ProductID -> robot_vacuum_depot.Product.ProductID
        - robot_vacuum_depot.WarehouseProductStock.WarehouseID -> robot_vacuum_depot.Warehouse.WarehouseID
        - robot_vacuum_depot.WarehouseProductStock.ProductID -> robot_vacuum_depot.Product.ProductID
        - robot_vacuum_depot.WarehouseDistributionCenter.WarehouseID -> robot_vacuum_depot.Warehouse.WarehouseID
        - robot_vacuum_depot.WarehouseDistributionCenter.DistributionCenterID -> robot_vacuum_depot.DistributionCenter.DistributionCenterID
        """

    def execute_query(self, uuid: str, query: str) -> List[Any]:
        """Execute SQL query on the local database and return results."""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(query))
                return [list(row) for row in result]
        except Exception as e:
            raise Exception(f"Error executing query: {str(e)}")