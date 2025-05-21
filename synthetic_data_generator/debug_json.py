#!/usr/bin/env python3
import os
import json
import pandas as pd

def load_and_flatten(path, prefix):
    """
    Load a JSON array of table dicts from `path`,
    normalize only the top-level fields into a DataFrame,
    and prefix column names so we can compare R_foo vs. Py_foo.
    """
    with open(path, 'r', encoding='utf-8') as f:
        tables = json.load(f)

    df = pd.json_normalize(tables)[[
        'name', 'replica', 'shuffle', 'agg_fun1',
        'agg_name1', 'values', 'valueName', 'row_format'
    ]]

    # Prefix every column except 'name'
    df = df.rename(columns={
        c: f'{prefix}_{c}' for c in df.columns if c != 'name'
    })
    return df

def compare_tables(r_df, py_df, report_path):
    # merge as before…
    merged = r_df.merge(py_df, on='name', how='outer', indicator=True)
    
    lines = []

    # 1. Tables only in one side
    only_r  = merged[merged['_merge']=='left_only']['name']
    only_py = merged[merged['_merge']=='right_only']['name']
    if len(only_r):
        lines.append(f"⚠ {len(only_r)} tables only in R output; e.g. {only_r.iloc[:5].tolist()} …")
    if len(only_py):
        lines.append(f"⚠ {len(only_py)} tables only in Python output; e.g. {only_py.iloc[:5].tolist()} …")

    both = merged[merged['_merge']=='both']

    # helper to strip the "_setNNN" suffix so you see the template name
    def template_base(name):
        return name.rsplit('_set',1)[0]

    for field in ['replica','shuffle','agg_fun1','agg_name1','values','valueName','row_format']:
        rcol, pycol = f'R_{field}', f'Py_{field}'
        if rcol not in both or pycol not in both:
            continue

        diff = both[both[rcol] != both[pycol]]['name']
        count = len(diff)
        if count == 0:
            lines.append(f"✔ No differences in `{field}`")
            continue

        # count distinct templates
        bases = diff.map(template_base)
        distinct = bases.nunique()
        examples = diff.iloc[:5].tolist()

        lines.append(
            f"— `{field}` mismatch in {count} tables "
            f"across {distinct} templates; e.g. {examples} …"
        )

    # write out
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == "__main__":
    root = os.path.abspath(os.path.dirname(__file__))
    path_r  = os.path.join(root, 'generator_code', 'PARAM_tablesToGenerate.json')
    path_py = os.path.join(root, 'python_generator_code', 'Py_PARAM_tablesToGenerate.json')
    report  = os.path.join(root, 'comparison_report.txt')

    df_r  = load_and_flatten(path_r,  'R')
    df_py = load_and_flatten(path_py, 'Py')
    compare_tables(df_r, df_py, report)

    print(f"Comparison complete — see {report}")
