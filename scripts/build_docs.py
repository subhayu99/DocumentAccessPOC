#!/usr/bin/env python3
"""
build_docs.py

1. Creates 'docs_staging'.
2. Splits README.md into multiple topic pages using a robust line parser.
3. Pre-processes Markdown (Admonitions, Links).
4. Generates API Reference.
5. Generates a dynamic Navigation structure in mkdocs.yml.
"""

import ast
import os
import re
import shutil
from pathlib import Path
from typing import Dict, List

# Configuration
ROOT_DIR = Path(".")
SOURCE_DOCS = ROOT_DIR / "docs"
STAGING_DIR = ROOT_DIR / "docs_staging"
MKDOCS_YML = ROOT_DIR / "mkdocs.yml"

# Map README Headers to (Filename, Nav Title)
# The script checks if the README header *contains* these keys.
README_SPLIT_MAP = {
    "🚀 Quick Start": ("quick-start.md", "Quick Start"),
    "⚙️ API Usage Examples": ("usage.md", "Usage Examples"),
    "🔐 Security Model": ("security.md", "Security Model"),
    "🗺️ Extensibility and Roadmap": ("roadmap.md", "Roadmap"),
    "❓ FAQ": ("faq.md", "FAQ"),
    "✨ Key Features": ("features.md", "Key Features"),
}

# -----------------------------------------------------------------------------
# 1. Robust README Splitter (Line-by-Line)
# -----------------------------------------------------------------------------

