import sys
import zipfile
import shutil
from pathlib import Path
from dbfread import DBF
import pandas as pd

ENCODING_PRIORITY = ["iso-8859-2", "cp852"]  # primary Latin2, fallback DOS


def load_dbf(dbf_path: Path):
    last_err = None
    for enc in ENCODING_PRIORITY:
        try:
            table = DBF(dbf_path, encoding=enc, char_decode_errors='ignore')
            return list(table), enc
        except Exception as e:
            last_err = e
    raise last_err


def main():
    if len(sys.argv) < 2:
        print("Použití: python convert_drd_names.py <soubor_zip> [--keep-temp]")
        sys.exit(1)

    zip_path = Path(sys.argv[1])
    if not zip_path.exists():
        print(f"Soubor {zip_path} neexistuje.")
        sys.exit(1)

    keep_temp = "--keep-temp" in sys.argv

    work_dir = Path("work_extracted")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True)

    # Rozbalení ZIP
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(work_dir)

    dbf_files = list(work_dir.rglob("*.dbf")) + list(work_dir.rglob("*.DBF"))
    if not dbf_files:
        print("Nenalezeny žádné .DBF soubory v archivu.")
        sys.exit(1)

    output_dir = Path("output")
    csv_dir = output_dir / "export_csv"
    output_dir.mkdir(exist_ok=True)
    csv_dir.mkdir(exist_ok=True)

    excel_path = output_dir / "drd_jmena.xlsx"
    writer = pd.ExcelWriter(excel_path, engine="xlsxwriter")

    summary = []

    for dbf_file in sorted(dbf_files):
        sheet_name = dbf_file.stem[:31]
        print(f"Zpracovávám: {dbf_file.name} -> list '{sheet_name}'")
        try:
            rows, used_encoding = load_dbf(dbf_file)
            if rows:
                df = pd.DataFrame(rows)
            else:
                df = pd.DataFrame()

            # Očištění názvů sloupců
            df.columns = [c.strip() if isinstance(c, str) else c for c in df.columns]

            # Uložení do Excelu
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # CSV (UTF-8)
            csv_out = csv_dir / f"{dbf_file.stem}.csv"
            df.to_csv(csv_out, index=False, encoding="utf-8")

            summary.append({
                "file": dbf_file.name,
                "rows": len(df),
                "cols": len(df.columns),
                "encoding": used_encoding
            })
        except Exception as e:
            print(f"Chyba při zpracování {dbf_file}: {e}")
            summary.append({
                "file": dbf_file.name,
                "rows": 0,
                "cols": 0,
                "encoding": "ERROR"
            })

    writer.close()

    print("\nShrnutí tabulek:")
    for item in summary:
        print(f"- {item['file']}: {item['rows']} řádků, {item['cols']} sloupců (encoding: {item['encoding']})")

    print(f"\nHotovo. Excel: {excel_path}")

    if not keep_temp:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()