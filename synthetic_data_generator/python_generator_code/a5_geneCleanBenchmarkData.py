#!/usr/bin/env python3
import os
import glob
import shutil

try:
    from config import (
        SEMANTIC_QANDA_FOLDER,
        SEMANTIC_TABLES_FOLDER,
        NON_SEMANTIC_QANDA_FOLDER,
        NON_SEMANTIC_TABLES_FOLDER,
        BENCHMARK_FOLDER,
    )
except ImportError:
    # fallback defaults
    SEMANTIC_QANDA_FOLDER        = "./semantic_qanda"
    SEMANTIC_TABLES_FOLDER       = "./semantic_tables"
    NON_SEMANTIC_QANDA_FOLDER    = "./nonsem_qanda"
    NON_SEMANTIC_TABLES_FOLDER   = "./nonsem_tables"
    BENCHMARK_FOLDER             = "./benchmark"

class BenchmarkCleaner:
    """
    Scans all semantic Q&A JSONs, checks whether all required
    semantic/nonsemantic table & Q&A files exist, and if so
    copies them into the BENCHMARK_FOLDER.
    """

    def __init__(self):
        os.makedirs(BENCHMARK_FOLDER, exist_ok=True)
        self.suffix = "_QandA.json"

    def list_roots(self):
        """
        Returns the list of root names for which
        SEMANTIC_QANDA_FOLDER/<root>_QandA.json exists.
        """
        pattern = os.path.join(SEMANTIC_QANDA_FOLDER, f"*{self.suffix}")
        files = glob.glob(pattern)
        return [os.path.basename(fp)[:-len(self.suffix)] for fp in files]

    def all_exist(self, root: str) -> bool:
        """
        Checks that for a given root, all 9 required files are present.
        """
        to_check = [
            os.path.join(NON_SEMANTIC_QANDA_FOLDER,  f"{root}_QandA_NONSEM.json"),
            os.path.join(SEMANTIC_TABLES_FOLDER,     f"{root}_HCT.html"),
            os.path.join(SEMANTIC_TABLES_FOLDER,     f"{root}_HCT.csv"),
            os.path.join(SEMANTIC_TABLES_FOLDER,     f"{root}_DB.html"),
            os.path.join(SEMANTIC_TABLES_FOLDER,     f"{root}_DB.csv"),
            os.path.join(NON_SEMANTIC_TABLES_FOLDER, f"{root}_HCT_NONSEM.html"),
            os.path.join(NON_SEMANTIC_TABLES_FOLDER, f"{root}_HCT_NONSEM.csv"),
            os.path.join(NON_SEMANTIC_TABLES_FOLDER, f"{root}_DB_NONSEM.html"),
            os.path.join(NON_SEMANTIC_TABLES_FOLDER, f"{root}_DB_NONSEM.csv"),
        ]
        return all(os.path.exists(p) for p in to_check)

    def copy_group(self, root: str):
        """
        Copies all 10 files for `root` into BENCHMARK_FOLDER.
        """
        tasks = [
            # semantic Q&A
            (SEMANTIC_QANDA_FOLDER,      f"{root}_QandA.json"),
            # non-semantic Q&A
            (NON_SEMANTIC_QANDA_FOLDER,  f"{root}_QandA_NONSEM.json"),
            # semantic tables
            (SEMANTIC_TABLES_FOLDER,     f"{root}_HCT.html"),
            (SEMANTIC_TABLES_FOLDER,     f"{root}_HCT.csv"),
            (SEMANTIC_TABLES_FOLDER,     f"{root}_DB.html"),
            (SEMANTIC_TABLES_FOLDER,     f"{root}_DB.csv"),
            # non-semantic tables
            (NON_SEMANTIC_TABLES_FOLDER, f"{root}_HCT_NONSEM.html"),
            (NON_SEMANTIC_TABLES_FOLDER, f"{root}_HCT_NONSEM.csv"),
            (NON_SEMANTIC_TABLES_FOLDER, f"{root}_DB_NONSEM.html"),
            (NON_SEMANTIC_TABLES_FOLDER, f"{root}_DB_NONSEM.csv"),
        ]
        for src_dir, fname in tasks:
            src = os.path.join(src_dir, fname)
            shutil.copy(src, BENCHMARK_FOLDER)

    def run(self):
        roots = self.list_roots()
        kept = []
        for root in roots:
            print(f"Checking {root}…", end=" ")
            if self.all_exist(root):
                print("OK")
                kept.append(root)
            else:
                print("MISSING FILES → skipping")
        print(f"\nCopying {len(kept)} complete groups into `{BENCHMARK_FOLDER}`:")
        for i, root in enumerate(kept, 1):
            print(f"  {i}/{len(kept)} → {root}")
            self.copy_group(root)
        print("Done.")


if __name__ == "__main__":
    BenchmarkCleaner().run()