class ReadmeSplitter:
    def __init__(self, staging_dir: Path):
        self.index_path = staging_dir / "index.md"
        self.staging_dir = staging_dir

    def split(self):
        """Parse index.md line-by-line, extract sections, write new files."""
        if not self.index_path.exists():
            return

        with open(self.index_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_index_lines = []
        current_buffer = []
        current_header = "Intro" # The text before the first ## header
        
        # We will store extracted sections here to write them later
        extracted_sections = {} 

        def process_buffer(header, buffer):
            """Decide where to send the accumulated buffer."""
            content = "".join(buffer)
            
            # Check if this header matches one of our targets
            target_config = None
            for key, val in README_SPLIT_MAP.items():
                if key in header:
                    target_config = val
                    break
            
            if target_config:
                # It's a target! Save to extraction list.
                filename, nav_title = target_config
                extracted_sections[filename] = (nav_title, content)
                print(f"✓ Extracted '{nav_title}' to {filename}")
            else:
                # Not a target, keep in Index.
                # If it's not the Intro, we need to add the header back.
                if header != "Intro":
                    new_index_lines.append(f"## {header}\n")
                new_index_lines.extend(buffer)

        # Iterate through lines
        for line in lines:
            # Check for H2 header (## Title)
            if line.strip().startswith("## "):
                # Process the PREVIOUS section
                process_buffer(current_header, current_buffer)
                
                # Start NEW section
                current_header = line.strip()[3:].strip() # Remove '## ' and whitespace
                current_buffer = []
            else:
                current_buffer.append(line)

        # Process the final section
        process_buffer(current_header, current_buffer)

        # 1. Write the new Index file
        with open(self.index_path, 'w', encoding='utf-8') as f:
            f.writelines(new_index_lines)

        # 2. Write the Extracted files
        for filename, (title, content) in extracted_sections.items():
            file_path = self.staging_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                # Add H1 title to the top of the extracted page
                f.write(f"# {title}\n\n{content}")

# -----------------------------------------------------------------------------
# 2. Content Preprocessor
# -----------------------------------------------------------------------------

class ContentPreprocessor:
    def __init__(self, staging_dir: Path):
        self.staging_dir = staging_dir

    def clean_markdown(self, content: str, is_index: bool = False) -> str:
        # 1. Remove Manual TOC (Matches "## ... Table of Contents" -> End of list)
        content = re.sub(r'##\s+.*Table of Contents.*?(?=^##|\Z)', '', content, flags=re.DOTALL | re.MULTILINE)
        
        # 2. Fix Relative Links in Index
        if is_index:
            content = content.replace("](docs/", "](")
        
        # 3. Convert Admonitions (**Note:** -> !!! note)
        def admonition_replacer(match):
            type_map = {'Note': 'note', 'Warning': 'warning', 'Tip': 'tip'}
            key = match.group(1)
            text = match.group(2)
            return f'!!! {type_map.get(key, "note")}\n    {text}'
        
        content = re.sub(r'^(?:> )?\*\*(Note|Warning|Tip):\*\*\s*(.*)', admonition_replacer, content, flags=re.MULTILINE)

        # 4. Remove Hardcoded Mermaid Theme
        content = re.sub(r'^\s*theme:\s*dark\s*$', '', content, flags=re.MULTILINE)

        # 5. Convert HTML Details to Collapsible
        pattern = r'<details>\s*<summary>(?:<strong>)?(.*?)(?:</strong>)?</summary>(.*?)</details>'
        def details_replacer(match):
            title = match.group(1)
            body = match.group(2).strip()
            indented_body = '\n    '.join(line for line in body.splitlines())
            return f'??? info "{title}"\n    {indented_body}'
        
        content = re.sub(pattern, details_replacer, content, flags=re.DOTALL)
        
        # 6. Replace self references to page links ([foo](#foo) -> [foo](foo))
        content = re.sub(r'\[(\w+)\]\(#(\w+)\)', r'[\1](\2)', content)

        return content

    def process_files(self):
        for root, _, files in os.walk(self.staging_dir):
            for file in files:
                if file.endswith(".md"):
                    path = Path(root) / file
                    with open(path, 'r', encoding='utf-8') as f:
                        raw = f.read()
                    cleaned = self.clean_markdown(raw, file == "index.md")
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(cleaned)

# -----------------------------------------------------------------------------
# 3. API Generator
# -----------------------------------------------------------------------------

class APIDocGenerator:
    def __init__(self, root_dir: Path, output_dir: Path):
        self.root_dir = root_dir
        self.docs_dir = output_dir / "api"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.target_dirs = ['backends', 'helpers', 'logic', 'models']
        self.target_files = ['main.py', 'config.py']

    def get_public_members(self, file_path: Path) -> bool:
        if not file_path.exists(): return False
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    if not node.name.startswith('_'): return True
        except: pass
        return False

    def generate(self) -> Dict[str, str]:
        generated_files = {}
        # Root
        root_modules = [f.replace('.py', '') for f in self.target_files if self.get_public_members(self.root_dir / f)]
        if root_modules:
            self._write_category("root", root_modules, "Application Entry")
            generated_files["root"] = "api/root.md"
        # Dirs
        for target in self.target_dirs:
            modules = []
            for root, _, files in os.walk(self.root_dir / target):
                for file in files:
                    if file.endswith('.py') and file != '__init__.py':
                        full_path = Path(root) / file
                        if self.get_public_members(full_path):
                            rel_path = full_path.relative_to(self.root_dir)
                            modules.append(str(rel_path).replace(os.sep, '.').replace('.py', ''))
            if modules:
                self._write_category(target, modules, target.title())
                generated_files[target] = f"api/{target}.md"
        return generated_files

    def _write_category(self, filename, modules, title):
        content = [f"# {title}\n"]
        for module in sorted(modules):
            content.append(f"## {module}")
            content.append(f"::: {module}")
            content.append("    options:")
            content.append("      show_root_heading: true")
            content.append("      show_source: true")
            content.append("      heading_level: 3")
            content.append("---\n")
        with open(self.docs_dir / f"{filename}.md", 'w', encoding='utf-8') as f:
            f.write("\n".join(content))

# -----------------------------------------------------------------------------
# 4. Navigation Builder
# -----------------------------------------------------------------------------

def build_navigation(api_map: Dict[str, str]) -> List[Dict]:
    nav = []

    # Project Guide (Only if files exist)
    guide_items = [{"Intro": "index.md"}]
    for _, (filename, title) in README_SPLIT_MAP.items():
        if (STAGING_DIR / filename).exists():
            guide_items.append({title: filename})
    if guide_items:
        nav.append({"Home": guide_items})

    # Architecture
    arch_items = []
    if (STAGING_DIR / "solution.md").exists(): arch_items.append({"Solution Overview": "solution.md"})
    if (STAGING_DIR / "flow.md").exists(): arch_items.append({"API Flow": "flow.md"})
    if (STAGING_DIR / "extensibility.md").exists(): arch_items.append({"Extensibility": "extensibility.md"})
    if arch_items:
        nav.append({"Architecture": arch_items})

    # API Reference
    api_items = []
    order = ['models', 'logic', 'helpers', 'backends', 'root']
    for cat in order:
        if cat in api_map:
            api_items.append({cat.title(): api_map[cat]})
    if api_items:
        nav.append({"API Reference": api_items})

    return nav

def update_mkdocs_config(nav_structure: List[Dict]):
    with open(MKDOCS_YML, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    skip = False
    
    for line in lines:
        if line.strip().startswith("docs_dir:"): continue
        if line.strip().startswith("nav:"):
            skip = True
            continue
        if skip and line.strip() and not line.startswith(" "):
            skip = False
        if not skip:
            new_lines.append(line)

    new_lines.append(f"docs_dir: {STAGING_DIR.name}\n")
    new_lines.append("nav:\n")
    
    def write_nav_item(item, indent=2):
        for key, value in item.items():
            if isinstance(value, str):
                new_lines.append(f"{' ' * indent}- {key}: {value}\n")
            elif isinstance(value, list):
                new_lines.append(f"{' ' * indent}- {key}:\n")
                for subitem in value:
                    write_nav_item(subitem, indent + 4)

    for item in nav_structure:
        write_nav_item(item)

    with open(MKDOCS_YML, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("✓ Updated mkdocs.yml navigation")

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    if STAGING_DIR.exists(): shutil.rmtree(STAGING_DIR)
    shutil.copytree(SOURCE_DOCS, STAGING_DIR)
    shutil.copy(ROOT_DIR / "README.md", STAGING_DIR / "index.md")
    print(f"✓ Created staging directory")

    splitter = ReadmeSplitter(STAGING_DIR)
    splitter.split()

    preprocessor = ContentPreprocessor(STAGING_DIR)
    preprocessor.process_files()

    generator = APIDocGenerator(ROOT_DIR, STAGING_DIR)
    api_map = generator.generate()

    nav = build_navigation(api_map)
    update_mkdocs_config(nav)

    print("\nBuild complete. Run 'mkdocs serve'.")

if __name__ == "__main__":
    main()