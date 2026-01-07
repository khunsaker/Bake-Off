# CT7: Visualization Assessment Guide

Subjective assessment of curation visualization tools for PostgreSQL vs Neo4j/Memgraph.

## Purpose

Evaluate the quality and usability of visualization tools from a curator's perspective. This is a qualitative assessment focusing on **curator productivity** and **ease of use**.

## Assessment Criteria

### 1. Relationship Visualization (Weight: 30%)

**Neo4j Bloom**
- [ ] Can visualize multi-hop relationships natively
- [ ] Interactive graph exploration (click to expand)
- [ ] Relationship labels visible
- [ ] Relationship properties displayed on hover
- [ ] Pattern-based search (visual query builder)

**PostgreSQL (pgAdmin/DBeaver)**
- [ ] Requires SQL queries to explore relationships
- [ ] No native graph visualization
- [ ] Must use ER diagrams (static, structural only)
- [ ] Requires joins to traverse relationships
- [ ] Third-party tools needed for graph view

**Memgraph Lab**
- [ ] Similar to Neo4j Bloom (graph visualization)
- [ ] Query builder interface
- [ ] Interactive exploration
- [ ] Relationship visualization

**Rating Scale**: 1 (Poor) to 5 (Excellent)

| Tool | Rating | Notes |
|------|--------|-------|
| Neo4j Bloom | __ / 5 | |
| Memgraph Lab | __ / 5 | |
| PostgreSQL (pgAdmin) | __ / 5 | |

---

### 2. Entity Editing (Weight: 25%)

**Ease of editing entity properties**

**Neo4j Bloom**
- [ ] Point-and-click property editing
- [ ] Inline editing of properties
- [ ] Visual feedback on changes
- [ ] No Cypher required for simple edits

**Memgraph Lab**
- [ ] Property editing in UI
- [ ] Query-based updates also supported

**PostgreSQL**
- [ ] Form-based editing in pgAdmin
- [ ] SQL knowledge helpful but not required
- [ ] Table view for bulk edits

**Rating Scale**: 1 (Poor) to 5 (Excellent)

| Tool | Rating | Notes |
|------|--------|-------|
| Neo4j Bloom | __ / 5 | |
| Memgraph Lab | __ / 5 | |
| PostgreSQL (pgAdmin) | __ / 5 | |

---

### 3. Relationship Management (Weight: 25%)

**Creating and editing relationships**

**Neo4j Bloom**
- [ ] Drag-and-drop relationship creation
- [ ] Visual relationship editing
- [ ] Relationship deletion with visual confirmation
- [ ] Relationship property editing

**Memgraph Lab**
- [ ] Visual relationship creation
- [ ] Query-based relationship management

**PostgreSQL**
- [ ] Requires SQL INSERT into junction tables
- [ ] No visual relationship creation
- [ ] Must understand foreign key constraints
- [ ] Relationship deletion requires CASCADE awareness

**Rating Scale**: 1 (Poor) to 5 (Excellent)

| Tool | Rating | Notes |
|------|--------|-------|
| Neo4j Bloom | __ / 5 | |
| Memgraph Lab | __ / 5 | |
| PostgreSQL (pgAdmin) | __ / 5 | |

---

### 4. Discovery and Exploration (Weight: 15%)

**Finding entities and exploring connections**

**Neo4j Bloom**
- [ ] Natural language-like search
- [ ] Visual pattern matching
- [ ] "Expand" to find connected entities
- [ ] Saved search perspectives

**Memgraph Lab**
- [ ] Graph-based exploration
- [ ] Query-based discovery

**PostgreSQL**
- [ ] SQL WHERE clauses for search
- [ ] JOIN queries for connections
- [ ] Requires knowledge of schema structure

**Rating Scale**: 1 (Poor) to 5 (Excellent)

| Tool | Rating | Notes |
|------|--------|-------|
| Neo4j Bloom | __ / 5 | |
| Memgraph Lab | __ / 5 | |
| PostgreSQL (pgAdmin) | __ / 5 | |

---

### 5. Batch Operations (Weight: 5%)

**Performing bulk updates**

