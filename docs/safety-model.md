# Safety Model

Open Family Medicine Cabinet is health-adjacent software, so the safety boundary is intentionally narrow.

The assistant helps a household understand its own medicine inventory. It does not diagnose, prescribe treatment, recommend dosages, or replace medical advice.

## Safety principles

1. **Inventory first**
   - The source of truth is the user's own medicine list.
   - The assistant should not invent medicines that are not in the inventory.

2. **No diagnosis**
   - User text or voice input is treated as a household search query, not a clinical case.
   - The assistant may identify symptom categories for matching, but it must not name a disease as a diagnosis.

3. **No prescription or dosage instructions**
   - The assistant should not tell a user what dose to take.
   - It should direct users to official instructions, a doctor, pharmacist, or emergency service when needed.

4. **Expired items are unsafe by default**
   - Expired or inactive medicines are filtered before matching.
   - The assistant should not present expired medicines as usable options.

5. **Adult/child separation**
   - Child-safe flags are explicit inventory metadata.
   - Adult-only medicines should not be presented as child-safe.

6. **Doctor-only escalation**
   - Items marked with `ВРАЧ` / doctor-only in the inventory should be shown with a warning.
   - Antibiotics, prescription medicines, eye drops with steroids/antibiotics, and similar items should be handled conservatively.

7. **Red flags override convenience**
   - If the request indicates a red-flag situation, the assistant should escalate to medical care instead of trying to solve the case at home.

## Red-flag examples

The exact rules can be adapted by language and region, but examples include:

- breathing difficulty;
- chest pain;
- severe allergic reaction;
- loss of consciousness;
- seizure;
- severe dehydration;
- blood in vomit or stool;
- severe abdominal pain;
- high or persistent fever in a child;
- symptoms in an infant;
- suspected poisoning or overdose;
- serious injury, burn, or wound;
- eye injury or sudden vision changes.

## Response style

Preferred wording:

```text
I found these items in your medicine cabinet that match this category.
Please check the official instructions and expiry date before use.
This does not replace medical advice.
```

When a red flag is present:

```text
This may be unsafe to handle at home. Please seek medical care / emergency help.
```

Avoid:

- “You have X disease.”
- “Take this medicine.”
- “This is safe.”
- “You do not need a doctor.”
- exact dosage instructions unless they are explicitly read from official user-provided instructions and clearly attributed.

## Data and privacy boundary

The MVP uses Google Sheets as the inventory backend and Telegram as the interface. Families should treat medicine inventory and health-related chat messages as sensitive data.

The open-source goal is to make the logic auditable and adaptable, while allowing users to keep their own inventory under their control.
