"""CLI entry point for AI API Key Harvester."""

import asyncio

import questionary

from src.browser import BrowserManager
from src.config import collect_config
from src.output import write_output
from src.providers import PROVIDERS_BY_TIER
from src.providers.base import ProviderResult


async def main() -> None:
    """Run the AI API Key Harvester."""
    # Step 1: Collect user config (email, name)
    config = collect_config()

    # Step 2: Tier selection menu
    tier_choice = await questionary.select(
        "Which tier(s) do you want to register?",
        choices=[
            "Email-only (25 providers — no phone, no CC)",
            "+ SMS/Phone (29 providers — includes email + 4 SMS)",
            "+ Credit Card (32 providers — all tiers)",
        ],
    ).ask_async()

    # Step 3: Build provider list based on selection
    if tier_choice.startswith("Email-only"):
        providers = PROVIDERS_BY_TIER["email"]
    elif tier_choice.startswith("+ SMS/Phone"):
        providers = PROVIDERS_BY_TIER["email"] + PROVIDERS_BY_TIER["sms"]
    else:
        providers = (
            PROVIDERS_BY_TIER["email"]
            + PROVIDERS_BY_TIER["sms"]
            + PROVIDERS_BY_TIER["cc"]
        )

    # Step 4: Print startup message
    total = len(providers)
    print(
        f"\nStarting with {total} providers...\nPress ENTER after each key is ready.\n"
    )

    # Step 5: Loop through providers using a single shared browser page
    results: list[ProviderResult] = []

    async with BrowserManager() as page:
        for i, provider in enumerate(providers):
            # Print provider header
            print(
                f"[{i + 1}/{total}] {provider.name} — {provider.credits} | {provider.env_var}"
            )

            # Print gotchas if set
            if provider.gotchas:
                print(f"  ⚠️  {provider.gotchas}")

            # Run the provider signup flow
            key = await provider.run(page, config)

            # Collect result
            result = ProviderResult(provider=provider, key=key)
            results.append(result)

            # Print status
            if key:
                print("  ✓ Saved")
            else:
                print("  ⏭ Skipped")

    # Step 6: Write output file
    filename = write_output(results)

    # Step 7: Print completion message
    print(f"\n✅ Done! Wrote: {filename}")


if __name__ == "__main__":
    asyncio.run(main())
