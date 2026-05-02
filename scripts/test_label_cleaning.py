def clean_label(label: str):
    original = label

    variant = None

    parts = label.split("_")

    if parts[-1].isdigit():
        variant = int(parts[-1])
        label_without_variant = "_".join(parts[:-1])
    else:
        label_without_variant = label

    alias_parts = label_without_variant.split("_OR_")

    aliases = [
        part.lower().replace("_", " ").replace("-", " ").strip()
        for part in alias_parts
    ]

    display_parts = [
        part.replace("_", " ").replace("-", " ").title()
        for part in alias_parts
    ]

    display_name = " / ".join(display_parts)

    if variant:
        display_name = f"{display_name} {variant}"

    return {
        "gloss": original,
        "displayName": display_name,
        "aliases": aliases,
        "baseWord": aliases[0] if aliases else "",
        "variant": variant,
    }


test_labels = [
    "WITHDRAWAL_OR_QUIT",
    "DANGEROUS_OR_DANGER",
    "WATER_2",
    "CARRY_1",
    "THANK_YOU",
    "TOM-BROWN",
    "NUMBER_1_-_10",
]

for label in test_labels:
    print(clean_label(label))