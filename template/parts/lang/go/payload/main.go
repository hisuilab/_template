// Generated placeholder — delete when you add real code
package main

import (
	"fmt"
	"log/slog"

	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load(); err != nil {
		slog.Info("no .env file found, using system environment variables")
	}
	fmt.Println("Hello, {{project_name}}!")
}
