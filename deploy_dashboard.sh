#!/bin/bash
set -e

# Set up variables
SITE_DIR="_site"
DOCS_DIR="docs"

# Render the Quarto project in parallel
echo "Rendering Quarto project..."
quarto render --parallel

# Create the docs folder if it doesn't exist
mkdir -p "$DOCS_DIR"

# Sync rendered files (only copies changed files, deletes removed files)
echo "Syncing rendered files to 'docs' folder..."
rsync -a --delete "$SITE_DIR/" "$DOCS_DIR/"

# Only commit and push if there are changes
if git diff --quiet "$DOCS_DIR" && git diff --cached --quiet "$DOCS_DIR"; then
    echo "No changes to deploy."
else
    echo "Adding changes to Git..."
    git add "$DOCS_DIR"

    echo "Committing changes..."
    git commit -m "Deploy Quarto dashboard to GitHub Pages"

    echo "Pushing changes to GitHub..."
    git push

    echo "GitHub Pages site is now live at:"
    echo "https://snfagora.github.io/agora_dashboard/"
fi
