# LINK-INDEX
<!-- type: LINK-INDEX -->
<!-- updated: 2026-02-20 -->
<!-- total-edges: 287 -->
<!-- total-nodes: 66 -->
<!-- seed-nodes: S000,L002,L005 (depth 0) -->
<!-- format: source|target|type|hop-depth -->
<!-- types: extends,implements,validates,informs,specifies,grounds,records,supersedes,contradicts -->

## How to Use
1. Search by source or target to find related files
2. hop-depth = BFS distance from seed nodes (S000,L002,L005)
3. type = relationship classification (extends=default)
4. Use brain.py parse_link_index() to query programmatically

## Relationship Types
- **extends**: builds on or references (default)
- **implements**: CODE edges, concrete realization
- **validates**: convergence/confirmation evidence
- **informs**: LEARN->SPEC, knowledge shaping design
- **specifies**: SPEC->RULE, design constraining behavior
- **grounds**: RULE->LEARN, rule justified by knowledge
- **records**: LOG->any, historical documentation
- **supersedes**: newer replaces older
- **contradicts**: conflicting claims (see Tensions in INDEX-MASTER)

---

## Summary
- Edges: 287
- Nodes: 66
- Max hop-depth: 2
- Avg edges/node: 4.3
- Types: extends=161, validates=45, informs=43, grounds=12, implements=8, supersedes=8, records=7, specifies=3
- Depth: d0=3, d1=48, d2=15

---

## Edges

