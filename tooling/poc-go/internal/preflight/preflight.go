// Package preflight validates all roles before any generation begins,
// mirroring the Python CLI's pre-generation validation for --role.
package preflight

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/hisuilab/_template/poc-go/internal/models"
)

// CheckRoles validates that each role's profile and lang exist on disk.
// It returns a list of errors (one per invalid role); nil means all valid.
// This mirrors _cmd_generate's preflight loop in cli.py.
func CheckRoles(roles []models.RoleSpec, templateRoot string) []error {
	availableProfiles := listProfiles(templateRoot)
	availableLangs := listLangs(templateRoot)

	profileSet := toSet(availableProfiles)
	langSet := toSet(availableLangs)

	var errs []error
	for _, role := range roles {
		if !profileSet[role.Profile] {
			errs = append(errs, fmt.Errorf("role %q: unknown profile %q. Available: %s",
				role.Name, role.Profile, strings.Join(availableProfiles, ", ")))
		}
		if role.Lang != "" && !langSet[role.Lang] {
			errs = append(errs, fmt.Errorf("role %q: unknown lang %q. Available: %s",
				role.Name, role.Lang, strings.Join(availableLangs, ", ")))
		}
	}
	return errs
}

func listProfiles(templateRoot string) []string {
	dir := filepath.Join(templateRoot, "profiles")
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil
	}
	var names []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".toml") {
			names = append(names, strings.TrimSuffix(e.Name(), ".toml"))
		}
	}
	sort.Strings(names)
	return names
}

func listLangs(templateRoot string) []string {
	dir := filepath.Join(templateRoot, "parts", "lang")
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil
	}
	var names []string
	for _, e := range entries {
		if e.IsDir() {
			names = append(names, e.Name())
		}
	}
	sort.Strings(names)
	return names
}

func toSet(items []string) map[string]bool {
	s := make(map[string]bool, len(items))
	for _, v := range items {
		s[v] = true
	}
	return s
}
