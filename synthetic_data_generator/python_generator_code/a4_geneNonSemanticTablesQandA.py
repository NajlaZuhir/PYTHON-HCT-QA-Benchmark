#!/usr/bin/env python3
import os
import re
import json
import itertools
import random
import pandas as pd

try:
    from config import (
        PARAMETERS_FOLDER,
        SEMANTIC_TABLES_FOLDER,
        SEMANTIC_QANDA_FOLDER,
        NON_SEMANTIC_TABLES_FOLDER,
        NON_SEMANTIC_QANDA_FOLDER,
    )
except ImportError:
    # Fallback defaults if config.py is missing
    PARAMETERS_FOLDER = "./"
    SEMANTIC_TABLES_FOLDER = "./semantic_tables"
    SEMANTIC_QANDA_FOLDER = "./semantic_qanda"
    NON_SEMANTIC_TABLES_FOLDER = "./nonsem_tables"
    NON_SEMANTIC_QANDA_FOLDER = "./nonsem_qanda"


class NonSemanticConverter:
    """
    Scans all *_QandA.json files in SEMANTIC_QANDA_FOLDER, builds
    a semantic→nonsemantic mapping from the corresponding DB CSV,
    and writes out all six NON-SEMANTIC versions of each resource.
    """

    def __init__(self):
        random.seed(0)

        # ensure output dirs exist
        os.makedirs(NON_SEMANTIC_TABLES_FOLDER, exist_ok=True)
        os.makedirs(NON_SEMANTIC_QANDA_FOLDER, exist_ok=True)

    # 1) CODE GENERATOR --------------------------------------------------------
    @staticmethod
    def gene_nonsemantic_codes(num_codes):
        consonants = list("bcdfghjklmnpqrstvwxyz")
        for k in itertools.count(2):
            all_codes = [''.join(c) for c in itertools.combinations(consonants, k)]
            if len(all_codes) >= num_codes:
                random.shuffle(all_codes)
                return all_codes[:num_codes]

    # 2) BUILD SEM→NON-SEM DICTIONARY -----------------------------------------
    def build_mapping_from_db(self, df: pd.DataFrame):
        feature_cols = df.columns[:-1]
        total = (df.shape[0] + 1) * len(feature_cols)
        codes = self.gene_nonsemantic_codes(total)
        it = iter(codes)

        mapping = []
        for col in feature_cols:
            # human header = first row with underscores replaced
            hct_label = df.iloc[0][col].replace('_', ' ')
            db_name   = col
            vals      = df[col].iloc[1:].unique().tolist()

            mapping.append((hct_label, next(it)))
            mapping.append((db_name,   next(it)))
            for v in vals:
                mapping.append((v, next(it)))

        return mapping

    # 3) GENERIC REPLACER ------------------------------------------------------
    @staticmethod
    def replace_in_text(text: str, mapping):
        out = text
        for sem, nonsem in mapping:
            # word-boundary replace
            out = re.sub(rf'\b{re.escape(str(sem))}\b', str(nonsem), out)
        return out.replace('\r\n', '\n').replace('\r', '\n')

    def process_file(self, in_path, out_path, mapping, is_json=False):
        with open(in_path, 'r', encoding='utf-8') as f:
            raw = f.read()
        replaced = self.replace_in_text(raw, mapping)

        if is_json:
            obj = json.loads(replaced)
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(obj, f, indent=2, ensure_ascii=False)
        else:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(replaced)

    # 4) MAIN LOOP ------------------------------------------------------------
    def run(self):
        for fname in sorted(os.listdir(SEMANTIC_QANDA_FOLDER)):
            if not fname.endswith("_QandA.json"):
                continue

            root = fname[:-len("_QandA.json")]

            # load DB CSV as strings
            db_csv_in  = os.path.join(SEMANTIC_TABLES_FOLDER,    f"{root}_DB.csv")
            df_db      = pd.read_csv(db_csv_in, dtype=str)
            mapping    = self.build_mapping_from_db(df_db)

            # define in/out pairs for all six files
            tasks = [
                # (is_json?,   in_folder,               in_suffix,        out_folder,               out_suffix)
                (True,  SEMANTIC_QANDA_FOLDER,    "_QandA.json",       NON_SEMANTIC_QANDA_FOLDER, "_QandA_NONSEM.json"),
                (False, SEMANTIC_TABLES_FOLDER,    "_DB.html",          NON_SEMANTIC_TABLES_FOLDER, "_DB_NONSEM.html"),
                (False, SEMANTIC_TABLES_FOLDER,    "_DB.csv",           NON_SEMANTIC_TABLES_FOLDER, "_DB_NONSEM.csv"),
                (False, SEMANTIC_TABLES_FOLDER,    "_HCT.csv",          NON_SEMANTIC_TABLES_FOLDER, "_HCT_NONSEM.csv"),
                (False, SEMANTIC_TABLES_FOLDER,    "_HCT.html",         NON_SEMANTIC_TABLES_FOLDER, "_HCT_NONSEM.html"),
            ]

            for is_json, in_dir, in_suf, out_dir, out_suf in tasks:
                in_path  = os.path.join(in_dir,  f"{root}{in_suf}")
                out_path = os.path.join(out_dir, f"{root}{out_suf}")
                self.process_file(in_path, out_path, mapping, is_json)

            print(f"✓ Processed {root}")


if __name__ == "__main__":
    NonSemanticConverter().run()
