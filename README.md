# Jména – Dračí doupě (DBF -> Excel/CSV)

Tento repozitář obsahuje původní ZIP archiv `jmena(1).zip` se sadami jmen pro Dračí doupě (formát FoxPro DBF) a automatizovaný proces převodu do moderních formátů.

## Co se generuje
Po spuštění workflow se vytvoří adresář:
```
output/
  drd_jmena.xlsx        # všechna DBF sjednocena – každá tabulka = samostatný list
  export_csv/           # jednotlivé CSV (UTF-8)
```

## Automatická konverze (Variant B)
GitHub Action automaticky převede data a výsledek **commitne zpět** do stejné větve (branch), pokud dojde ke změně.

### Kdy se workflow spouští
- `push` změny souborů: `jmena(1).zip`, `convert_drd_names.py`, `requirements.txt`
- `pull_request` (může přidat / aktualizovat výstup v PR větvi)
- ruční spuštění přes "Run workflow" (workflow_dispatch)

### Jak ručně spustit
1. Otevři záložku **Actions** v repozitáři.
2. Vyber workflow "Convert DBF to Excel/CSV".
3. Klikni na **Run workflow**.

### Prevence nekonečné smyčky
Workflow necommituje, pokud akci spustil už uživatel `github-actions` (kontrola `github.actor`).

## Lokální spuštění (alternativa)
```bash
git clone https://github.com/Ferenc1234/jmena-draci-doupe.git
cd jmena-draci-doupe
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python convert_drd_names.py jmena(1).zip
```
Soubor najdeš jako `output/drd_jmena.xlsx`.

## Kódování
Primárně se používá `ISO-8859-2` (Latin2). Pokud selže, fallback je `CP852`. Výstupy (Excel, CSV) jsou v Unicode (UTF-8 pro CSV).

## Struktura kódu
- `convert_drd_names.py` – hlavní skript konverze
- `requirements.txt` – závislosti
- `.github/workflows/convert-drd-jmena.yml` – automatizace

## Možné rozšíření (TODO)
- Export do JSON (`output/json/`)
- Webový generátor náhodných jmen
- Normalizace a sjednocení diakritiky
- Sloučení vybraných kategorií do jedné tabulky

## Licence dat
Původní zdroj: [Altar – DrD jména](https://www.altar.cz/drd/jmena.html). Ujisti se, že použití dat odpovídá původním licenčním podmínkám.

---
Automatický převod nastaven – po prvním úspěšném běhu by se měl objevit adresář `output/` s výsledky.