import sys
from generate_html import generate_html

def main():
    print("Starte die Generierung der Fantasy Football HTML-Seite...")
    try:
        # Ruft die Funktion aus der generate_site.py auf
        generate_html()
        print("Vorgang erfolgreich beendet.")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()