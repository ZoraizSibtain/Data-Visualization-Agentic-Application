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
        
        Manufacturer(ManufacturerID, ManufacturerName, ReliabilityScore)
        Product(ProductID, ProductName, ProductDescription, ModelNumber, ManufacturerID, ProductPrice)
        Customer(CustomerID, CustomerName, CustomerEmail, CustomerZipCode, CustomerAddress, Segment)
        Warehouse(WarehouseID, WarehouseStreetAddress, WarehouseZipCode, WarehouseCapacity)
        DistributionCenter(DistributionCenterID, DistributionCenterStreetAddress, DistributionCenterZipCode, FleetSize)
        Order(OrderID, OrderDate, CustomerID, ProductID, DeliveryStatus, DeliveryAddress, DeliveryZipCode, ShippingCost, ShippingCarrier, TotalAmount, TaxAmount, DiscountAmount, Quantity, PaymentMethod, ExpectedDeliveryDate, ActualDeliveryDate)
        Review(ReviewID, OrderID, ReviewRating, ReviewText, ReviewDate, ReviewSentiment)
        WarehouseProductStock(WarehouseID, ProductID, StockLevel, RestockThreshold, LastRestockDate)
        WarehouseDistributionCenter(WarehouseID, DistributionCenterID, LeadTimeDays)
        
        Relationships:
        - Product.ManufacturerID -> Manufacturer.ManufacturerID
        - Order.CustomerID -> Customer.CustomerID
        - Order.ProductID -> Product.ProductID
        - Review.OrderID -> Order.OrderID
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
        3. IMPORTANT: All table and column names are case-sensitive and must be quoted with double quotes. Examples:
           - "Order"."Quantity"
           - "Product"."ProductName"
           - "Manufacturer"."ManufacturerName"
        4. Handle case-insensitivity for string comparisons using ILIKE if needed.
        5. For date operations, use PostgreSQL specific functions like DATE_TRUNC.
        6. Ensure all joins are correct based on the schema relationships.
        7. Always use table aliases and fully qualify column names with double quotes.

        User Query: {query}

        SQL Query:
        """)
        
        chain = prompt | self.llm | StrOutputParser()
        
        sql = chain.invoke({"schema": self.schema_info, "query": query})
        
        # Clean up any potential markdown code blocks if the LLM ignores the rule
        sql = sql.replace("```sql", "").replace("```", "").strip()
        return sql
