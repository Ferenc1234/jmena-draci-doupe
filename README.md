# jmena-draci-doupe

## Artefakt ke stažení

Každé spuštění workflow automaticky vytvoří a nahraje artefakt `drd-jmena-export.zip`, který obsahuje všechny vygenerované soubory z adresáře `output/` (Excel soubory + CSV soubory).

**Jak stáhnout:**
1. Jděte na záložku **Actions** v tomto repositáři
2. Vyberte konkrétní běh workflow 
3. V sekci **Artifacts** najdete `drd-jmena-export` ke stažení
4. Stažený ZIP obsahuje Excel soubory (`drd_names.xlsx`) a CSV soubory pro jednotlivé DBF tabulky

## Diacritization / Diakritizace

Tato aplikace podporuje automatickou diakritizaci českých textů pomocí MorfFlex slovníku s pokročilými heuristikami pro lepší výběr kandidátů.

### Funkce

- **Diakritická insenzitivní porovnávání přípon**: Nejprv se odstraní diakritika z původního tokenu i kandidátů před porovnáním koncovek
- **PAD2 preference pro -ů**: V sloupci PAD2 se preferují kandidáti končící na "ů" před těmi končícími na "u" (typické pro genitivy plurálu maskulin: blesků, hromů, duchů, komárů, ...)
- **Zachování původního velkého/malého písma**: Vzor velkých a malých písmen se zachovává z původního textu
- **Fallback na původní token**: Pokud neexistuje žádný slovníkový kandidát, původní token se zachová

### CLI možnosti

```bash
python convert_drd_names.py input.zip [options]

Options:
  --diacritize {on,off}     Zapnout/vypnout diakritizaci PAD sloupců (výchozí: on)
  --prefer-genpl-uu         Preferovat koncovky -ů v PAD2 sloupcích (výchozí: zapnuto)
  --no-prefer-genpl-uu      Vypnout preferenci -ů v PAD2 sloupcích
```

### Příklady transformací

V PAD2 sloupci (genitivy plurálu):
- `blesku` → `blesků`  
- `hromu` → `hromů`
- `duchu` → `duchů`
- `komaru` → `komárů`

V ostatních sloupcích:
- `komar` → `komár` (základní tvar s diakritikou)
- `bazina` → `bažina`

### Workflow integrace

Diakritizace je ve workflow automaticky zapnutá s následujícími výchozími nastaveními:
- `--diacritize on` (diakritizace zapnuta)
- `--prefer-genpl-uu` (preference -ů v PAD2 zapnuta)

Workflow pokračuje i když MorfFlex slovník není dostupný - v takovém případě se zachovají původní tokeny.