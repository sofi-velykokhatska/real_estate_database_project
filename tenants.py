import csv
from faker import Faker
import random
import re

# German faker
fake = Faker("de_DE")

# Precompiled patterns for stripping unwanted legal-form suffixes from Faker names
LEGAL_TOKEN_PATTERNS = (
    r"ag",
    r"gmbh",
    r"ug",
    r"kg",
    r"ohg",
    r"kgaa",
    r"gbr",
    r"e\.?g\.?",  # covers eG / e.G. / e.g.
    r"e\.?v\.?",  # covers eV / e.V. / e.v.
)
LEGAL_FORM_PATTERN = re.compile(
    r"\s+\b(?:"
    + "|".join(LEGAL_TOKEN_PATTERNS)
    + r")\b(?:\s*&\s*co\.)?(?:\s+\b(?:"
    + "|".join(LEGAL_TOKEN_PATTERNS)
    + r")\b)?\.?.*$",
    flags=re.IGNORECASE,
)

def clean_person_name():
    """
    Generates a German name without titles.
    Ensures format: Firstname Lastname.
    """
    
    return f"{fake.first_name()} {fake.last_name()}"


def german_phone():
    """
    Generates a mobile-style German phone number:
    +49 1XXXXXXXXX
    """
    rest = ''.join(str(random.randint(0, 9)) for _ in range(9))
    return f"+49 1{rest}"


def generate_tenants(output_path="tenants_final_clean.csv"):
    num_tenants = 360
    business_ratio = 0.25

    num_business = int(num_tenants * business_ratio)
    num_private = num_tenants - num_business

    legal_forms = [
        ("GmbH", 70),          # 60–70%
        ("UG", 15),            # 10–15%
        ("GmbH & Co. KG", 15)  # 10–15%
    ]
    rows = []

    def normalize_ascii(text: str) -> str:
        """Transliterate German umlauts/ß to ASCII equivalents."""
        replacements = {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "ß": "ss",
            "Ä": "ae",
            "Ö": "oe",
            "Ü": "ue",
        }
        for src, tgt in replacements.items():
            text = text.replace(src, tgt)
        return text

    def email_local_from_name(name: str) -> str:
        """Lowercase name to an email-friendly local part."""
        ascii_name = normalize_ascii(name.strip().lower())
        return re.sub(r"[^a-z0-9]+", ".", ascii_name).strip(".")

    def strip_existing_form(name: str) -> str:
        """
        Remove any trailing legal form (including combos like 'AG & Co. GmbH')
        so we can reattach one from our allowed set.
        """
        cleaned = LEGAL_FORM_PATTERN.sub("", name).strip()
        return cleaned or name.strip()

    def choose_legal_form() -> str:
        """Select a legal form using the configured weights."""
        labels = [lf[0] for lf in legal_forms]
        weights = [lf[1] for lf in legal_forms]
        return random.choices(labels, weights=weights, k=1)[0]

    def company_domain(company_name: str) -> str:
        """Build a simple domain from the company name without legal form."""
        base = strip_existing_form(company_name)
        cleaned = re.sub(r"[^a-z0-9]+", "", normalize_ascii(base).lower())
        return f"{cleaned or 'firma'}.de"

    # header
    rows.append([
        "tenant_id",
        "customer_type",
        "full_name",
        "company_name",
        "contact_person",
        "email",
        "phone_number"
    ])

    tenant_number = 1

    # --- Generate Private Tenants ---
    for _ in range(num_private):
        tenant_id = f"T{tenant_number:04d}"
        full_name = clean_person_name()
        email_local = email_local_from_name(full_name)
        email = f"{email_local}@example.com"
        phone = german_phone()

        rows.append([
            tenant_id,
            "private",
            full_name,
            "",
            "",
            email,
            phone
        ])

        tenant_number += 1

    # --- Generate Business Tenants ---
    for _ in range(num_business):
        tenant_id = f"T{tenant_number:04d}"

        # Company with legal form
        base_company = fake.company().split(",")[0].strip()
        base_company = strip_existing_form(base_company)
        company_name = f"{base_company} {choose_legal_form()}"

        contact_person = clean_person_name()
        email_local = email_local_from_name(contact_person)
        domain = company_domain(company_name)
        email = f"{email_local}@{domain}"
        phone = german_phone()

        rows.append([
            tenant_id,
            "business",
            "",
            company_name,
            contact_person,
            email,
            phone
        ])

        tenant_number += 1

    # --- Save CSV ---
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"CSV generated successfully: {output_path}")


if __name__ == "__main__":
    generate_tenants()