CODE-001|LEARN-013|implements|1
CODE-001|LEARN-028|implements|1
CODE-001|LEARN-030|implements|1
CODE-001|LEARN-040|implements|1
CODE-001|SPEC-000|implements|1
LEARN-001|SPEC-000|informs|1
LEARN-002|LEARN-001|validates|1
LEARN-002|LOG-001|validates|1
LEARN-002|SPEC-000|validates|0
LEARN-003|LEARN-001|extends|1
LEARN-003|LEARN-002|extends|1
LEARN-003|SPEC-000|informs|1
LEARN-004|LEARN-001|validates|1
LEARN-004|LEARN-002|validates|1
LEARN-004|SPEC-000|validates|1
LEARN-005|LEARN-004|supersedes|1
LEARN-005|LEARN-013|supersedes|1
LEARN-005|LEARN-014|supersedes|1
LEARN-005|LEARN-017|supersedes|1
LEARN-005|LEARN-018|supersedes|1
LEARN-005|SPEC-000|supersedes|0
LEARN-006|LEARN-004|validates|1
LEARN-006|LEARN-005|validates|1
LEARN-006|SPEC-000|validates|1
LEARN-007|LEARN-005|extends|1
LEARN-007|LEARN-006|extends|1
LEARN-007|SPEC-000|informs|1
LEARN-008|LEARN-005|extends|1
LEARN-008|LEARN-007|extends|1
LEARN-008|LEARN-015|extends|1
LEARN-008|LEARN-016|extends|1
LEARN-008|SPEC-000|informs|1
LEARN-009|LEARN-005|validates|1
LEARN-009|LEARN-007|validates|1
LEARN-009|SPEC-000|validates|1
LEARN-010|LEARN-005|extends|1
LEARN-010|LEARN-006|extends|1
LEARN-010|LEARN-013|extends|1
LEARN-010|LEARN-014|extends|1
LEARN-010|LEARN-017|extends|1
LEARN-010|SPEC-000|informs|1
LEARN-011|LEARN-002|validates|1
LEARN-011|LEARN-006|validates|1
LEARN-011|LEARN-009|validates|1
LEARN-011|SPEC-000|validates|1
LEARN-012|LOG-002|extends|1
LEARN-012|SPEC-000|informs|1
LEARN-013|LEARN-002|validates|1
LEARN-013|LEARN-005|validates|1
LEARN-013|LEARN-008|validates|1
LEARN-013|LEARN-010|validates|1
LEARN-013|SPEC-000|validates|1
LEARN-014|LEARN-005|extends|1
LEARN-014|LEARN-010|extends|1
LEARN-014|LEARN-013|extends|1
LEARN-014|SPEC-000|informs|1
LEARN-015|LEARN-005|extends|1
LEARN-015|LEARN-009|extends|1
LEARN-015|SPEC-000|informs|1
LEARN-016|LEARN-005|extends|1
LEARN-016|LEARN-007|extends|1
LEARN-016|LEARN-008|extends|1
LEARN-016|LEARN-009|extends|1
LEARN-016|LEARN-013|extends|1
LEARN-016|SPEC-000|informs|1
LEARN-017|LEARN-004|extends|1
LEARN-017|LEARN-005|extends|1
LEARN-017|LEARN-006|extends|1
LEARN-017|LEARN-010|extends|1
LEARN-017|SPEC-000|informs|1
LEARN-018|LEARN-005|extends|1
LEARN-018|LEARN-010|extends|1
LEARN-018|LEARN-014|extends|1
LEARN-018|LEARN-017|extends|1
LEARN-018|SPEC-000|informs|1
LEARN-019|LEARN-005|extends|1
LEARN-019|LEARN-006|extends|1
LEARN-019|LEARN-007|extends|1
LEARN-019|LEARN-008|extends|1
LEARN-019|LOG-003|extends|1
LEARN-019|SPEC-000|informs|1
LEARN-020|LEARN-001|extends|1
LEARN-020|LEARN-002|extends|1
LEARN-020|SPEC-000|informs|1
LEARN-021|LEARN-002|validates|1
LEARN-021|LEARN-020|validates|1
LEARN-021|SPEC-000|validates|1
LEARN-022|LEARN-002|extends|1
LEARN-022|LEARN-020|extends|1
LEARN-022|SPEC-000|informs|1
LEARN-023|LEARN-002|extends|1
LEARN-023|LEARN-013|extends|1
LEARN-023|LEARN-021|extends|1
LEARN-023|SPEC-000|informs|1
LEARN-024|LEARN-002|extends|1
LEARN-024|LEARN-004|extends|1
LEARN-024|LEARN-005|extends|1
LEARN-024|LEARN-011|extends|1
LEARN-024|SPEC-000|informs|1
LEARN-025|SPEC-000|informs|1
LEARN-025|SPEC-001|informs|1
LEARN-026|LEARN-002|extends|1
LEARN-026|LEARN-009|extends|1
LEARN-026|LEARN-015|extends|1
LEARN-026|LEARN-021|extends|1
LEARN-026|LEARN-024|extends|1
LEARN-026|SPEC-001|informs|1
LEARN-027|LEARN-009|extends|2
LEARN-027|LEARN-015|extends|2
LEARN-027|LEARN-024|extends|2
LEARN-027|LEARN-026|extends|2
LEARN-027|SPEC-001|informs|2
LEARN-028|LEARN-002|extends|1
LEARN-028|LEARN-013|extends|1
LEARN-028|LEARN-023|extends|1
LEARN-028|SPEC-001|informs|1
LEARN-029|LEARN-018|extends|2
LEARN-029|LEARN-024|extends|2
LEARN-029|SPEC-001|informs|2
LEARN-030|LEARN-021|extends|1
LEARN-030|LEARN-023|extends|1
LEARN-030|SPEC-000|informs|1
LEARN-031|LEARN-002|validates|1
LEARN-031|LEARN-003|validates|1
LEARN-031|LEARN-012|validates|1
LEARN-031|SPEC-000|validates|1
LEARN-032|LEARN-002|extends|1
LEARN-032|LEARN-003|extends|1
LEARN-032|LEARN-011|extends|1
LEARN-032|LEARN-031|extends|1
LEARN-032|SPEC-000|informs|1
LEARN-032|SPEC-003|informs|1
LEARN-033|LEARN-011|extends|1
LEARN-033|LEARN-031|extends|1
LEARN-033|LEARN-032|extends|1
LEARN-033|SPEC-000|informs|1
LEARN-033|SPEC-003|informs|1
LEARN-034|LEARN-010|extends|1
LEARN-034|LEARN-019|extends|1
LEARN-034|LEARN-032|extends|1
LEARN-034|SPEC-000|informs|1
LEARN-034|SPEC-003|informs|1
LEARN-037|LEARN-014|extends|2
LEARN-037|LEARN-026|extends|2
LEARN-037|LEARN-027|extends|2
LEARN-037|SPEC-001|informs|2
LEARN-038|LEARN-026|extends|2
LEARN-038|LEARN-027|extends|2
LEARN-038|LEARN-037|extends|2
LEARN-038|SPEC-001|informs|2
LEARN-039|LEARN-005|extends|1
LEARN-039|LEARN-009|extends|1
LEARN-039|LEARN-010|extends|1
LEARN-039|LEARN-014|extends|1
LEARN-039|LEARN-038|extends|2
LEARN-040|LEARN-002|extends|1
LEARN-040|LEARN-013|extends|1
LEARN-040|LEARN-024|extends|1
LEARN-040|LEARN-028|extends|1
LEARN-040|LEARN-030|extends|1
LEARN-040|LEARN-031|extends|1
LEARN-040|SPEC-000|informs|1
LEARN-040|SPEC-001|informs|1
LEARN-041|CODE-001|implements|2
LEARN-041|LEARN-013|supersedes|2
LEARN-041|LEARN-019|supersedes|2
LEARN-042|LEARN-010|extends|2
LEARN-042|LEARN-019|extends|2
LEARN-042|RULE-001|extends|2
LEARN-043|LEARN-001|extends|2
LEARN-044|LEARN-001|extends|1
LEARN-044|LEARN-002|extends|1
LEARN-044|LEARN-023|extends|1
LEARN-044|LEARN-030|extends|1
LEARN-044|LEARN-040|extends|1
LEARN-044|SPEC-000|informs|1
LEARN-044|SPEC-003|informs|1
LEARN-045|LEARN-002|extends|1
LEARN-045|LEARN-044|extends|1
LEARN-045|SPEC-000|informs|1
LEARN-046|LEARN-030|extends|1
LEARN-046|LEARN-044|extends|1
LEARN-046|SPEC-000|informs|1
LEARN-047|LEARN-026|extends|2
LEARN-047|LEARN-027|extends|2
LEARN-047|LEARN-037|extends|2
LEARN-047|SPEC-001|informs|2
LEARN-048|LEARN-023|extends|1
LEARN-048|LEARN-030|extends|1
LEARN-048|LEARN-044|extends|1
LEARN-048|LEARN-046|extends|1
LEARN-048|SPEC-000|informs|1
LEARN-049|LEARN-030|extends|1
LEARN-049|LEARN-032|extends|1
LEARN-049|LEARN-044|extends|1
LEARN-049|LEARN-048|extends|1
LEARN-049|SPEC-000|informs|1
LEARN-050|LEARN-009|extends|1
LEARN-050|LEARN-023|extends|1
LEARN-050|LEARN-024|extends|1
LEARN-050|LEARN-031|extends|1
LEARN-050|LEARN-034|extends|1
LEARN-050|RULE-001|extends|2
LEARN-050|SPEC-000|informs|1
LEARN-051|LEARN-001|extends|2
LEARN-051|LEARN-024|extends|2
LEARN-051|LEARN-030|extends|2
LEARN-051|LEARN-040|extends|2
LEARN-051|LEARN-044|extends|2
LEARN-051|LEARN-048|extends|2
LEARN-051|SPEC-005|informs|2
LEARN-052|LEARN-002|extends|1
LEARN-052|LEARN-021|extends|1
LEARN-052|LEARN-040|extends|1
LEARN-052|LEARN-044|extends|1
LEARN-052|LEARN-051|extends|2
LEARN-052|RULE-005|extends|2
LEARN-052|SPEC-005|informs|1
LOG-001|SPEC-000|records|1
LOG-002|SPEC-000|records|1
LOG-003|LEARN-005|records|1
LOG-003|LEARN-006|records|1
LOG-003|LEARN-007|records|1
LOG-003|LEARN-008|records|1
LOG-003|SPEC-000|records|1
RULE-001|LEARN-008|validates|2
RULE-001|LEARN-019|validates|2
RULE-002|LEARN-005|grounds|1
RULE-002|LEARN-010|grounds|1
RULE-002|LEARN-018|grounds|1
RULE-003|LEARN-005|grounds|1
RULE-003|LEARN-007|grounds|1
RULE-003|LEARN-018|grounds|1
RULE-003|LEARN-019|grounds|1
RULE-004|LEARN-008|grounds|2
RULE-004|LEARN-019|grounds|2
RULE-004|RULE-001|extends|2
RULE-005|LEARN-034|grounds|2
RULE-005|RULE-002|extends|2
RULE-006|CODE-001|implements|2
RULE-006|LEARN-030|grounds|2
RULE-006|LEARN-041|grounds|2
SPEC-001|LEARN-009|validates|1
SPEC-001|LEARN-011|validates|1
SPEC-001|LEARN-015|validates|1
SPEC-001|LEARN-024|validates|1
SPEC-001|LEARN-025|validates|1
SPEC-001|LEARN-026|validates|1
SPEC-001|LEARN-027|validates|2
SPEC-001|LEARN-028|validates|1
SPEC-001|LEARN-029|validates|2
SPEC-001|LEARN-031|validates|1
SPEC-001|LEARN-037|validates|2
SPEC-001|SPEC-000|validates|1
SPEC-002|LEARN-025|validates|2
SPEC-002|LEARN-028|validates|2
SPEC-002|SPEC-001|validates|2
SPEC-003|LEARN-003|extends|1
SPEC-003|LEARN-031|extends|1
SPEC-003|LEARN-032|extends|1
SPEC-003|SPEC-000|extends|1
SPEC-004|LEARN-009|extends|2
SPEC-004|LEARN-026|extends|2
SPEC-004|LEARN-027|extends|2
SPEC-004|LEARN-047|extends|2
SPEC-004|RULE-005|specifies|2
SPEC-004|SPEC-001|extends|2
SPEC-005|CODE-001|implements|1
SPEC-005|LEARN-009|extends|1
SPEC-005|LEARN-023|extends|1
SPEC-005|LEARN-024|extends|1
SPEC-005|LEARN-030|extends|1
SPEC-005|LEARN-031|extends|1
SPEC-005|LEARN-032|extends|1
SPEC-005|LEARN-033|extends|1
SPEC-005|LEARN-034|extends|1
SPEC-005|LEARN-040|extends|1
SPEC-005|LEARN-044|extends|1
SPEC-005|LEARN-046|extends|1
SPEC-005|LEARN-048|extends|1
SPEC-005|LEARN-049|extends|1
SPEC-005|LEARN-050|extends|1
SPEC-005|LEARN-051|extends|2
SPEC-005|RULE-001|specifies|2
SPEC-005|RULE-005|specifies|2
SPEC-005|SPEC-000|extends|1
SPEC-005|SPEC-003|extends|1
