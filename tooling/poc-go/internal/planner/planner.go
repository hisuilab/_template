// Package planner implements the PLAN stage: variable binding, file name
// transformation, and collision detection.
package planner

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/hisuilab/_template/poc-go/internal/models"
)

var placeholderRE = regexp.MustCompile(`\{\{(\w+)\}\}`)

const dotPrefix = "dot-"

var reserved = map[string]struct{}{"project_name": {}}

func substitute(text string, variables map[string]string) string {
	return placeholderRE.ReplaceAllStringFunc(text, func(m string) string {
		sub := placeholderRE.FindStringSubmatch(m)
		if len(sub) < 2 {
			return m
		}
		if v, ok := variables[sub[1]]; ok {
			return v
		}
		return m
	})
}

func stripDotPrefix(name string) string {
	if strings.HasPrefix(name, dotPrefix) {
		return "." + name[len(dotPrefix):]
	}
	return name
}

func transformPath(rel string, variables map[string]string) string {
	parts := strings.Split(filepath.ToSlash(rel), "/")
	result := make([]string, len(parts))
	for i, p := range parts {
		result[i] = stripDotPrefix(substitute(p, variables))
	}
	return strings.Join(result, "/")
}

func fileStrategy(part *models.PartSchema, destPath string) string {
	for _, rule := range part.Files {
		if rule.Path == destPath {
			return rule.Strategy
		}
	}
	return "error"
}

// Plan creates a GenerationPlan from the resolved parts and the generation request.
func Plan(
	request models.GenerateRequest,
	parts []*models.PartSchema,
	templateRoot string,
	profileVariables map[string]string,
) (*models.GenerationPlan, error) {
	variables := make(map[string]string)
	for k, v := range profileVariables {
		variables[k] = v
	}
	// Reserved keys always win
	variables["project_name"] = request.Name

	// Validate required placeholders
	for _, part := range parts {
		for _, ph := range part.PlaceholdersRequired {
			if _, ok := variables[ph]; !ok {
				return nil, fmt.Errorf("part %q requires placeholder {{%s}} but it was not provided", part.ID, ph)
			}
		}
	}

	planned := make(map[string]models.PlannedFile) // dest_path -> PlannedFile

	for _, part := range parts {
		payloadDir := filepath.Join(templateRoot, "parts", part.ID, "payload")
		err := filepath.Walk(payloadDir, func(path string, info os.FileInfo, err error) error {
			if err != nil {
				return err
			}
			if info.IsDir() {
				return nil
			}
			rel, err := filepath.Rel(payloadDir, path)
			if err != nil {
				return err
			}
			rel = filepath.ToSlash(rel)
			dest := transformPath(rel, variables)
			strategy := fileStrategy(part, dest)

			if existing, exists := planned[dest]; exists {
				if strategy == "replace" {
					planned[dest] = models.PlannedFile{SrcPath: path, DestPath: dest, Strategy: strategy}
				} else if strategy == "add" {
					_ = existing // keep first part's version
				} else {
					return fmt.Errorf("file %q is provided by multiple parts (use strategy='replace' to allow overwriting)", dest)
				}
			} else {
				planned[dest] = models.PlannedFile{SrcPath: path, DestPath: dest, Strategy: strategy}
			}
			return nil
		})
		if err != nil {
			if os.IsNotExist(err) {
				// Part has no payload directory — skip
				continue
			}
			return nil, fmt.Errorf("planning part %q: %w", part.ID, err)
		}
	}

	files := make([]models.PlannedFile, 0, len(planned))
	for _, f := range planned {
		files = append(files, f)
	}

	return &models.GenerationPlan{
		Request:   request,
		Variables: variables,
		Files:     files,
	}, nil
}
