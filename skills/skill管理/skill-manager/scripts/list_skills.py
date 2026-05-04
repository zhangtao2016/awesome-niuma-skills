import os
import sys
import yaml
import io

# Force UTF-8 encoding for stdout to handle Chinese characters on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
else:
    # Fallback for older Python versions
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def list_skills(skills_root):
    if not os.path.exists(skills_root):
        print(f"Error: {skills_root} not found")
        return

    # Header with Description, License, Update URL columns
    header = f"{'Skill Name':<20} | {'Type':<12} | {'Description':<40} | {'Ver':<8} | {'License':<12} | {'Update URL'}"
    print(header)
    print("-" * 130)

    for item in os.listdir(skills_root):
        skill_dir = os.path.join(skills_root, item)
        if not os.path.isdir(skill_dir):
            continue

        skill_md = os.path.join(skill_dir, "SKILL.md")
        skill_type = "Standard"
        version = "0.1.0"
        description = "No description"
        license_val = "N/A"
        update_url = "N/A"

        if os.path.exists(skill_md):
            try:
                with open(skill_md, "r", encoding="utf-8") as f:
                    content = f.read()
                parts = content.split("---")
                if len(parts) >= 3:
                    meta = yaml.safe_load(parts[1])
                    if "update_url" in meta:
                        skill_type = "GitHub"
                        update_url = meta.get("update_url", "N/A")
                    version = str(meta.get("version", "0.1.0"))
                    description = meta.get("description", "No description").replace('\n', ' ')
                    license_val = str(meta.get("license", "N/A"))
            except:
                pass

        # Simple truncation for display
        if len(description) > 37:
            display_desc = description[:37] + "..."
        else:
            display_desc = description
        if len(update_url) > 50:
            display_url = update_url[:47] + "..."
        else:
            display_url = update_url

        print(f"{item:<20} | {skill_type:<12} | {display_desc:<40} | {version:<8} | {license_val:<12} | {display_url}")

if __name__ == "__main__":
    skills_path = os.path.expanduser(r"~\.claude\skills")
    if len(sys.argv) > 1:
        skills_path = sys.argv[1]
    list_skills(skills_path)
