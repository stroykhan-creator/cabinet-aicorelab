# /tmp/reanimator_one_shot.py
# Однократный прогон реаниматора для одной компании.
# Измените COMPANY_ID при необходимости.

COMPANY_ID = 6  # <- замените на нужный id компании

from cabinet.management.commands.run_bot import Command
from cabinet.models import Company

def main():
    print("--- Starting main() function ---") # <--- ДОБАВЛЕНО ЭТО
    cmd = Command()

    try:
        c = Company.objects.get(id=COMPANY_ID)
    except Company.DoesNotExist:
        print(f"Company with id={COMPANY_ID} not found")
        return

    print("Processing company:", c.id, c.name)
    print("Flags: is_active:", c.is_active, "is_reanimator_enabled:", c.is_reanimator_enabled)
    print("Has keys: green_api_id:", bool(c.green_api_id), "green_api_token:", bool(c.green_api_token), "openai_key:", bool(c.openai_key))
    print("Counts: patients:", c.patients.count(), "outreaches:", c.outreaches.count())

    if not (c.is_active and c.is_reanimator_enabled and c.green_api_id and c.green_api_token and c.openai_key):
        print("Skipping: missing flags or API keys. No actions performed.")
        return

    try:
        print("--- run_initial_outreach ---")
        cmd.run_initial_outreach(c)
        print("--- check_scheduler ---")
        cmd.check_scheduler(c)
        print("--- process_incoming ---")
        cmd.process_incoming(c)
        print("One-shot reanimator finished successfully for company id=", c.id)
    except Exception as e:
        print("Error during one-shot run for company id=", c.id, ":", repr(e))

# Убрали if __name__ == "__main__":
main() # <--- Теперь вызываем main() напрямую

