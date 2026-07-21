// Generated placeholder — delete when you add real code
package main

import (
	"log/slog"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load(); err != nil {
		slog.Info("no .env file found, using system environment variables")
	}

	r := chi.NewRouter()
	r.Get("/health", func(w http.ResponseWriter, _ *http.Request) {
		_, _ = w.Write([]byte("ok"))
	})

	slog.Info("listening", "addr", ":3000")
	if err := http.ListenAndServe(":3000", r); err != nil {
		slog.Error("server error", "error", err)
	}
}
