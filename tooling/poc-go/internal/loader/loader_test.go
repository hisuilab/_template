package loader_test

import (
	"path/filepath"
	"runtime"
	"testing"

	"github.com/hisuilab/_template/poc-go/internal/loader"
)

func templateRoot() string {
	_, filename, _, _ := runtime.Caller(0)
	// internal/loader/loader_test.go → ../../../../template
	// Dir: poc-go/internal/loader/ → 4 levels up to repo root
	return filepath.Join(filepath.Dir(filename), "..", "..", "..", "..", "template")
}

func TestLoadProfile_StarterCli(t *testing.T) {
	root := templateRoot()
	p, err := loader.LoadProfile("starter-cli", root)
	if err != nil {
		t.Fatalf("LoadProfile: %v", err)
	}
	if p.Name == "" {
		t.Error("expected non-empty name")
	}
	if p.Category != "cli" {
		t.Errorf("expected category=cli, got %q", p.Category)
	}
	if len(p.Parts) == 0 {
		t.Error("expected non-empty parts")
	}
}

func TestLoadProfile_NotFound(t *testing.T) {
	root := templateRoot()
	_, err := loader.LoadProfile("no-such-profile", root)
	if err == nil {
		t.Fatal("expected error for missing profile")
	}
}

func TestLoadPart_Base(t *testing.T) {
	root := templateRoot()
	p, err := loader.LoadPart("base", root)
	if err != nil {
		t.Fatalf("LoadPart: %v", err)
	}
	if p.ID != "base" {
		t.Errorf("expected id=base, got %q", p.ID)
	}
	if p.Layer == "" {
		t.Error("expected non-empty layer")
	}
}

func TestLoadPart_LangGo(t *testing.T) {
	root := templateRoot()
	p, err := loader.LoadPart("lang/go", root)
	if err != nil {
		t.Fatalf("LoadPart lang/go: %v", err)
	}
	if p.ID != "lang/go" {
		t.Errorf("expected id=lang/go, got %q", p.ID)
	}
}

func TestLoadPart_NotFound(t *testing.T) {
	root := templateRoot()
	_, err := loader.LoadPart("no-such-part", root)
	if err == nil {
		t.Fatal("expected error for missing part")
	}
}

func TestLoadPartsForProfile(t *testing.T) {
	root := templateRoot()
	prof, err := loader.LoadProfile("starter-cli", root)
	if err != nil {
		t.Fatalf("LoadProfile: %v", err)
	}
	parts, err := loader.LoadPartsForProfile(prof, root)
	if err != nil {
		t.Fatalf("LoadPartsForProfile: %v", err)
	}
	if len(parts) == 0 {
		t.Error("expected at least one part")
	}
	// base must be included
	found := false
	for _, p := range parts {
		if p.ID == "base" {
			found = true
		}
	}
	if !found {
		t.Error("expected 'base' part in starter-cli profile")
	}
}

func TestStarterLangParts(t *testing.T) {
	root := templateRoot()
	prof, _ := loader.LoadProfile("starter-cli", root)
	extras := loader.StarterLangParts(prof.Parts, "python", root)
	// starter/cli-python should exist
	found := false
	for _, e := range extras {
		if e == "starter/cli-python" {
			found = true
		}
	}
	if !found {
		t.Errorf("expected starter/cli-python in extras, got %v", extras)
	}
}
