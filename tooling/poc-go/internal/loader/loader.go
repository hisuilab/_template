// Package loader implements the LOAD stage: deserialize profile.toml and part.toml files.
package loader

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/BurntSushi/toml"
	"github.com/hisuilab/_template/poc-go/internal/models"
)

// profileTOML mirrors the TOML structure of template/profiles/<id>.toml.
type profileTOML struct {
	Profile struct {
		Name     string   `toml:"name"`
		Summary  string   `toml:"summary"`
		Category string   `toml:"category"`
		Parts    []string `toml:"parts"`
	} `toml:"profile"`
	Variables map[string]string `toml:"variables"`
}

// partTOML mirrors the TOML structure of template/parts/<id>/part.toml.
type partTOML struct {
	Part struct {
		ID        string   `toml:"id"`
		Layer     string   `toml:"layer"`
		Summary   string   `toml:"summary"`
		Requires  []string `toml:"requires"`
		Conflicts []string `toml:"conflicts"`
	} `toml:"part"`
	Placeholders struct {
		Required []string `toml:"required"`
	} `toml:"placeholders"`
	Files []struct {
		Path     string `toml:"path"`
		Strategy string `toml:"strategy"`
	} `toml:"files"`
}

var validCategories = map[string]bool{"cli": true, "web": true, "library": true}

// LoadProfile reads and validates template/profiles/<profileID>.toml.
func LoadProfile(profileID, templateRoot string) (*models.ProfileSchema, error) {
	path := filepath.Join(templateRoot, "profiles", profileID+".toml")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			available, _ := listProfiles(templateRoot)
			return nil, fmt.Errorf("profile %q not found (looked at %s). Available: %s",
				profileID, path, strings.Join(available, ", "))
		}
		return nil, fmt.Errorf("reading profile %q: %w", profileID, err)
	}

	var raw profileTOML
	if err := toml.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("parsing profile %q: %w", profileID, err)
	}

	if !validCategories[raw.Profile.Category] {
		return nil, fmt.Errorf("profile %q: invalid category %q (must be cli|web|library)", profileID, raw.Profile.Category)
	}
	if len(raw.Profile.Parts) == 0 {
		return nil, fmt.Errorf("profile %q: parts must be a non-empty list", profileID)
	}

	vars := raw.Variables
	if vars == nil {
		vars = map[string]string{}
	}

	return &models.ProfileSchema{
		Name:      raw.Profile.Name,
		Summary:   raw.Profile.Summary,
		Category:  raw.Profile.Category,
		Parts:     raw.Profile.Parts,
		Variables: vars,
	}, nil
}

// LoadPart reads and validates template/parts/<partID>/part.toml.
func LoadPart(partID, templateRoot string) (*models.PartSchema, error) {
	path := filepath.Join(templateRoot, "parts", partID, "part.toml")
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			available, _ := listParts(templateRoot)
			return nil, fmt.Errorf("part %q not found (looked at %s). Available: %s",
				partID, path, strings.Join(available, ", "))
		}
		return nil, fmt.Errorf("reading part %q: %w", partID, err)
	}

	var raw partTOML
	if err := toml.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("parsing part %q: %w", partID, err)
	}

	if raw.Part.ID != partID {
		return nil, fmt.Errorf("part.toml declares id=%q but is located in directory %q (they must match)",
			raw.Part.ID, partID)
	}

	files := make([]models.FileRule, 0, len(raw.Files))
	for _, f := range raw.Files {
		strategy := f.Strategy
		if strategy == "" {
			strategy = "error"
		}
		files = append(files, models.FileRule{Path: f.Path, Strategy: strategy})
	}

	return &models.PartSchema{
		ID:                   raw.Part.ID,
		Layer:                raw.Part.Layer,
		Summary:              raw.Part.Summary,
		Requires:             raw.Part.Requires,
		Conflicts:            raw.Part.Conflicts,
		PlaceholdersRequired: raw.Placeholders.Required,
		Files:                files,
	}, nil
}

// LoadPartsForProfile loads all parts declared in a profile.
func LoadPartsForProfile(profile *models.ProfileSchema, templateRoot string) ([]*models.PartSchema, error) {
	parts := make([]*models.PartSchema, 0, len(profile.Parts))
	for _, id := range profile.Parts {
		p, err := LoadPart(id, templateRoot)
		if err != nil {
			return nil, err
		}
		parts = append(parts, p)
	}
	return parts, nil
}

// StarterLangParts returns composite part IDs like "starter/cli-python" when they exist on disk.
func StarterLangParts(profileParts []string, lang, templateRoot string) []string {
	var result []string
	for _, partID := range profileParts {
		if strings.HasPrefix(partID, "starter/") {
			candidate := partID + "-" + lang
			candidatePath := filepath.Join(templateRoot, "parts", candidate, "part.toml")
			if _, err := os.Stat(candidatePath); err == nil {
				result = append(result, candidate)
			}
		}
	}
	return result
}

func listProfiles(templateRoot string) ([]string, error) {
	dir := filepath.Join(templateRoot, "profiles")
	entries, err := os.ReadDir(dir)
	if err != nil {
		return nil, err
	}
	var names []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasSuffix(e.Name(), ".toml") {
			names = append(names, strings.TrimSuffix(e.Name(), ".toml"))
		}
	}
	return names, nil
}

func listParts(templateRoot string) ([]string, error) {
	var names []string
	root := filepath.Join(templateRoot, "parts")
	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() && info.Name() == "part.toml" {
			rel, _ := filepath.Rel(root, filepath.Dir(path))
			names = append(names, filepath.ToSlash(rel))
		}
		return nil
	})
	return names, err
}
