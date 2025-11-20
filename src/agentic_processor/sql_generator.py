import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class SQLGenerator:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.schema_info = self._get_schema_info()
        
    def _get_schema_info(self) -> str:
        return """
        Tables and Columns:

        Customer(CustomerID, CustomerName, CustomerEmail, CustomerStreetAddress, CustomerZipCode, BillingZipCode, Segment)
        Manufacturer(ManufacturerID, ManufacturerName, Country, LeadTimeDays, ReliabilityScore)
        Product(ProductID, ProductName, ModelNumber, ManufacturerID, UnitPrice, ProductDescription)
        Warehouse(WarehouseID, WarehouseStreetAddress, WarehouseZipCode, WarehouseCapacity)
        DistributionCenter(DistributionCenterID, Region, DistributionCenterStreetAddress, DistributionCenterZipCode, FleetSize)
        WarehouseDistributionCenter(WarehouseID, DistributionCenterID)
        WarehouseProductStock(WarehouseID, ProductID, StockLevel, RestockThreshold, LastRestockDate, LastUpdateDate)
        Order(OrderID, CustomerID, ProductID, WarehouseID, DistributionCenterID, Quantity, UnitPrice, DiscountAmount, PromoCode, TaxAmount, ShippingCost, CostOfGoods, TotalAmount, OrderDate, ExpectedDeliveryDate, ActualDeliveryDate, DeliveryStatus, PaymentMethod, CardNumber, CardBrand, BillingZipCode, DeliveryStreetAddress, DeliveryZipCode, ShippingCarrier)
        Review(ReviewID, OrderID, CustomerID, ProductID, ProductRating, ReviewText, ReviewDate, ReviewSentiment)

        Relationships:
        - Product.ManufacturerID -> Manufacturer.ManufacturerID
        - Order.CustomerID -> Customer.CustomerID
        - Order.ProductID -> Product.ProductID
        - Order.WarehouseID -> Warehouse.WarehouseID
        - Order.DistributionCenterID -> DistributionCenter.DistributionCenterID
        - Review.OrderID -> Order.OrderID
        - Review.CustomerID -> Customer.CustomerID
        - Review.ProductID -> Product.ProductID
        - WarehouseProductStock.WarehouseID -> Warehouse.WarehouseID
        - WarehouseProductStock.ProductID -> Product.ProductID
        - WarehouseDistributionCenter.WarehouseID -> Warehouse.WarehouseID
        - WarehouseDistributionCenter.DistributionCenterID -> DistributionCenter.DistributionCenterID
        """

    def generate_sql(self, query: str) -> str:
        prompt = ChatPromptTemplate.from_template("""
        You are an expert PostgreSQL SQL generator. Given the following database schema and a natural language query, generate a valid SQL query.

        Schema:
        {schema}

        Rules:
        1. Return ONLY the SQL query, no markdown formatting, no explanations.
        2. Use standard PostgreSQL syntax.
        3. IMPORTANT: All tables are in the robot_vacuum_depot schema. You MUST prefix all table names with the schema.
        4. IMPORTANT: All table names and column names use PascalCase and MUST be quoted with double quotes. Examples:
           - robot_vacuum_depot."Customer"
           - robot_vacuum_depot."Product"
           - robot_vacuum_depot."Manufacturer"
           - robot_vacuum_depot."Order"
        5. Column names must also be quoted with double quotes in PascalCase. Examples:
           - "DeliveryStatus"
           - "ProductName"
           - "ManufacturerName"
           - "OrderDate"
        6. Handle case-insensitivity for string comparisons using ILIKE if needed.
        7. For date operations, use PostgreSQL specific functions like DATE_TRUNC.
        8. Ensure all joins are correct based on the schema relationships.
        9. IMPORTANT: When using table aliases, you MUST use the alias consistently throughout the query. Example:
           - FROM robot_vacuum_depot."Order" AS o ... use o."OrderDate", NOT "Order"."OrderDate"

        User Query: {query}

        SQL Query:
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        
        sql = chain.invoke({"schema": self.schema_info, "query": query})
        
        # Clean up any potential markdown code blocks if the LLM ignores the rule
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql
