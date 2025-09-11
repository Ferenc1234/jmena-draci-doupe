# jmena-draci-doupe

Konverze DBF souborů s českými jmény ze hry Dračí doupě do Excel a CSV formátů s automatickou rekonstrukcí diakritiky.

## Vlastnosti

- **Automatická detekce kódování**: Inteligentně rozpozná správné kódování DBF souborů (cp852, cp1250, iso-8859-2)
- **Rekonstrukce diakritiky**: Automaticky obnovuje českou diakritiku v textu, který byl uložen bez diakritických znamének
- **Export do více formátů**: Excel workbook (.xlsx) + jednotlivé CSV soubory
- **Zachování struktury**: Všechny sloupce a záznamy zůstávají zachovány

## Rekonstrukce diakritiky

Nová funkce automaticky obnovuje českou diakritiku pomocí:

- **Primární slovník**: Zjednodušený český morfologický slovník
- **Manuální přepisy**: Vlastní opravy v `diacritics/overrides.tsv`
- **Zachování velikosti**: Respektuje původní velikost písmen (VELKÁ, Velká, malá)

### Příklady rekonstrukce

- `Bazina` → `Bažina`
- `komaru` → `komárů`  
- `krkavcu` → `krkavců`
- `mrtvych` → `mrtvých`

## Použití

```bash
# S rekonstrukcí diakritiky (výchozí)
python convert_drd_names.py "jmena(1).zip"

# Bez rekonstrukce diakritiky
python convert_drd_names.py "jmena(1).zip" --no-diacritics

# Vlastní výstupní složka
python convert_drd_names.py "jmena(1).zip" --output-dir moje_slozka

# Vynucené kódování
python convert_drd_names.py "jmena(1).zip" --encoding cp852
```

## Artefakt ke stažení

Každé spuštění workflow automaticky vytvoří a nahraje artefakt `drd-jmena-export.zip`, který obsahuje všechny vygenerované soubory z adresáře `output/` (Excel soubory + CSV soubory).

**Jak stáhnout:**
1. Jděte na záložku **Actions** v tomto repositáři
2. Vyberte konkrétní běh workflow 
3. V sekci **Artifacts** najdete `drd-jmena-export` ke stažení
4. Stažený ZIP obsahuje Excel soubory (`drd_names.xlsx`) a CSV soubory pro jednotlivé DBF tabulky