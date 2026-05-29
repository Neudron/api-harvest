"""Configuration collection module for AI API Key Harvester."""


def collect_config() -> dict:
    """Collect user email, name, Google credentials, and optional vision key.

    Returns:
        dict with keys: email, name, and optionally google_email,
        google_password, vision_api_key
    """
    print("=== AI API Key Harvester ===\n")

    # Collect email (required)
    while True:
        email = input("Your email (for pre-filling forms): ").strip()
        if email:
            break
        print("Email cannot be empty. Please try again.")

    name = input("Your name (for form fields): ").strip()

    config: dict = {"email": email, "name": name}

    print()

    # Google OAuth — optional but recommended for faster signups
    use_google = input("Use Google account to auto-login where possible? (y/n): ").strip().lower()
    if use_google == "y":
        google_email = input(f"Google account email [{email}]: ").strip() or email
        google_password = input("Google account password (memory only, never saved to disk): ").strip()
        if google_password:
            config["google_email"] = google_email
            config["google_password"] = google_password

    print()

    # Existing vision key — optional, enables 'v' command from the start
    existing_key = input("Existing Gemini API key for vision assistance? (ENTER to skip): ").strip()
    if existing_key:
        config["vision_api_key"] = existing_key

    print()
    return config
