def normalize_text(input_text):
    replacements = {
        "’": "'",  # Curly apostrophe to straight apostrophe
        "‘": "'",  # Left single quotation mark to straight apostrophe
        "“": '"',  # Left double quotation mark to straight quote
        "”": '"',  # Right double quotation mark to straight quote
        "–": "-",  # En-dash to hyphen
        "—": "-",  # Em-dash to hyphen
        # Add more replacements as needed
    }
    for old, new in replacements.items():
        input_text = input_text.replace(old, new)
    return input_text