"""Configuration collection module for AI API Key Harvester."""


def collect_config() -> dict:
    """Collect user email and name via stdin.

    Returns:
        dict: {"email": str, "name": str}
    """
    print("=== AI API Key Harvester ===\n")

    # Collect email
    while True:
        email = input("Your email (for pre-filling forms): ").strip()
        if email:
            break
        print("Email cannot be empty. Please try again.")

    # Collect name
    name = input("Your name (for form fields): ").strip()

    return {"email": email, "name": name}
