# UPS Agent Skills (Claude import bundle)

This bundle is structured for Claude Agent Skills import:

- One top-level folder: `UPS_Agent_Skills/`
- Each skill lives in its own subfolder and includes **`SKILL.md`**:
  - `universal_prediction_system/SKILL.md`
  - `prediction_system_blueprint/SKILL.md`
  - `unified_decision_intelligence_ui/SKILL.md`
  - `ups_kb_authoring/SKILL.md`

Shared reference files (optional for humans/automation):
- `ups_output_schema.json`
- `core_contract.txt`

If Claude reports an issue with `SKILL.md`, verify:
1) The file is named exactly `SKILL.md` (case-sensitive)
2) It begins with valid YAML front matter including `name` and `description`
3) The markdown body follows the closing `---`
