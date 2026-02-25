# Plan: Integrate 三層十段 Framework into Script Editor

## Context

The current script editor generates simple 3-segment scripts (opening/main/closing). The template at `docs/Podcast節目結構模板.md` defines a professional **三層十段** (3-layer, 10-segment) podcast framework with structure variants, hook techniques, and retention strategies. This plan integrates that framework into the prompt, backend, and frontend so generated scripts are richer and the UI reflects the layered structure.

## Changes Overview

### 1. Prompt: `prompts/system.txt`
- Add knowledge of 三層十段 framework and 起承轉合 narrative structure
- Add awareness of structure variants (訪談型/獨白型/故事敘事型)
- Keep the strict JSON-only response constraint

### 2. Prompt: `prompts/script_generation.txt`
- Add new template variable `{structure_variant}` (computed by backend from style)
- Define 10 segment types with duration proportions
- Include structure variant instructions, hook techniques, retention strategies
- New JSON output schema with `segment_type`, `label`, `content`, `cues`, `estimated_duration`

### 3. Prompt: `prompts/script_refinement.txt`
- Add template variables `{segment_type}`, `{label}`
- Add structure-aware refinement guidance
- Response JSON includes `segment_type`, `label`, `content`, `cues`, `estimated_duration`

### 4. DB Migration: `app/db.py`
- Add `label` and `estimated_duration` columns to `script_segments`
- Update `create_segments()` to store new fields

### 5. Backend API: `app/api/scripts.py`
- Add `STYLE_TO_VARIANT` mapping
- Pass `structure_variant` to prompt
- Pass `segment_type` and `label` to refinement prompt

### 6. Backend API: `app/api/feedback.py`
- Import and use `STYLE_TO_VARIANT` for script regeneration

### 7. Frontend CSS: `frontend/src/assets/styles/variables.css`
- Add `--purple` and `--blue` color pairs

### 8. Frontend Store: `frontend/src/stores/flow.js`
- Expanded segment type mappings (10 types + legacy fallbacks)
- Updated `mapSegment()` with `segmentType`, `layer` fields
- Updated `getDemoSegments()` with 10-segment demo

### 9. Frontend: `frontend/src/components/flow/SegmentCard.vue`
- Expanded `TAG_LABELS` to 10 types
- CSS classes for all tag types using 5-color palette

### 10. Frontend: `frontend/src/components/flow/StepScript.vue`
- `layerGroups` computed property grouping segments by layer
- Nested template with layer headers + grouped SegmentCards
- CSS for `.layer-group`, `.layer-header`, `.layer-segments`

## Backward Compatibility
- New DB columns are nullable: old rows get NULL, frontend defaults handle this
- All frontend mappings include legacy fallbacks for `opening`/`main`/`closing`
- No schema-breaking changes

## Implementation Order
1. Prompts (system.txt, script_generation.txt, script_refinement.txt)
2. DB migration (db.py)
3. Backend API (scripts.py, feedback.py)
4. Frontend CSS (variables.css)
5. Frontend store (flow.js)
6. Frontend components (SegmentCard.vue, StepScript.vue)
