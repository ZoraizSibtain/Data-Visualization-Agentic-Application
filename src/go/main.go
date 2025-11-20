package main

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/lib/pq"
)

func main() {
	// Connection parameters
	host := "127.0.0.1" // safer than localhost on Windows
	port := 5432
	user := "postgres"
	password := "root"
	dbname := "robotvacuum"

	// Construct connection string (fmt.Sprintf)
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		host, port, user, password, dbname)

	// Open the connection
	db, err := sql.Open("postgres", psqlInfo)
	if err != nil {
		log.Fatalf("Error opening database: %v", err)
	}
	defer db.Close()

	// Verify connection works
	err = db.Ping()
	if err != nil {
		log.Fatalf("Cannot connect to database: %v", err)
	}

	fmt.Println("Connected to PostgreSQL successfully!")

	// Example: create schema to test
	_, err = db.Exec("CREATE SCHEMA IF NOT EXISTS robot_vacuum_depot;")
	if err != nil {
		log.Fatalf("Error creating schema: %v", err)
	}
	fmt.Println("Schema created successfully.")
}
