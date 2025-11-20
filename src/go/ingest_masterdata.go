package main

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	_ "github.com/lib/pq"
)

const (
	host     = "127.0.0.1"
	port     = 5432
	user     = "postgres"
	password = "root"
	dbname   = "robotvacuum"
	csvFile  = "RobotVacuumDepot_MasterData.csv"
)

func main() {
	start := time.Now()

	psqlInfo := fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname,
	)
	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		log.Fatalf("X open database: %v", err)
	}
	defer db.Close()
	if err := db.Ping(); err != nil {
		log.Fatalf("X ping database: %v", err)
	}
	log.Println("✔ Connected to PostgreSQL.")

	file, err := os.Open(csvFile)
	if err != nil {
		log.Fatalf("X open CSV: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	headers, err := reader.Read()
	if err != nil {
		log.Fatalf("X read header: %v", err)
	}

	headerMap := make(map[string]int)
	for i, h := range headers {
		headerMap[strings.ToLower(strings.TrimSpace(h))] = i
	}

	log.Printf("✔ Loaded %d CSV columns (header-based mapping enabled).", len(headerMap))

	// Read ALL records at once
	records, err := reader.ReadAll()
	if err != nil {
		log.Fatalf("X read all records: %v", err)
	}
	log.Printf("✔ Read %d records from CSV.", len(records))

	// Start a SINGLE transaction for everything
	tx, err := db.Begin()
	if err != nil {
		log.Fatalf("X begin transaction: %v", err)
	}
	defer tx.Rollback()

	rowCount := 0
	for _, rec := range records {
		rowCount++
		if err := insertRowByHeader(tx, rec, headerMap, rowCount); err != nil {
			log.Printf("X row %d (OrderID=%s): %v",
				rowCount, safeGet(rec, headerMap, "orderid"), err)
		}
		if rowCount%1000 == 0 {
			log.Printf("Processed %d rows...", rowCount)
		}
	}

	if err := tx.Commit(); err != nil {
		log.Fatalf("X commit transaction: %v", err)
	}

	log.Printf("✓ Ingestion complete: %d rows in %s.", rowCount, time.Since(start))
}

func safeGet(record []string, headerMap map[string]int, column string) string {
	if idx, exists := headerMap[column]; exists && idx < len(record) {
		return record[idx]
	}
	return ""
}

func insertRowByHeader(tx *sql.Tx, rec []string, hdr map[string]int, row int) error {
	get := func(name string) string {
		idx, ok := hdr[strings.ToLower(name)]
		if !ok || idx >= len(rec) {
			return ""
		}
		return strings.TrimSpace(rec[idx])
	}

	intOrWarn := func(v, field string) int {
		if v == "" {
			return 0
		}
		n, err := strconv.Atoi(v)
		if err != nil {
			// log.Printf("▲ row %d: invalid INT %s='%s' -> 0", row, field, v)
			return 0
		}
		return n
	}

	floatOrWarn := func(v, field string) float64 {
		if v == "" {
			return 0
		}
		f, err := strconv.ParseFloat(v, 64)
		if err != nil {
			// log.Printf("▲ row %d: invalid FLOAT %s='%s' -> 0.0", row, field, v)
			return 0
		}
		return f
	}

	parseDate := func(v, field string) time.Time {
		if v == "" {
			return time.Time{}
		}
		v = strings.TrimSpace(v)
		layouts := []string{
			"2006-01-02 15:04:05",
			"2006-01-02 15:04",
			"01/02/2006 15:04:05",
			"01/02/2006 15:04",
			"01/02/2006 3:04 PM",
			"1/2/2006 3:04 PM",
			"1/2/2006 15:04:05",
			"1/2/2006 15:04",
			"1/2/2006 7:04",
			"1/2/2006 07:04",
			"01/02/2006",
			"1/2/2006",
		}

		for _, layout := range layouts {
			if t, err := time.Parse(layout, v); err == nil {
				return t
			}
		}

		if strings.Count(v, ":") == 1 && !strings.Contains(v, "M") {
			try := v + " PM"
			if t, err := time.Parse("1/2/2006 3:04 PM", try); err == nil {
				return t
			}
		}

		// log.Printf("▲ row %d: invalid DATE %s='%s' (no matching layout)", row, field, v)
		return time.Time{}
	}

	truncate := func(s string, max int, field string) string {
		if len(s) > max {
			// log.Printf("▲ row %d: truncating %s from %d to %d chars", row, field, len(s), max)
			return s[:max]
		}
		return s
	}

	// --- Map headers → schema fields ---
	customerID := get("customerid")
	customerName := truncate(get("customername"), 120, "CustomerName")
	customerEmail := truncate(get("customeremail"), 120, "CustomerEmail")
	// MAPPING FIX: CSV 'CustomerAddress' -> DB 'CustomerStreetAddress'
	customerStreet := truncate(get("customeraddress"), 200, "CustomerStreetAddress")
	customerZip := truncate(get("customerzipcode"), 20, "CustomerZipCode")
	billingZip := truncate(get("billingzipcode"), 20, "BillingZipCode")
	segment := truncate(get("segment"), 60, "Segment")

	manufacturerID := get("manufacturerid")
	manufacturerName := truncate(get("manufacturername"), 120, "ManufacturerName")
	country := truncate(get("country"), 60, "Country") // Likely empty in CSV
	leadTime := floatOrWarn(get("leadtimedays"), "LeadTimeDays")
	reliability := floatOrWarn(get("reliabilityscore"), "ReliabilityScore")

	productID := get("productid")
	productName := truncate(get("productname"), 160, "ProductName")
	modelNumber := truncate(get("modelnumber"), 80, "ModelNumber")
	// MAPPING FIX: CSV 'ProductPrice' -> DB 'Product.UnitPrice'
	productUnitPrice := floatOrWarn(get("productprice"), "Product.UnitPrice")
	productDesc := get("productdescription")

	warehouseID := get("warehouseid")
	warehouseStreet := truncate(get("warehousestreetaddress"), 200, "WarehouseStreetAddress")
	warehouseZip := truncate(get("warehousezipcode"), 20, "WarehouseZipCode")
	warehouseCap := intOrWarn(get("warehousecapacity"), "WarehouseCapacity")

	// WarehouseProductStock fields
	stockLevel := intOrWarn(get("stocklevel"), "StockLevel")
	restockThreshold := intOrWarn(get("restockthreshold"), "RestockThreshold")
	lastRestockDate := parseDate(get("lastrestockdate"), "LastRestockDate")
	lastUpdateDate := parseDate(get("lastupdated"), "LastUpdated")

	dcID := get("distributioncenterid")
	dcRegion := truncate(get("region"), 60, "Region")
	dcStreet := truncate(get("distributioncenterstreetaddress"), 200, "DistributionCenterStreetAddress")
	dcZip := truncate(get("distributioncenterzipcode"), 20, "DistributionCenterZipCode")
	dcFleet := intOrWarn(get("fleetsize"), "FleetSize")

	orderID := get("orderid")
	quantity := intOrWarn(get("quantity"), "Quantity")
	// CSV 'UnitPrice' -> DB 'Order.UnitPrice'
	orderUnitPrice := floatOrWarn(get("unitprice"), "Order.UnitPrice")
	discount := floatOrWarn(get("discountamount"), "DiscountAmount")
	promoCode := truncate(get("promocode"), 80, "PromoCode")
	tax := floatOrWarn(get("taxamount"), "TaxAmount")
	shippingCost := floatOrWarn(get("shippingcost"), "ShippingCost")
	cogs := floatOrWarn(get("costofgoods"), "CostOfGoods") // Likely empty in CSV
	total := floatOrWarn(get("totalamount"), "TotalAmount")
	orderDate := parseDate(get("orderdate"), "OrderDate")
	expectedDate := parseDate(get("expecteddeliverydate"), "ExpectedDeliveryDate")
	actualDate := parseDate(get("actualdeliverydate"), "ActualDeliveryDate")
	deliveryStatus := truncate(get("deliverystatus"), 40, "DeliveryStatus")
	paymentMethod := truncate(get("paymentmethod"), 20, "PaymentMethod")
	cardNumber := truncate(get("cardnumber"), 30, "CardNumber")
	cardBrand := truncate(get("cardbrand"), 40, "CardBrand")
	// billZip already parsed
	// MAPPING FIX: CSV 'DeliveryAddress' -> DB 'DeliveryStreetAddress'
	deliveryStreet := truncate(get("deliveryaddress"), 200, "DeliveryStreetAddress")
	deliveryZip := truncate(get("deliveryzipcode"), 20, "DeliveryZipCode")
	shippingCarrier := truncate(get("shippingcarrier"), 80, "ShippingCarrier")

	reviewID := get("reviewid")
	// CSV 'ReviewRating' -> DB 'ProductRating'
	reviewRating := intOrWarn(get("reviewrating"), "ProductRating")
	reviewText := get("reviewtext")
	reviewDate := parseDate(get("reviewdate"), "ReviewDate")
	reviewSentiment := truncate(get("reviewsentiment"), 20, "ReviewSentiment")

	// Insert into each table
	execTrace(tx, "Customer",
		`INSERT INTO robot_vacuum_depot."Customer"
        ("CustomerID", "CustomerName", "CustomerEmail", "CustomerStreetAddress", "CustomerZipCode", "BillingZipCode", "Segment")
        VALUES ($1,$2,$3,$4,$5,$6,$7)
        ON CONFLICT ("CustomerID") DO NOTHING;`,
		customerID, customerName, customerEmail, customerStreet, customerZip, billingZip, segment)

	execTrace(tx, "Manufacturer",
		`INSERT INTO robot_vacuum_depot."Manufacturer"
        ("ManufacturerID", "ManufacturerName", "Country", "LeadTimeDays", "ReliabilityScore")
        VALUES ($1,$2,$3,$4,$5)
        ON CONFLICT ("ManufacturerID") DO NOTHING;`,
		manufacturerID, manufacturerName, country, leadTime, reliability)

	execTrace(tx, "Product",
		`INSERT INTO robot_vacuum_depot."Product"
        ("ProductID", "ProductName", "ModelNumber", "ManufacturerID", "UnitPrice", "ProductDescription")
        VALUES ($1,$2,$3,$4,$5,$6)
        ON CONFLICT ("ProductID") DO NOTHING;`,
		productID, productName, modelNumber, manufacturerID, productUnitPrice, productDesc)

	execTrace(tx, "Warehouse",
		`INSERT INTO robot_vacuum_depot."Warehouse"
        ("WarehouseID", "WarehouseStreetAddress", "WarehouseZipCode", "WarehouseCapacity")
        VALUES ($1,$2,$3,$4)
        ON CONFLICT ("WarehouseID") DO NOTHING;`,
		warehouseID, warehouseStreet, warehouseZip, warehouseCap)

	execTrace(tx, "DistributionCenter",
		`INSERT INTO robot_vacuum_depot."DistributionCenter"
        ("DistributionCenterID", "Region", "DistributionCenterStreetAddress", "DistributionCenterZipCode", "FleetSize")
        VALUES ($1,$2,$3,$4,$5)
        ON CONFLICT ("DistributionCenterID") DO NOTHING;`,
		dcID, dcRegion, dcStreet, dcZip, dcFleet)

	// Insert into WarehouseDistributionCenter bridge table
	if warehouseID != "" && dcID != "" {
		execTrace(tx, "WarehouseDistributionCenter",
			`INSERT INTO robot_vacuum_depot."WarehouseDistributionCenter"
            ("WarehouseID", "DistributionCenterID")
            VALUES ($1,$2)
            ON CONFLICT ("WarehouseID", "DistributionCenterID") DO NOTHING;`,
			warehouseID, dcID)
	}

	// Insert into WarehouseProductStock
	if warehouseID != "" && productID != "" {
		execTrace(tx, "WarehouseProductStock",
			`INSERT INTO robot_vacuum_depot."WarehouseProductStock"
            ("WarehouseID", "ProductID", "StockLevel", "RestockThreshold", "LastRestockDate", "LastUpdateDate")
            VALUES ($1,$2,$3,$4,$5,$6)
            ON CONFLICT ("WarehouseID", "ProductID") DO NOTHING;`,
			warehouseID, productID, stockLevel, restockThreshold, lastRestockDate, lastUpdateDate)
	}

	execTrace(tx, "Order",
		`INSERT INTO robot_vacuum_depot."Order"
        ("OrderID", "CustomerID", "ProductID", "WarehouseID", "DistributionCenterID",
        "Quantity", "UnitPrice", "DiscountAmount", "PromoCode", "TaxAmount", "ShippingCost",
        "CostOfGoods", "TotalAmount", "OrderDate", "ExpectedDeliveryDate", "ActualDeliveryDate",
        "DeliveryStatus", "PaymentMethod", "CardNumber", "CardBrand", "BillingZipCode",
        "DeliveryStreetAddress", "DeliveryZipCode", "ShippingCarrier")
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24)
        ON CONFLICT ("OrderID") DO NOTHING;`,
		orderID, customerID, productID, warehouseID, dcID,
		quantity, orderUnitPrice, discount, promoCode, tax, shippingCost,
		cogs, total, orderDate, expectedDate, actualDate,
		deliveryStatus, paymentMethod, cardNumber, cardBrand, billingZip,
		deliveryStreet, deliveryZip, shippingCarrier)

	if reviewID != "" {
		execTrace(tx, "Review",
			`INSERT INTO robot_vacuum_depot."Review"
            ("ReviewID", "OrderID", "CustomerID", "ProductID", "ProductRating", "ReviewText", "ReviewDate", "ReviewSentiment")
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            ON CONFLICT ("ReviewID") DO NOTHING;`,
			reviewID, orderID, customerID, productID, reviewRating, reviewText, reviewDate, reviewSentiment)
	}

	return nil
}

func execTrace(tx *sql.Tx, table, query string, args ...interface{}) {
	if _, err := tx.Exec(query, args...); err != nil {
		log.Printf("X insert %s: %v", table, err)
		// for i, a := range args {
		// 	log.Printf("  ▸ arg[%d]: %#v", i, a)
		// }
	}
}
