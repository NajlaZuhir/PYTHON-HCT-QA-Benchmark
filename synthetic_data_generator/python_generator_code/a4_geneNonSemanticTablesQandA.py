#!/usr/bin/env python3
import os
import re
import csv
import json
import itertools
import random
import pandas as pd

from config import (
    PARAMETERS_FOLDER,
    SEMANTIC_TABLES_FOLDER,
    SEMANTIC_QANDA_FOLDER,
    NON_SEMANTIC_TABLES_FOLDER,
    NON_SEMANTIC_QANDA_FOLDER,
)

# -----------------------------------------------------------------------------
# 1) NON-SEMANTIC CODE GENERATOR
# -----------------------------------------------------------------------------
def gene_nonsemantic_codes(num_codes):
    """Return a random permutation of all 2-letter (then 3,4…) consonant strings."""
    consonants = list("bcdfghjklmnpqrstvwxyz")
    # start with all 2-combos, then 3-combos if needed, etc.
    for k in itertools.count(2):
        all_codes = [''.join(c) for c in itertools.combinations(consonants, k)]
        if len(all_codes) >= num_codes:
            random.shuffle(all_codes)
            return all_codes[:num_codes]

# -----------------------------------------------------------------------------
# 2) BUILD SEM→NON-SEM DICTIONARY FROM DB CSV
# -----------------------------------------------------------------------------
def get_code_names_dict_from_dbtable(df):
    """
    Given a DataFrame for the DB table,
    build a mapping of every semantic item (column header, HCT header, and each cell value)
    to a fresh consonant code.
    """
    # drop the final Value column
    feature_cols = df.columns[:-1]
    # there are (nrows + 1) distinct names per column: 
    #   HCT label (human name), DB column name, plus each unique value in that column
    total_codes = (df.shape[0] + 1) * len(feature_cols)
    codes = gene_nonsemantic_codes(total_codes)
    code_iter = iter(codes)

    sem_list = []
    nonsem_list = []

    # for each feature column
    for i, col in enumerate(feature_cols):
        # HUMAN-READABLE HCT header is stored in the first row of that column
        hct_label = df.iloc[0, i].replace('_', ' ')
        # DB-column name is the column name itself
        db_name = col

        # all the subsequent rows in that column are the distinct values
        values = df.iloc[1:, i].unique().tolist()

        # assign codes
        hct_code = next(code_iter)
        db_code  = next(code_iter)
        sem_list.extend([hct_label, db_name])
        nonsem_list.extend([hct_code, db_code])

        for val in values:
            sem_list.append(val)
            nonsem_list.append(next(code_iter))

    # build lookup as list of (sem,nonsem)
    return list(zip(sem_list, nonsem_list))

# -----------------------------------------------------------------------------
# 3) GENERIC STRING REPLACER
# -----------------------------------------------------------------------------
def replace_semantics_in_text(text, mapping):
    """
    For every (sem,nonsem) pair in mapping, do a word-boundary replace
    in the given text blob.
    """
    out = text
    for sem, nonsem in mapping:
        # escape regex, clamp to word boundaries
        out = re.sub(rf'\b{re.escape(str(sem))}\b', str(nonsem), out)
    # normalize CRLF → LF
    return out.replace('\r\n', '\n').replace('\r', '\n')

# -----------------------------------------------------------------------------
# 4) PROCESS ALL FILES
# -----------------------------------------------------------------------------
def main():
    random.seed(0)

    # ensure output dirs exist
    os.makedirs(NON_SEMANTIC_TABLES_FOLDER, exist_ok=True)
    os.makedirs(NON_SEMANTIC_QANDA_FOLDER, exist_ok=True)

    # find all semantic Q&A JSONs
    for fname in sorted(os.listdir(SEMANTIC_QANDA_FOLDER)):
        if not fname.endswith("_QandA.json"):
            continue

        root = fname[:-len("_QandA.json")]

        # 4.1) load the DB CSV to build our mapping
        db_csv = os.path.join(SEMANTIC_TABLES_FOLDER, f"{root}_DB.csv")
        df_db   = pd.read_csv(db_csv, dtype=str)
        mapping = get_code_names_dict_from_dbtable(df_db)

        # helper to write replaced text
        def write_replaced(in_path, out_path, is_json=False):
            with open(in_path, 'r', encoding='utf-8') as f:
                data = f.read()
            replaced = replace_semantics_in_text(data, mapping)
            if is_json:
                # pretty-print JSON
                obj = json.loads(replaced)
                with open(out_path, 'w', encoding='utf-8') as f:
                    json.dump(obj, f, indent=2, ensure_ascii=False)
            else:
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(replaced)

        # 4.2) Q&A JSON
        in_q = os.path.join(SEMANTIC_QANDA_FOLDER,    f"{root}_QandA.json")
        out_q= os.path.join(NON_SEMANTIC_QANDA_FOLDER, f"{root}_QandA_NONSEM.json")
        write_replaced(in_q, out_q, is_json=True)

        # 4.3) DB HTML
        in_db_html = os.path.join(SEMANTIC_TABLES_FOLDER,    f"{root}_DB.html")
        out_db_html= os.path.join(NON_SEMANTIC_TABLES_FOLDER, f"{root}_DB_NONSEM.html")
        write_replaced(in_db_html, out_db_html)

        # 4.4) DB CSV
        in_db_csv = os.path.join(SEMANTIC_TABLES_FOLDER,    f"{root}_DB.csv")
        out_db_csv= os.path.join(NON_SEMANTIC_TABLES_FOLDER, f"{root}_DB_NONSEM.csv")
        write_replaced(in_db_csv, out_db_csv)

        # 4.5) HCT CSV
        in_hct_csv = os.path.join(SEMANTIC_TABLES_FOLDER,    f"{root}_HCT.csv")
        out_hct_csv= os.path.join(NON_SEMANTIC_TABLES_FOLDER, f"{root}_HCT_NONSEM.csv")
        write_replaced(in_hct_csv, out_hct_csv)

        # 4.6) HCT HTML
        in_hct_html = os.path.join(SEMANTIC_TABLES_FOLDER,    f"{root}_HCT.html")
        out_hct_html= os.path.join(NON_SEMANTIC_TABLES_FOLDER, f"{root}_HCT_NONSEM.html")
        write_replaced(in_hct_html, out_hct_html)

        print(f"Processed {root}")

if __name__ == "__main__":
    main()
