# LEARN-003: Qualitative Research Methods Applicable to Knowledge Systems
<!-- type: LEARN -->
<!-- created: 2026-02-14 -->
<!-- source: Robert E. Stake "Qualitative Research: Studying How Things Work" (2010, Guilford Press) -->
<!-- confidence: MEDIUM — academic framework, not directly about LLM memory, but transferable concepts -->

## Why This Matters
Our brain system is essentially a qualitative research tool — it ingests sources, deduplicates, triangulates findings, progressively focuses on what matters, and synthesizes knowledge. Stake's methodology formalizes several things we do intuitively and suggests improvements.

## Transferable Concepts

### 1. Triangulation
**Definition:** Using multiple data sources/methods to confirm or differentiate a finding. Not just confirmation — discovering *disagreement* is equally valuable because it reveals complexity.

**Four rules for when to triangulate:**
- Trivial/obvious claims → skip
- Relevant but debatable → some triangulation
- Core assertions → must triangulate
- Personal interpretation → triangulate the *validity*, not the statement itself

**Application to brain system:** Our dedup process already does this — when LEARN-002 (Turtle Soup) was corroborated by Ehrlich17, that's triangulation. We should formalize: any finding from a single source is "unconfirmed"; findings confirmed by 2+ independent sources are "corroborated." The INDEX-MASTER fat entries could carry a confidence indicator.

### 2. Progressive Focusing
**Definition:** Start broad, then systematically narrow to emerging issues. Don't commit to a fixed structure too early.

Three stages: (1) observe broadly, (2) inquire further into emerging patterns, (3) seek to explain.

Key warning from Miles & Huberman (1984): "Putting all conceptualization together at the beginning would be a serious mistake. It rules out the possibility of collecting new data to fill in gaps or test new hypotheses."

**Application to brain system:** This is exactly what our ingestion process does — we scan broadly, grep for relevant sections, read deeply, then deposit only what passes dedup. The SESSION-HANDOFF's "open questions" list is our progressive focusing tracker. Could formalize this into a FOCUS file type that evolves across sessions.

### 3. Concept Mapping
**Definition:** Visual/spatial representation of how concepts relate, with distance = association strength and area = importance.

Key insight: "A researcher fails to find relevant literature in other disciplines because they have not considered that other disciplines use different terms for the same concept."

**Application to brain system:** Our INDEX-MASTER is a flat list. A concept map overlay could help LLMs navigate related knowledge that's filed under different names (e.g., "volatility squeeze" in LEARN-003 is the same concept as "dull period + volume" in LEARN-004 Rule 2, but they're filed separately). Cross-references partially solve this, but a concept map would be more systematic.

### 4. Member Checking
**Definition:** Present findings back to the source for correction and comment. Reduces errors, protects subjects, and often reveals complexity.

**Application to brain system:** Analogous to our user reviewing deposits before they're committed. The INIT.md instruction "present what you plan to deposit for approval" is a form of member checking. Could also apply to periodic brain audits — re-reading old LEARN files to check if they still hold up against newer knowledge.

### 5. Coding and Progressive Recoding
**Definition:** Classify all data by topics/themes/issues. Code categories change as the research question evolves, meaning already-coded data may need recoding.

**Application to brain system:** Our file type system (SPEC/CODE/RULE/LEARN/LOG) is a coding scheme. As projects mature, LEARN files may need reclassification (a LEARN might become a RULE, or two LEARNs might merge). The INDEX-MASTER update process handles this but we haven't formalized "recoding triggers."

### 6. Data Storage Tips (Box 8.2)
Stake's practical tips that map directly to our system:
- Keep a research log (= SESSION-HANDOFF.md)
- Link storage to data gathering and writing (= our file-per-finding approach)
- Too few files AND too many files are both mistakes (= our consolidation vs. splitting judgment)
- Major records should be duplicated (= git versioning, once implemented)
- Records needing discussion should be marked (= "Known issues" in fat index entries)
- Memory is important storage — keep a good log with names, dates, musings (= our fat index summaries serve this exact function)

## Concepts Scanned But NOT Deposited
- Thick description (Geertz) — interesting but more about narrative writing than knowledge storage
- Multiple realities — philosophical stance on subjectivity, not actionable for our system
- Evidence-based decision making chapter — too focused on social science policy, not transferable
- Specific case studies (Seals marital counseling, Grogan math teaching) — illustrative but domain-specific

## Action Taken
Deposited as meta-knowledge for brain system design. Three actionable improvements identified:
1. Add confidence indicator to fat index entries (unconfirmed / corroborated / validated)
2. Consider a FOCUS file type for progressive focusing across sessions
3. Concept map overlay for INDEX-MASTER (deferred until file count grows)

## Cross-References
- SPEC-000 (brain architecture — these concepts inform the methodology)
- LEARN-001 (semantic compression — complementary approach to knowledge organization)
- LEARN-002 (competitive landscape — triangulation validates our corroboration approach)