**Neo4j**
- [ ] Cypher for batch updates
- [ ] APOC procedures for advanced operations
- [ ] CSV import tools

**Memgraph**
- [ ] Cypher for batch updates
- [ ] CSV import

**PostgreSQL**
- [ ] SQL UPDATE with WHERE clauses
- [ ] COPY command for imports
- [ ] Transaction management

**Rating Scale**: 1 (Poor) to 5 (Excellent)

| Tool | Rating | Notes |
|------|--------|-------|
| Neo4j | __ / 5 | |
| Memgraph | __ / 5 | |
| PostgreSQL | __ / 5 | |

---

## Assessment Process

### Step 1: Setup (10 minutes)

1. **Neo4j**: Access Bloom at `http://localhost:7474/browser/` → Open Bloom
2. **Memgraph**: Access Lab at `http://localhost:3000/`
3. **PostgreSQL**: Open pgAdmin or DBeaver, connect to database

### Step 2: Property Update Task (10 minutes)

**Task**: Find aircraft with Mode-S "A12345" and update its operator

**Neo4j Bloom**:
1. Search for "A12345" in search bar
2. Click node when it appears
3. Click "Edit" in property panel
4. Change operator value
5. Save

**Memgraph Lab**:
1. Run query or use visual query builder
2. Edit properties in result panel
3. Or write Cypher UPDATE

**PostgreSQL**:
1. Find table in schema browser
2. Open query tool or use view data
3. Filter for Mode-S = 'A12345'
4. Edit operator value in grid
5. Commit changes

**Time taken**:
- Neo4j Bloom: _____ seconds
- Memgraph Lab: _____ seconds
- PostgreSQL: _____ seconds

**Curator notes**: ___________________________________

---

### Step 3: Relationship Exploration Task (15 minutes)

**Task**: Starting from aircraft "A12345", find all aircraft operated by the same organization

**Neo4j Bloom**:
1. Search for A12345
2. Click "Expand" → Select "OPERATED_BY" relationship
3. From organization node, expand "OPERATED_BY" (reverse direction)
4. See all connected aircraft

**Memgraph Lab**:
1. Similar visual exploration
2. Or write Cypher traversal query

**PostgreSQL**:
1. Write SQL query:
   ```sql
   SELECT a2.*
   FROM air_instance_lookup a1
   JOIN air_instance_lookup a2 ON a1.operator = a2.operator
   WHERE a1.mode_s = 'A12345' AND a2.mode_s != 'A12345';
   ```
2. Execute and review results

**Number of steps required**:
- Neo4j Bloom: _____ steps
- Memgraph Lab: _____ steps
- PostgreSQL: _____ steps

**Curator notes**: ___________________________________

---

### Step 4: Relationship Creation Task (10 minutes)

**Task**: Create a "SEEN_WITH" relationship between two aircraft

**Neo4j Bloom**:
1. Search and select first aircraft
2. Search and add second aircraft to scene
3. Right-click → "Create Relationship"
4. Select relationship type "SEEN_WITH"
5. Add properties (timestamp, confidence)
6. Save

**Memgraph Lab**:
1. Visual relationship creation or Cypher

**PostgreSQL**:
1. Identify IDs of both aircraft
2. Write INSERT statement:
   ```sql
   INSERT INTO kb_relationships (source_domain, source_id, target_domain, target_id, relationship_type, properties)
   VALUES ('AIR', 123, 'AIR', 456, 'SEEN_WITH', '{"timestamp": "2025-01-06T12:00:00Z"}');
   ```
3. Execute

**Complexity rating** (1=simple, 5=complex):
- Neo4j Bloom: ___ / 5
- Memgraph Lab: ___ / 5
- PostgreSQL: ___ / 5

**Curator notes**: ___________________________________

---

### Step 5: Pattern Discovery Task (15 minutes)

**Task**: Find all aircraft that have refueled from the same tanker

**Neo4j Bloom**:
1. Search for tanker aircraft (by air_role or pattern)
2. Expand "REFUELED_BY" relationships (reverse)
3. Visual display of all connected aircraft
4. Can save this pattern as a "Perspective"

