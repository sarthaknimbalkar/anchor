from anchor import config, cache


def load_block_index(files: list[tuple[str, str]], project_trusted: bool) -> dict:
    user_rules, project_rules = [], []
    for path, scope in files:
        rules = config.parse_file(path, scope)
        (project_rules if scope == "project" else user_rules).extend(rules)
    merged = config.merge_cascade(user_rules, project_rules, project_trusted)
    blocks = [r for r in merged if r.tier == "block"]
    return cache.index_by_tool(blocks)


def load_all_rules(files: list[tuple[str, str]], project_trusted: bool):
    user_rules, project_rules = [], []
    for path, scope in files:
        rules = config.parse_file(path, scope)
        (project_rules if scope == "project" else user_rules).extend(rules)
    return config.merge_cascade(user_rules, project_rules, project_trusted)
