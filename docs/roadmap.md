# Grant Roadmap

The current demo works with an already prepared household medicine inventory. The grant would unlock the work needed to turn it into a more accessible open-source product for non-technical families and caregivers.

## Milestone 1 — Non-technical setup

Goal: make installation and first launch possible for non-technical users or local community helpers.

Planned work:

- Step-by-step setup wizard.
- Clear hosted vs self-hosted setup paths.
- Example Google Sheet inventory template.
- Better environment configuration documentation.
- Health checks that explain what is misconfigured.
- Simple deployment guide for Vercel or another low-cost host.

## Milestone 2 — Multilingual support

Goal: make the assistant usable by multilingual households.

Planned work:

- Language selection in the bot.
- English and Russian interface support.
- Prepare Hebrew support as a next language.
- Translate safety disclaimers and red-flag messages.
- Make medicine categories and symptom synonyms language-aware.
- Keep medical-safety boundaries consistent across languages.

## Milestone 3 — First-time medicine cabinet creation

Goal: remove the biggest onboarding barrier: manually creating the first inventory.

Planned work:

- Allow users to send a photo of a medicine box/package to the bot.
- Extract medicine name, form, active ingredient, expiry date, and visible instructions where possible.
- Ask follow-up questions when the label is unclear.
- Add a human confirmation step before writing anything into the inventory.
- Create or update the household medicine database automatically after confirmation.
- Mark uncertain fields as `needs review` instead of guessing.

## Milestone 4 — Safety and review layer

Goal: keep the product safe while adding automation.

Planned work:

- Add validation rules for extracted medicine data.
- Add warnings when dosage/age/expiry data is missing or uncertain.
- Improve red-flag detection tests.
- Add demo flows for photo-based inventory creation.
- Document the safety model for contributors and users.

## Why grant funding matters

The MVP proves the core workflow, but it still assumes a prepared inventory and a technical setup path.

Grant support would fund the productization layer: easier setup, multilingual support, safer onboarding, and photo-based first inventory creation. Those are the parts needed for the assistant to become useful beyond one technical household.