**Memgraph Lab**:
1. Similar visual or Cypher-based discovery

**PostgreSQL**:
1. Write complex query with self-join:
   ```sql
   SELECT DISTINCT a1.shark_name, a2.shark_name, r.properties
   FROM kb_relationships r
   JOIN air_instance_lookup a1 ON r.source_id = a1.id
   JOIN air_instance_lookup a2 ON r.target_id = a2.id
   WHERE r.relationship_type = 'REFUELED_BY'
     AND a2.air_role = 'Tanker';
   ```
2. Execute and interpret results

**Ease of discovery** (1=difficult, 5=easy):
- Neo4j Bloom: ___ / 5
- Memgraph Lab: ___ / 5
- PostgreSQL: ___ / 5

**Curator notes**: ___________________________________

---

## Scoring Summary

### Calculate Weighted Scores

| Criterion | Weight | Neo4j Score | Memgraph Score | PostgreSQL Score |
|-----------|--------|-------------|----------------|------------------|
| Relationship Visualization | 30% | __ x 0.30 = __ | __ x 0.30 = __ | __ x 0.30 = __ |
| Entity Editing | 25% | __ x 0.25 = __ | __ x 0.25 = __ | __ x 0.25 = __ |
| Relationship Management | 25% | __ x 0.25 = __ | __ x 0.25 = __ | __ x 0.25 = __ |
| Discovery & Exploration | 15% | __ x 0.15 = __ | __ x 0.15 = __ | __ x 0.15 = __ |
| Batch Operations | 5% | __ x 0.05 = __ | __ x 0.05 = __ | __ x 0.05 = __ |
| **TOTAL** | 100% | **____** | **____** | **____** |

---

## Curator Feedback

### Strengths

**Neo4j Bloom**:
- ___________________________________
- ___________________________________
- ___________________________________

**Memgraph Lab**:
- ___________________________________
- ___________________________________
- ___________________________________

**PostgreSQL**:
- ___________________________________
- ___________________________________
- ___________________________________

### Weaknesses

**Neo4j Bloom**:
- ___________________________________
- ___________________________________
- ___________________________________

**Memgraph Lab**:
- ___________________________________
- ___________________________________
- ___________________________________

**PostgreSQL**:
- ___________________________________
- ___________________________________
- ___________________________________

---

## Overall Recommendation

Based on visualization and curation workflow assessment:

**Preferred tool**: ___________________________________

**Reasoning**: ___________________________________

**Acceptable alternatives**: ___________________________________

**Unacceptable for curation**: ___________________________________

---

## Additional Notes

**Training requirements**:
- Neo4j Bloom: ___________________________________
- Memgraph Lab: ___________________________________
- PostgreSQL: ___________________________________

**Curator learning curve**:
- Neo4j Bloom: _____ hours to proficiency
- Memgraph Lab: _____ hours to proficiency
- PostgreSQL: _____ hours to proficiency

**Daily workflow impact**:
- ___________________________________
- ___________________________________

---

## Sign-off

**Curator Name**: ___________________________________
**Date**: ___________________________________
**Role**: ___________________________________

**This assessment represents**: [ ] Individual feedback [ ] Team consensus

---

## Expected Outcomes

Based on industry experience and the plan's curation requirements:

### Likely Results

**Neo4j Bloom**: 4.0-4.5 / 5.0
- Excellent for relationship visualization
- Intuitive for non-technical curators
- "Bloom-quality" is the standard in the plan

**Memgraph Lab**: 3.5-4.0 / 5.0
- Good graph visualization
- May require more Cypher knowledge
- Lighter weight than Bloom

**PostgreSQL**: 2.0-2.5 / 5.0
- Adequate for simple property edits
- Poor for relationship management
- Requires SQL knowledge
- Not designed for graph curation

### Critical Differentiator

The plan specifically mentions "**Curator preference: Neo4j tooling (Bloom) strongly preferred**" - this CT7 assessment validates or challenges that assumption.

If Bloom scores significantly higher (>1.5 points), it becomes a major factor in the final decision, potentially outweighing performance considerations.
