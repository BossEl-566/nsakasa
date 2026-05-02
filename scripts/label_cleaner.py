import re


def format_label_piece(piece: str, title_case: bool = False):
    range_token = "RANGETOKEN"

    text = piece.replace("_-_", f" {range_token} ")
    text = text.replace("_", " ")
    text = text.replace("-", " ")
    text = text.replace(range_token, "-")

    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s*-\s*", " - ", text).strip()

    if title_case:
        return text.title()

    return text.lower()


def unique_list(items):
    seen = set()
    result = []

    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)

    return result


def clean_label(label: str):
    original = label

    variant = None
    label_without_variant = label

    is_number_range = "_-_" in label

    if not is_number_range:
        variant_match = re.match(r"^(.*)_(\d+)$", label)

        if variant_match:
            label_without_variant = variant_match.group(1)
            variant = int(variant_match.group(2))

    alias_parts = label_without_variant.split("_OR_")

    display_parts = [
        format_label_piece(part, title_case=True)
        for part in alias_parts
    ]

    display_name = " / ".join(display_parts)

    if variant is not None:
        display_name = f"{display_name} {variant}"

    aliases = []

    for part in alias_parts:
        alias = format_label_piece(part)
        aliases.append(alias)

        if " - " in alias:
            aliases.append(alias.replace(" - ", " to "))
            aliases.append(alias.replace(" - ", " "))

        if variant is not None:
            aliases.append(f"{alias} {variant}")

    aliases = unique_list(aliases)

    return {
        "gloss": original,
        "displayName": display_name,
        "aliases": aliases,
        "baseWord": aliases[0] if aliases else "",
        "variant": variant,
    }