#!/bin/bash
# Package all skills into .skill files

set -e

SKILLS_DIR="$(dirname "$0")"
OUTPUT_DIR="${SKILLS_DIR}/dist"

mkdir -p "$OUTPUT_DIR"

echo "Packaging skills from: $SKILLS_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

for skill_dir in "$SKILLS_DIR"/*/; do
    skill_name=$(basename "$skill_dir")
    
    # Skip non-skill directories
    if [[ "$skill_name" == "dist" ]] || [[ "$skill_name" == "scripts" ]]; then
        continue
    fi
    
    # Check for SKILL.md
    if [[ ! -f "${skill_dir}/SKILL.md" ]]; then
        echo "⚠️  Skipping $skill_name (no SKILL.md)"
        continue
    fi
    
    echo "📦 Packaging: $skill_name"
    
    # Create zip archive
    output_file="${OUTPUT_DIR}/${skill_name}.skill"
    
    # Remove existing package
    rm -f "$output_file"
    
    # Create package (excluding dist and package script)
    cd "$SKILLS_DIR"
    zip -r "$output_file" "$skill_name" \
        -x "*/dist/*" \
        -x "*/package-all.sh" \
        -x "*/.git/*" \
        -x "*/__pycache__/*" \
        -x "*.pyc" \
        -q
    
    # Get size
    size=$(du -h "$output_file" | cut -f1)
    echo "   ✓ Created: ${skill_name}.skill (${size})"
done

echo ""
echo "✅ All skills packaged to: $OUTPUT_DIR"
echo ""
ls -lh "$OUTPUT_DIR"
