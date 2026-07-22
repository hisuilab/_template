// Package resolver implements the RESOLVE stage: topological sort of Part dependencies.
package resolver

import (
	"fmt"

	"github.com/hisuilab/_template/poc-go/internal/models"
)

// Resolve returns parts in topological dependency order (requires satisfied before dependants).
// It also validates requires/conflicts before sorting.
func Resolve(parts []*models.PartSchema) ([]*models.PartSchema, error) {
	byID := make(map[string]*models.PartSchema, len(parts))
	for _, p := range parts {
		byID[p.ID] = p
	}

	// Validate requires
	for _, part := range parts {
		for _, req := range part.Requires {
			if _, ok := byID[req]; !ok {
				return nil, fmt.Errorf("part %q requires %q, which is not in the parts list", part.ID, req)
			}
		}
	}

	// Validate conflicts
	for _, part := range parts {
		for _, conflictID := range part.Conflicts {
			if _, ok := byID[conflictID]; ok {
				return nil, fmt.Errorf("part %q conflicts with %q: both cannot be used together", part.ID, conflictID)
			}
		}
	}

	result := make([]*models.PartSchema, 0, len(parts))
	visited := make(map[string]bool)
	inStack := make(map[string]bool)

	var visit func(id string) error
	visit = func(id string) error {
		if inStack[id] {
			return fmt.Errorf("circular dependency detected involving %q", id)
		}
		if visited[id] {
			return nil
		}
		inStack[id] = true
		for _, req := range byID[id].Requires {
			if err := visit(req); err != nil {
				return err
			}
		}
		delete(inStack, id)
		visited[id] = true
		result = append(result, byID[id])
		return nil
	}

	for _, part := range parts {
		if err := visit(part.ID); err != nil {
			return nil, err
		}
	}

	return result, nil
}
