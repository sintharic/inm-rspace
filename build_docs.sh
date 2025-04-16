#!/bin/bash
sphinx-apidoc -o docs . --separate

DOCS_DIR="docs"

# Process all .rst files except index.rst and modules.rst
for file in "$DOCS_DIR"/*.rst; do
    filename=$(basename "$file")

    if [[ "$filename" == "index.rst" || "$filename" == "modules.rst" ]]; then
        continue
    fi

    name="${filename%.rst}"  # Extract filename without extension

    # Use awk to delete everything before the first occurrence of $name
    # and remove everything after and including "Module content"
    awk -v name="$name" '
        BEGIN { keep = 0 }
        $0 ~ name { keep = 1 }
        keep && !found_end { print }
        /Module content/ { found_end = 1 }
    ' "$file" > "$file.tmp" && mv "$file.tmp" "$file"
done

# Modify modules.rst: delete everything up to ".. toctree::"
awk '
    BEGIN { keep = 0 }
    /.. toctree::/ { keep = 1; print; next }
    keep
' "$DOCS_DIR/modules.rst" > "$DOCS_DIR/modules.rst.tmp" && mv "$DOCS_DIR/modules.rst.tmp" "$DOCS_DIR/modules.rst"

# Modify index.rst: Replace ":maxdepth: 2" with ":maxdepth: 3"
# awk '
#     { gsub(":maxdepth: 2", ":maxdepth: 3") }
#     { print }
# ' "$DOCS_DIR/index.rst" > "$DOCS_DIR/index.rst.tmp" && mv "$DOCS_DIR/index.rst.tmp" "$DOCS_DIR/index.rst"


sphinx-build docs _build