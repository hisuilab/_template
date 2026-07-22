package resolver_test

import (
	"testing"

	"github.com/hisuilab/_template/poc-go/internal/models"
	"github.com/hisuilab/_template/poc-go/internal/resolver"
)

func makepart(id string, requires ...string) *models.PartSchema {
	return &models.PartSchema{ID: id, Layer: "base", Requires: requires}
}

func TestResolve_SinglePart(t *testing.T) {
	parts := []*models.PartSchema{makepart("base")}
	out, err := resolver.Resolve(parts)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(out) != 1 || out[0].ID != "base" {
		t.Errorf("expected [base], got %v", ids(out))
	}
}

func TestResolve_TopologicalOrder(t *testing.T) {
	// b requires a — a must come first
	a := makepart("a")
	b := makepart("b", "a")
	out, err := resolver.Resolve([]*models.PartSchema{b, a})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(out) != 2 {
		t.Fatalf("expected 2 parts, got %d", len(out))
	}
	if out[0].ID != "a" || out[1].ID != "b" {
		t.Errorf("expected [a, b], got %v", ids(out))
	}
}

func TestResolve_CircularDependency(t *testing.T) {
	a := makepart("a", "b")
	b := makepart("b", "a")
	_, err := resolver.Resolve([]*models.PartSchema{a, b})
	if err == nil {
		t.Fatal("expected circular dependency error")
	}
}

func TestResolve_MissingRequires(t *testing.T) {
	a := makepart("a", "missing")
	_, err := resolver.Resolve([]*models.PartSchema{a})
	if err == nil {
		t.Fatal("expected missing requires error")
	}
}

func TestResolve_Conflict(t *testing.T) {
	a := &models.PartSchema{ID: "a", Layer: "lang", Conflicts: []string{"b"}}
	b := makepart("b")
	_, err := resolver.Resolve([]*models.PartSchema{a, b})
	if err == nil {
		t.Fatal("expected conflict error")
	}
}

func ids(parts []*models.PartSchema) []string {
	out := make([]string, len(parts))
	for i, p := range parts {
		out[i] = p.ID
	}
	return out
}
