// Package models defines data types used across the generator pipeline.
package models

import "path/filepath"

// ProfileSchema is the parsed and validated content of a profile.toml.
type ProfileSchema struct {
	Name      string
	Summary   string
	Category  string
	Parts     []string
	Variables map[string]string
}

// FileRule holds a non-default placement strategy for a single payload path.
type FileRule struct {
	Path     string
	Strategy string // "error" | "replace" | "add"
}

// PartSchema is the parsed and validated content of a part.toml.
type PartSchema struct {
	ID                   string
	Layer                string
	Summary              string
	Requires             []string
	Conflicts            []string
	PlaceholdersRequired []string
	Files                []FileRule
}

// PayloadRoot returns the filesystem path to this part's payload directory.
func (p *PartSchema) PayloadRoot(templateRoot string) string {
	return filepath.Join(templateRoot, "parts", p.ID, "payload")
}

// GenerateRequest captures a single generation task.
type GenerateRequest struct {
	Name       string
	ProfileID  string
	OutputPath string
	Lang       string // empty if no lang was requested
}

// PlannedFile is one file in the generation plan.
type PlannedFile struct {
	SrcPath  string // absolute path in the payload directory
	DestPath string // relative path in the output directory
	Strategy string
}

// GenerationPlan is the complete plan for one generation run.
type GenerationPlan struct {
	Request   GenerateRequest
	Variables map[string]string
	Files     []PlannedFile
}

// RoleSpec captures one --role entry for multi-role preflight.
type RoleSpec struct {
	Name    string
	Profile string
	Lang    string // empty if not specified
}
