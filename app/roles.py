"""Load and validate role templates and lexicon references at import time."""

import json
from pathlib import Path

ROLES_PATH = Path(__file__).resolve().parent.parent / "data" / "roles" / "roles.json"


def _nonempty_string(value, context):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"roles.json: {context} harus berupa teks tidak kosong")


def _reference_list(value, valid_ids, context):
    if not isinstance(value, list) or not value:
        raise ValueError(f"roles.json: {context} harus berupa daftar tidak kosong")
    for item in value:
        if not isinstance(item, str) or item not in valid_ids:
            raise ValueError(f"roles.json: {context} merujuk ID tidak dikenal: {item!r}")


def _load_roles():
    try:
        data = json.loads(ROLES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"roles.json tidak dapat dimuat dari {ROLES_PATH}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("roles.json: root harus berupa object")
    roles, groups, skills = (data.get(key) for key in ("roles", "groups", "skills"))
    if not isinstance(roles, dict) or set(roles) != {"backend", "frontend"}:
        raise ValueError("roles.json: roles harus berisi tepat backend dan frontend")
    if not isinstance(groups, dict) or not isinstance(skills, list):
        raise ValueError("roles.json: groups harus object dan skills harus daftar")
    skill_ids = set()
    for index, skill in enumerate(skills):
        if not isinstance(skill, dict):
            raise ValueError(f"roles.json: skills[{index}] harus object")
        skill_id = skill.get("id")
        _nonempty_string(skill_id, f"skills[{index}].id")
        if skill_id in skill_ids:
            raise ValueError(f"roles.json: ID skill duplikat: {skill_id!r}")
        skill_ids.add(skill_id)
        _nonempty_string(skill.get("name"), f"skills[{index}].name")
        aliases = skill.get("aliases")
        if not isinstance(aliases, list) or not aliases:
            raise ValueError(f"roles.json: aliases untuk {skill_id!r} harus daftar tidak kosong")
        for alias in aliases:
            _nonempty_string(alias, f"aliases untuk {skill_id!r}")
        _reference_list(skill.get("roles"), roles, f"skills[{index}].roles")
    for group_id, group in groups.items():
        _nonempty_string(group_id, "groups ID")
        if not isinstance(group, dict):
            raise ValueError(f"roles.json: grup {group_id!r} harus object")
        _nonempty_string(group.get("label"), f"groups.{group_id}.label")
        _reference_list(group.get("any_of"), skill_ids, f"groups.{group_id}.any_of")
    for role_id, role in roles.items():
        if not isinstance(role, dict):
            raise ValueError(f"roles.json: role {role_id!r} harus object")
        _nonempty_string(role.get("label"), f"roles.{role_id}.label")
        templates = role.get("templates")
        if not isinstance(templates, dict):
            raise ValueError(f"roles.json: templates untuk {role_id!r} harus object")
        for language in ("id", "en"):
            _nonempty_string(templates.get(language), f"roles.{role_id}.templates.{language}")
        _reference_list(role.get("core_skills"), skill_ids, f"roles.{role_id}.core_skills")
        _reference_list(role.get("core_groups"), groups, f"roles.{role_id}.core_groups")
    return data


_DATA = _load_roles()


def get_roles():
    """Return role identifiers, labels, and bilingual JD templates."""
    return [
        {"id": role_id, "label": role["label"],
         "template_id": role["templates"]["id"], "template_en": role["templates"]["en"]}
        for role_id, role in _DATA["roles"].items()
    ]


def get_template(role_id, language):
    """Return a validated role template for the requested language."""
    if role_id not in _DATA["roles"] or language not in ("id", "en"):
        raise ValueError(f"Role atau bahasa template tidak dikenal: {role_id!r}/{language!r}")
    return _DATA["roles"][role_id]["templates"][language]


def is_valid_role(role_id):
    """Whether the role is one of the configured role IDs."""
    return role_id in _DATA["roles"]
