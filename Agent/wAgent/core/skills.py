import os
import re
import glob


def load_skills():
    """扫描 .agents/skills/ 目录，加载所有技能的 name 和 description"""
    skills_dir = os.path.join(os.getcwd(), ".agents", "skills")
    if not os.path.isdir(skills_dir):
        return []

    skills = []
    for skill_name in os.listdir(skills_dir):
        skill_md = os.path.join(skills_dir, skill_name, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
            # 解析 YAML Frontmatter
            m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if not m:
                continue
            frontmatter = m.group(1)
            name = re.search(r'name:\s*"?(.*?)"?\s*$', frontmatter, re.MULTILINE)
            desc = re.search(r'description:\s*"?(.*?)"?\s*$', frontmatter, re.MULTILINE)
            if name and desc:
                skills.append({
                    "name": name.group(1),
                    "description": desc.group(1),
                    "path": skill_md,
                })
        except Exception:
            continue
    return skills


def get_skill_content(path):
    """读取技能完整内容"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""
