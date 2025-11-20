package main

import (
	"database/sql"
	"fmt"
	"log"
	"time"

	_ "github.com/lib/pq"
)

func main() {
	start := time.Now()

	// Database connection parameters
	host := "127.0.0.1"
	port := 5432
	user := "postgres"
	password := "root"
	dbname := "robotvacuum"

	psqlInfo := fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname,
	)

	log.Printf("Connecting to PostgreSQL at %s:%d ...", host, port)
	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		log.Fatalf("X FATAL: Unable to open database connection: %v", err)
	}
	defer db.Close()

	if err := db.Ping(); err != nil {
		log.Fatalf("X FATAL: Unable to ping database: %v", err)
	}

	log.Println("✔ Connected to PostgreSQL successfully.")

	// ---
	// Drop existing schema and all tables (CASCADE)
	// ---
	log.Println("Dropping existing schema if exists...")
	if _, err := db.Exec("DROP SCHEMA IF EXISTS robot_vacuum_depot CASCADE;"); err != nil {
		log.Fatalf("X ERROR dropping schema: %v", err)
	} else {
		log.Println("✔ Existing schema dropped.")
	}

	// ---
	// Create schema
	// ---
	if _, err := db.Exec("CREATE SCHEMA robot_vacuum_depot;"); err != nil {
		log.Fatalf("X ERROR creating schema: %v", err)
	} else {
		log.Println("✔ Schema robot_vacuum_depot created.")
	}

	// ---
	// Table: Customer
	// ---
	createTable(db, "Customer", `CREATE TABLE robot_vacuum_depot."Customer"(
        "CustomerID" VARCHAR(40) PRIMARY KEY,
        "CustomerName" VARCHAR(120),
        "CustomerEmail" VARCHAR(120),
        "CustomerStreetAddress" VARCHAR(200),
        "CustomerZipCode" VARCHAR(20),
        "BillingZipCode" VARCHAR(20),
        "Segment" VARCHAR(60)
    );`)

	// ---
	// Table: Manufacturer
	// ---
	createTable(db, "Manufacturer", `CREATE TABLE robot_vacuum_depot."Manufacturer"(
        "ManufacturerID" VARCHAR(40) PRIMARY KEY,
        "ManufacturerName" VARCHAR(120),
        "Country" VARCHAR(60),
        "LeadTimeDays" NUMERIC(10,2),
        "ReliabilityScore" NUMERIC(10,4)
    );`)

	// ---
	// Table: Product
	// ---
	createTable(db, "Product", `CREATE TABLE robot_vacuum_depot."Product"(
        "ProductID" VARCHAR(40) PRIMARY KEY,
        "ProductName" VARCHAR(160),
        "ModelNumber" VARCHAR(80),
        "ManufacturerID" VARCHAR(40) REFERENCES robot_vacuum_depot."Manufacturer"("ManufacturerID"),
        "UnitPrice" NUMERIC(12,2),
        "ProductDescription" TEXT
    );`)

	// ---
	// Table: Warehouse
	// ---
	createTable(db, "Warehouse", `CREATE TABLE robot_vacuum_depot."Warehouse"(
        "WarehouseID" VARCHAR(40) PRIMARY KEY,
        "WarehouseStreetAddress" VARCHAR(200),
        "WarehouseZipCode" VARCHAR(20),
        "WarehouseCapacity" INT
    );`)

	// ---
	// Table: DistributionCenter
	// ---
	createTable(db, "DistributionCenter", `CREATE TABLE robot_vacuum_depot."DistributionCenter"(
        "DistributionCenterID" VARCHAR(40) PRIMARY KEY,
        "Region" VARCHAR(60),
        "DistributionCenterStreetAddress" VARCHAR(200),
        "DistributionCenterZipCode" VARCHAR(20),
        "FleetSize" INT
    );`)

	// ---
	// Bridge: WarehouseDistributionCenter
	// ---
	createTable(db, "WarehouseDistributionCenter", `CREATE TABLE robot_vacuum_depot."WarehouseDistributionCenter"(
        "WarehouseID" VARCHAR(40) REFERENCES robot_vacuum_depot."Warehouse"("WarehouseID"),
        "DistributionCenterID" VARCHAR(40) REFERENCES robot_vacuum_depot."DistributionCenter"("DistributionCenterID"),
        PRIMARY KEY ("WarehouseID", "DistributionCenterID")
    );`)

	// ---
	// Table: WarehouseProductStock
	// ---
	createTable(db, "WarehouseProductStock", `CREATE TABLE robot_vacuum_depot."WarehouseProductStock"(
        "WarehouseID" VARCHAR(40) REFERENCES robot_vacuum_depot."Warehouse"("WarehouseID"),
        "ProductID" VARCHAR(40) REFERENCES robot_vacuum_depot."Product"("ProductID"),
        "StockLevel" INT,
        "RestockThreshold" INT,
        "LastRestockDate" TIMESTAMP,
        "LastUpdateDate" TIMESTAMP,
        PRIMARY KEY ("WarehouseID", "ProductID")
    );`)

	// ---
	// Table: Order
	// ---
	createTable(db, "Order", `CREATE TABLE robot_vacuum_depot."Order"(
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
    );`)

	// ---
	// Table: Review
	// ---
	createTable(db, "Review", `CREATE TABLE robot_vacuum_depot."Review"(
        "ReviewID" VARCHAR(40) PRIMARY KEY,
        "OrderID" VARCHAR(40) REFERENCES robot_vacuum_depot."Order"("OrderID"),
        "CustomerID" VARCHAR(40) REFERENCES robot_vacuum_depot."Customer"("CustomerID"),
        "ProductID" VARCHAR(40) REFERENCES robot_vacuum_depot."Product"("ProductID"),
        "ProductRating" INT,
        "ReviewText" TEXT,
        "ReviewDate" TIMESTAMP,
        "ReviewSentiment" VARCHAR(20)
    );`)

	// ---
	// Indexes
	// ---
	log.Println("Creating indexes...")
	createIndex(db, "idx_order_customer", `CREATE INDEX "idx_order_customer" ON robot_vacuum_depot."Order"("CustomerID");`)
	createIndex(db, "idx_order_date", `CREATE INDEX "idx_order_date" ON robot_vacuum_depot."Order"("OrderDate");`)
	createIndex(db, "idx_order_status", `CREATE INDEX "idx_order_status" ON robot_vacuum_depot."Order"("DeliveryStatus");`)
	createIndex(db, "idx_review_product", `CREATE INDEX "idx_review_product" ON robot_vacuum_depot."Review"("ProductID");`)
	createIndex(db, "idx_product_manufacturer", `CREATE INDEX "idx_product_manufacturer" ON robot_vacuum_depot."Product"("ManufacturerID");`)

	elapsed := time.Since(start)
	log.Printf("Schema creation complete in %s", elapsed)
}

// Helper function for table creation with detailed tracing
func createTable(db *sql.DB, tableName string, ddl string) {
	start := time.Now()
	log.Printf("Creating table: %s ...", tableName)
	_, err := db.Exec(ddl)
	if err != nil {
		log.Fatalf("X ERROR creating table %s: %v", tableName, err)
	} else {
		elapsed := time.Since(start)
		log.Printf("☑ Table %s created successfully in %s", tableName, elapsed)
	}
}

// Helper function for index creation
func createIndex(db *sql.DB, indexName string, ddl string) {
	start := time.Now()
	log.Printf("Creating index: %s ...", indexName)
	_, err := db.Exec(ddl)
	if err != nil {
		log.Printf("X ERROR creating index %s: %v", indexName, err)
	} else {
		elapsed := time.Since(start)
		log.Printf("☑ Index %s created successfully in %s", indexName, elapsed)
	}
}
