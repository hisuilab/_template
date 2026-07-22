// Command generate is a Go PoC that implements the LOAD→RESOLVE→PLAN pipeline
// for the _template generator. It does NOT perform RENDER or APPLY, so no
// user files are created or modified.
//
// Usage:
//
//	go run ./cmd/generate --name myapp --profile starter-cli [--lang python] [--template-root PATH]
//	go run ./cmd/generate --name myapp --role backend:profile=starter-web-api,lang=python \
//	                                   --role frontend:profile=starter-cli
package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"

	"github.com/hisuilab/_template/poc-go/internal/loader"
	"github.com/hisuilab/_template/poc-go/internal/models"
	"github.com/hisuilab/_template/poc-go/internal/planner"
	"github.com/hisuilab/_template/poc-go/internal/preflight"
	"github.com/hisuilab/_template/poc-go/internal/resolver"
)

// defaultTemplateRoot resolves the template/ directory relative to this source file's location.
func defaultTemplateRoot() string {
	_, filename, _, _ := runtime.Caller(0)
	// cmd/generate/main.go → ../../../../template
	return filepath.Join(filepath.Dir(filename), "..", "..", "..", "..", "template")
}

// roleFlag is a repeatable CLI flag (--role can appear multiple times).
type roleFlag []string

func (r *roleFlag) String() string { return strings.Join(*r, ", ") }
func (r *roleFlag) Set(v string) error {
	*r = append(*r, v)
	return nil
}

func main() {
	os.Exit(run())
}

func run() int {
	var (
		name        = flag.String("name", "", "Project name (required)")
		profile     = flag.String("profile", "", "Profile ID (e.g. starter-cli). Required unless --role is used")
		lang        = flag.String("lang", "", "Language (e.g. python, go, rust, typescript)")
		templateDir = flag.String("template-root", "", "Path to template/ directory (default: auto-detect from source)")
		roles       roleFlag
	)
	flag.Var(&roles, "role", "Role spec: name:profile=<p>[,lang=<l>]. Repeatable. Mutually exclusive with --profile/--lang")
	flag.Parse()

	if *name == "" {
		fmt.Fprintln(os.Stderr, "error: --name is required")
		return 1
	}

	templateRoot := *templateDir
	if templateRoot == "" {
		templateRoot = defaultTemplateRoot()
	}
	templateRoot = filepath.Clean(templateRoot)

	if len(roles) > 0 {
		return runPreflight(*name, roles, templateRoot)
	}

	if *profile == "" {
		fmt.Fprintln(os.Stderr, "error: --profile is required unless --role is used")
		return 1
	}

	return runGenerate(*name, *profile, *lang, templateRoot)
}

func runGenerate(name, profileID, lang, templateRoot string) int {
	fmt.Printf("LOAD: profile=%s lang=%s\n", profileID, lang)

	// LOAD
	prof, err := loader.LoadProfile(profileID, templateRoot)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error (LOAD): %v\n", err)
		return 1
	}
	fmt.Printf("  profile: %s (%s)\n", prof.Name, prof.Category)
	fmt.Printf("  base parts: %v\n", prof.Parts)

	// Inject lang parts
	allPartIDs := append([]string{}, prof.Parts...)
	if lang != "" {
		allPartIDs = append(allPartIDs, "lang/"+lang)
		extras := loader.StarterLangParts(prof.Parts, lang, templateRoot)
		allPartIDs = append(allPartIDs, extras...)
		fmt.Printf("  lang parts added: lang/%s %v\n", lang, extras)
	}

	parts, err := loader.LoadPartsForProfile(&models.ProfileSchema{
		Name:      prof.Name,
		Summary:   prof.Summary,
		Category:  prof.Category,
		Parts:     allPartIDs,
		Variables: prof.Variables,
	}, templateRoot)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error (LOAD parts): %v\n", err)
		return 1
	}
	fmt.Printf("  loaded %d part(s)\n", len(parts))

	// RESOLVE
	fmt.Println("RESOLVE: topological sort")
	resolved, err := resolver.Resolve(parts)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error (RESOLVE): %v\n", err)
		return 1
	}
	for i, p := range resolved {
		fmt.Printf("  [%d] %s\n", i, p.ID)
	}

	// PLAN
	fmt.Println("PLAN: variable binding and file list")
	request := models.GenerateRequest{
		Name:       name,
		ProfileID:  profileID,
		OutputPath: "(dry-run — no files written)",
		Lang:       lang,
	}
	gen, err := planner.Plan(request, resolved, templateRoot, prof.Variables)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error (PLAN): %v\n", err)
		return 1
	}
	fmt.Printf("  planned %d file(s)\n", len(gen.Files))
	fmt.Printf("  variables: %v\n", gen.Variables)

	fmt.Println("OK: LOAD→RESOLVE→PLAN completed successfully (dry-run, no files written)")
	return 0
}

func runPreflight(name string, roleStrs []string, templateRoot string) int {
	fmt.Printf("PREFLIGHT: validating %d role(s) for project %q\n", len(roleStrs), name)

	roles := make([]models.RoleSpec, 0, len(roleStrs))
	for _, s := range roleStrs {
		r, err := parseRole(s)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error: invalid --role format %q: %v\n", s, err)
			return 1
		}
		roles = append(roles, r)
	}

	errs := preflight.CheckRoles(roles, templateRoot)
	if len(errs) > 0 {
		for _, e := range errs {
			fmt.Fprintf(os.Stderr, "error: %v\n", e)
		}
		return 1
	}

	fmt.Printf("  all %d role(s) passed preflight validation\n", len(roles))
	for _, r := range roles {
		lang := r.Lang
		if lang == "" {
			lang = "(omitted)"
		}
		fmt.Printf("  role %q: profile=%s lang=%s\n", r.Name, r.Profile, lang)
	}
	fmt.Println("OK: preflight passed — no files written (generation not implemented in this PoC)")
	return 0
}

// parseRole parses "name:profile=<p>[,lang=<l>]" into a RoleSpec.
func parseRole(s string) (models.RoleSpec, error) {
	colonIdx := strings.Index(s, ":")
	if colonIdx < 0 {
		return models.RoleSpec{}, fmt.Errorf("expected 'name:profile=<p>[,lang=<l>]'")
	}
	roleName := s[:colonIdx]
	rest := s[colonIdx+1:]
	if roleName == "" {
		return models.RoleSpec{}, fmt.Errorf("role name must not be empty")
	}

	kv := make(map[string]string)
	for _, pair := range strings.Split(rest, ",") {
		eqIdx := strings.Index(pair, "=")
		if eqIdx < 0 {
			continue
		}
		kv[pair[:eqIdx]] = pair[eqIdx+1:]
	}

	profileVal := kv["profile"]
	if profileVal == "" {
		return models.RoleSpec{}, fmt.Errorf("profile= is required in role spec")
	}

	return models.RoleSpec{
		Name:    roleName,
		Profile: profileVal,
		Lang:    kv["lang"],
	}, nil
}
