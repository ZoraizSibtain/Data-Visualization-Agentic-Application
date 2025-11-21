"""
RAG (Retrieval Augmented Generation) Layer for Robot Vacuum Depot Analytics

This module provides contextual data retrieval to enhance query responses with
relevant examples, business context, and historical patterns.
"""

from typing import Dict, List, Any, Optional
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from .LLMManager import LLMManager
from .DatabaseManager import DatabaseManager
import numpy as np


class RAGLayer:
    """
    RAG Layer that enhances SQL generation with contextual retrieval.

    Features:
    - Schema context retrieval
    - Query example matching
    - Business context injection
    - Historical pattern recognition
    """

    def __init__(self):
        self.llm_manager = LLMManager()
        self.db_manager = DatabaseManager()
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # Pre-defined query examples for few-shot learning
        self.query_examples = self._load_query_examples()
        self.example_embeddings = None
        self._initialize_embeddings()

    def _load_query_examples(self) -> List[Dict[str, str]]:
        """Load curated query examples for few-shot learning."""
        return [
            {
                "question": "Which robot vacuum models have the highest number of delayed deliveries across all Chicago ZIP codes?",
                "sql": '''SELECT p."ProductName", COUNT(*) as delayed_count
                    FROM "robot_vacuum_depot"."Order" o
                    JOIN "robot_vacuum_depot"."Product" p ON o."ProductID" = p."ProductID"
                    WHERE o."DeliveryStatus" = 'Delayed'
                    AND o."DeliveryZipCode" LIKE '606%'
                    GROUP BY p."ProductName"
                    ORDER BY delayed_count DESC
                    LIMIT 10''',
                "context": "Delivery analysis - Chicago ZIP codes start with 606, joins Order and Product tables"
            },
            {
                "question": "Which warehouses are below their restock threshold?",
                "sql": '''SELECT w."WarehouseID", w."WarehouseZipCode", wps."StockLevel", wps."RestockThreshold"
                    FROM "robot_vacuum_depot"."Warehouse" w
                    JOIN "robot_vacuum_depot"."WarehouseProductStock" wps ON w."WarehouseID" = wps."WarehouseID"
                    WHERE wps."StockLevel" < wps."RestockThreshold"
                    ORDER BY (wps."RestockThreshold" - wps."StockLevel") DESC''',
                "context": "Inventory management - warehouse stock monitoring"
            },
            {
                "question": "What is the total monthly revenue trend?",
                "sql": '''SELECT DATE_TRUNC('month', o."OrderDate") as month,
                    SUM(o."TotalAmount") as revenue
                    FROM "robot_vacuum_depot"."Order" o
                    WHERE o."TotalAmount" IS NOT NULL
                    GROUP BY DATE_TRUNC('month', o."OrderDate")
                    ORDER BY month''',
                "context": "Time series analysis - revenue trends"
            },
            {
                "question": "What is the distribution of delivery statuses?",
                "sql": '''SELECT "DeliveryStatus", COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
                    FROM "robot_vacuum_depot"."Order"
                    WHERE "DeliveryStatus" IS NOT NULL
                    GROUP BY "DeliveryStatus"
                    ORDER BY count DESC''',
                "context": "Distribution analysis - categorical breakdown"
            },
            {
                "question": "Which manufacturer has the best average review rating?",
                "sql": '''SELECT m."ManufacturerName",
                    ROUND(AVG(r."Rating")::numeric, 2) as avg_rating,
                    COUNT(r."ReviewID") as review_count
                    FROM "robot_vacuum_depot"."Manufacturer" m
                    JOIN "robot_vacuum_depot"."Product" p ON m."ManufacturerID" = p."ManufacturerID"
                    JOIN "robot_vacuum_depot"."Review" r ON p."ProductID" = r."ProductID"
                    GROUP BY m."ManufacturerName"
                    HAVING COUNT(r."ReviewID") >= 5
                    ORDER BY avg_rating DESC
                    LIMIT 10''',
                "context": "Aggregation with filtering - manufacturer performance"
            },
            {
                "question": "Compare average shipping cost by carrier",
                "sql": '''SELECT "Carrier",
                    ROUND(AVG("ShippingCost")::numeric, 2) as avg_shipping_cost,
                    COUNT(*) as order_count
                    FROM "robot_vacuum_depot"."Order"
                    WHERE "Carrier" IS NOT NULL AND "ShippingCost" IS NOT NULL
                    GROUP BY "Carrier"
                    ORDER BY avg_shipping_cost DESC''',
                "context": "Carrier comparison - cost analysis"
            },
            {
                "question": "Top selling products by revenue",
                "sql": '''SELECT p."ProductName",
                    SUM(o."TotalAmount") as total_revenue,
                    SUM(o."Quantity") as units_sold
                    FROM "robot_vacuum_depot"."Order" o
                    JOIN "robot_vacuum_depot"."Product" p ON o."ProductID" = p."ProductID"
                    WHERE o."TotalAmount" IS NOT NULL
                    GROUP BY p."ProductName"
                    ORDER BY total_revenue DESC
                    LIMIT 10''',
                "context": "Sales ranking - product performance"
            },
            {
                "question": "Customer orders by ZIP code",
                "sql": '''SELECT c."ZipCode", COUNT(o."OrderID") as order_count,
                    SUM(o."TotalAmount") as total_revenue
                    FROM "robot_vacuum_depot"."Customer" c
                    JOIN "robot_vacuum_depot"."Order" o ON c."CustomerID" = o."CustomerID"
                    WHERE c."ZipCode" IS NOT NULL
                    GROUP BY c."ZipCode"
                    ORDER BY order_count DESC
                    LIMIT 15''',
                "context": "Geographic analysis - customer distribution"
            }
        ]

    def _initialize_embeddings(self):
        """Pre-compute embeddings for query examples."""
        try:
            questions = [ex["question"] for ex in self.query_examples]
            self.example_embeddings = self.embeddings.embed_documents(questions)
        except Exception as e:
            print(f"Warning: Failed to initialize RAG embeddings: {e}")
            self.example_embeddings = None

    def get_similar_examples(self, question: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        Retrieve most similar query examples using semantic search.

        Args:
            question: User's natural language question
            top_k: Number of examples to retrieve

        Returns:
            List of similar query examples
        """
        if self.example_embeddings is None:
            return self.query_examples[:top_k]

        try:
            # Embed the question
            question_embedding = self.embeddings.embed_query(question)

            # Calculate cosine similarity
            similarities = []
            for i, ex_emb in enumerate(self.example_embeddings):
                similarity = np.dot(question_embedding, ex_emb) / (
                    np.linalg.norm(question_embedding) * np.linalg.norm(ex_emb)
                )
                similarities.append((i, similarity))

            # Sort by similarity and get top_k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_indices = [idx for idx, _ in similarities[:top_k]]

            return [self.query_examples[i] for i in top_indices]

        except Exception as e:
            print(f"Error in semantic search: {e}")
            return self.query_examples[:top_k]

    def get_business_context(self, question: str) -> str:
        """
        Generate relevant business context for the question.

        Args:
            question: User's question

        Returns:
            Business context string
        """
        # Define business rules and context
        business_rules = {
            "delivery": "DeliveryStatus can be: 'Delivered', 'Delayed', 'Canceled', 'In Transit', 'Fraud'. Delayed deliveries impact customer satisfaction.",
            "revenue": "TotalAmount = (ProductPrice * Quantity) + ShippingCost + TaxAmount - DiscountAmount",
            "inventory": "StockLevel below RestockThreshold indicates need for reorder. Critical when StockLevel < RestockThreshold * 0.5",
            "rating": "Reviews have Rating 1-5. Consider only products with 5+ reviews for reliable averages.",
            "shipping": "Carriers include FedEx, UPS, USPS. ShippingCost varies by carrier and distance.",
            "time": "OrderDate and DeliveryDate are timestamps. Use DATE_TRUNC for time-based grouping.",
        }

        # Identify relevant contexts based on keywords
        relevant_contexts = []
        question_lower = question.lower()

        if any(word in question_lower for word in ['delivery', 'delayed', 'shipped', 'transit']):
            relevant_contexts.append(business_rules["delivery"])
        if any(word in question_lower for word in ['revenue', 'sales', 'amount', 'money']):
            relevant_contexts.append(business_rules["revenue"])
        if any(word in question_lower for word in ['stock', 'inventory', 'warehouse', 'restock']):
            relevant_contexts.append(business_rules["inventory"])
        if any(word in question_lower for word in ['rating', 'review', 'satisfaction']):
            relevant_contexts.append(business_rules["rating"])
        if any(word in question_lower for word in ['shipping', 'carrier', 'cost']):
            relevant_contexts.append(business_rules["shipping"])
        if any(word in question_lower for word in ['trend', 'monthly', 'daily', 'time', 'over']):
            relevant_contexts.append(business_rules["time"])

        return " ".join(relevant_contexts) if relevant_contexts else ""

    def enhance_sql_generation(self, state: dict) -> dict:
        """
        Enhance SQL generation with RAG context.

        Args:
            state: Current workflow state with 'question' and 'uuid'

        Returns:
            Updated state with RAG-enhanced context
        """
        question = state['question']

        # Get similar examples
        similar_examples = self.get_similar_examples(question, top_k=3)

        # Get business context
        business_context = self.get_business_context(question)

        # Format examples for prompt
        examples_text = "\n\n".join([
            f"Question: {ex['question']}\nSQL: {ex['sql']}\nContext: {ex['context']}"
            for ex in similar_examples
        ])

        return {
            "rag_examples": examples_text,
            "rag_business_context": business_context,
            "rag_similar_queries": similar_examples
        }

    def get_table_relationships(self) -> str:
        """
        Get a description of table relationships for context.

        Returns:
            String describing key table relationships
        """
        return """
Key Table Relationships:
- Order -> Customer (CustomerID): Links orders to customers
- Order -> Product (ProductID): Links orders to products
- Product -> Manufacturer (ManufacturerID): Links products to manufacturers
- Review -> Product (ProductID): Links reviews to products
- Review -> Customer (CustomerID): Links reviews to customers
- WarehouseProductStock -> Warehouse (WarehouseID): Links stock to warehouses
- WarehouseProductStock -> Product (ProductID): Links stock to products
- WarehouseDistributionCenter -> Warehouse, DistributionCenter: Warehouse-DC mapping

Common Join Patterns:
- Product details with orders: Order JOIN Product ON ProductID
- Manufacturer info: Product JOIN Manufacturer ON ManufacturerID
- Customer info: Order JOIN Customer ON CustomerID
- Review analysis: Review JOIN Product JOIN Manufacturer
"""


# Usage in SQLAgent.generate_sql_direct():
#
# def generate_sql_with_rag(self, state: dict) -> dict:
#     """Generate SQL with RAG enhancement."""
#     rag = RAGLayer()
#     rag_context = rag.enhance_sql_generation(state)
#
#     # Include RAG context in the prompt
#     prompt = ChatPromptTemplate.from_messages([
#         ("system", f'''You are an expert SQL developer...
#
# Business Context:
# {rag_context.get('rag_business_context', '')}
#
# Similar Query Examples:
# {rag_context.get('rag_examples', '')}
#
# {rag.get_table_relationships()}
#
# Generate SQL query...'''),
#         ...
#     ])
