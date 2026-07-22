package planner_test

import (
	"path/filepath"
	"runtime"
	"testing"

	"github.com/hisuilab/_template/poc-go/internal/loader"
	"github.com/hisuilab/_template/poc-go/internal/models"
	"github.com/hisuilab/_template/poc-go/internal/planner"
	"github.com/hisuilab/_template/poc-go/internal/resolver"
)

func templateRoot() string {
	_, filename, _, _ := runtime.Caller(0)
	// internal/planner/planner_test.go → ../../../../template
	// Dir: poc-go/internal/planner/ → 4 levels up to repo root
	return filepath.Join(filepath.Dir(filename), "..", "..", "..", "..", "template")
}

func TestPlan_StarterCliPython(t *testing.T) {
	root := templateRoot()

	prof, err := loader.LoadProfile("starter-cli", root)
	if err != nil {
		t.Fatalf("LoadProfile: %v", err)
	}

	// Add lang/python and starter/cli-python
	allPartIDs := append([]string{}, prof.Parts...)
	allPartIDs = append(allPartIDs, "lang/python")
	extras := loader.StarterLangParts(prof.Parts, "python", root)
	allPartIDs = append(allPartIDs, extras...)

	extendedProfile := &models.ProfileSchema{
		Name:      prof.Name,
		Summary:   prof.Summary,
		Category:  prof.Category,
		Parts:     allPartIDs,
		Variables: prof.Variables,
	}
	parts, err := loader.LoadPartsForProfile(extendedProfile, root)
	if err != nil {
		t.Fatalf("LoadPartsForProfile: %v", err)
	}

	resolved, err := resolver.Resolve(parts)
	if err != nil {
		t.Fatalf("Resolve: %v", err)
	}

	request := models.GenerateRequest{
		Name:       "myapp",
		ProfileID:  "starter-cli",
		OutputPath: "/tmp/test-output",
		Lang:       "python",
	}
	gen, err := planner.Plan(request, resolved, root, prof.Variables)
	if err != nil {
		t.Fatalf("Plan: %v", err)
	}

	if len(gen.Files) == 0 {
		t.Fatal("expected at least one planned file")
	}
	if gen.Variables["project_name"] != "myapp" {
		t.Errorf("expected project_name=myapp, got %q", gen.Variables["project_name"])
	}

	// flake.nix must be planned
	found := false
	for _, f := range gen.Files {
		if f.DestPath == "flake.nix" {
			found = true
		}
	}
	if !found {
		t.Error("expected flake.nix in planned files")
	}
}

func TestPlan_ProjectNameSubstituted(t *testing.T) {
	root := templateRoot()
	prof, _ := loader.LoadProfile("starter-cli", root)
	parts, _ := loader.LoadPartsForProfile(prof, root)
	resolved, _ := resolver.Resolve(parts)

	request := models.GenerateRequest{
		Name:      "coolproject",
		ProfileID: "starter-cli",
	}
	gen, err := planner.Plan(request, resolved, root, prof.Variables)
	if err != nil {
		t.Fatalf("Plan: %v", err)
	}

	if gen.Variables["project_name"] != "coolproject" {
		t.Errorf("expected project_name=coolproject, got %q", gen.Variables["project_name"])
	}
}

func TestPlan_NoPythonSrcWithoutLang(t *testing.T) {
	root := templateRoot()
	prof, _ := loader.LoadProfile("starter-cli", root)
	parts, _ := loader.LoadPartsForProfile(prof, root)
	resolved, _ := resolver.Resolve(parts)

	request := models.GenerateRequest{
		Name:      "nolanapp",
		ProfileID: "starter-cli",
	}
	gen, err := planner.Plan(request, resolved, root, prof.Variables)
	if err != nil {
		t.Fatalf("Plan: %v", err)
	}

	// Without --lang python, src/main.py must not appear
	for _, f := range gen.Files {
		if f.DestPath == "src/main.py" {
			t.Errorf("src/main.py must not appear in plan without --lang python")
		}
	}
}
