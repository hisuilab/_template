package preflight_test

import (
	"path/filepath"
	"runtime"
	"testing"

	"github.com/hisuilab/_template/poc-go/internal/models"
	"github.com/hisuilab/_template/poc-go/internal/preflight"
)

func templateRoot() string {
	_, filename, _, _ := runtime.Caller(0)
	// internal/preflight/preflight_test.go → ../../../../template
	// Dir: poc-go/internal/preflight/ → 4 levels up to repo root
	return filepath.Join(filepath.Dir(filename), "..", "..", "..", "..", "template")
}

func TestCheckRoles_AllValid(t *testing.T) {
	root := templateRoot()
	roles := []models.RoleSpec{
		{Name: "backend", Profile: "starter-web-api", Lang: "python"},
		{Name: "frontend", Profile: "starter-cli", Lang: "go"},
	}
	errs := preflight.CheckRoles(roles, root)
	if len(errs) != 0 {
		t.Errorf("expected no errors for valid roles, got: %v", errs)
	}
}

func TestCheckRoles_UnknownProfile(t *testing.T) {
	root := templateRoot()
	roles := []models.RoleSpec{
		{Name: "bad", Profile: "no-such-profile", Lang: "python"},
	}
	errs := preflight.CheckRoles(roles, root)
	if len(errs) == 0 {
		t.Fatal("expected error for unknown profile")
	}
}

func TestCheckRoles_UnknownLang(t *testing.T) {
	root := templateRoot()
	roles := []models.RoleSpec{
		{Name: "bad", Profile: "starter-cli", Lang: "cobol"},
	}
	errs := preflight.CheckRoles(roles, root)
	if len(errs) == 0 {
		t.Fatal("expected error for unknown lang")
	}
}

func TestCheckRoles_LangOmitted_IsValid(t *testing.T) {
	root := templateRoot()
	roles := []models.RoleSpec{
		{Name: "worker", Profile: "starter-cli", Lang: ""},
	}
	errs := preflight.CheckRoles(roles, root)
	if len(errs) != 0 {
		t.Errorf("expected no errors when lang is omitted, got: %v", errs)
	}
}

func TestCheckRoles_MultipleErrors(t *testing.T) {
	root := templateRoot()
	roles := []models.RoleSpec{
		{Name: "r1", Profile: "no-profile", Lang: "cobol"},
		{Name: "r2", Profile: "starter-cli", Lang: "python"},
	}
	errs := preflight.CheckRoles(roles, root)
	if len(errs) != 2 {
		t.Errorf("expected 2 errors, got %d: %v", len(errs), errs)
	}
}
