import numpy as np
import random
#DONE
# -----------------------------------------------
# STEP 1: Extract names and values by code
# -----------------------------------------------
# Returns the 'names' and 'values' for a given semantic attribute code.

def get_names_values(semantic_data, code):
    for entry in semantic_data:
        if entry.get('code') == code:
            return {
                'names': entry.get('names', []),
                'values': entry.get('values', [])
            }
    return {'names': [], 'values': []}

# # Test STEP 1
# semantic_data = [
#     {"code": "x1", "names": ["country"], "values": ["USA", "UK"]},
#     {"code": "x2", "names": ["year"], "values": [2020, 2021]}
# ]
# print(get_names_values(semantic_data, "x1"))
# # → {'names': ['country'], 'values': ['USA', 'UK']}


# -----------------------------------------------
# STEP 2: Sample values from numeric range
# -----------------------------------------------
# Uses named or direct range codes and ensures uniqueness using make_distinct().

def make_distinct(vals, num_digits=2):
    epsilon = 10 ** -num_digits
    vals = list(vals)
    while len(set(vals)) != len(vals):
        vals.sort()
        for i in range(len(vals) - 1):
            if vals[i] == vals[i+1]:
                vals[i+1] += epsilon
    np.random.shuffle(vals)
    return vals

def get_sample_values_numeric(semantic_values: dict, value_code, num_sample: int, num_digits: int = 2) -> list:
    if isinstance(value_code, str) and value_code in semantic_values:
        lo, hi = semantic_values[value_code]
    elif isinstance(value_code, (list, tuple)) and len(value_code) == 2:
        lo, hi = value_code
    else:
        raise ValueError(f"Invalid value_code: {value_code}")

    if float(lo).is_integer() and float(hi).is_integer():
        lo_i, hi_i = int(lo), int(hi)
        minv = lo_i
        maxv = max(minv + num_sample, hi_i)
        pool = list(range(minv, maxv + 1))
        vals = np.random.choice(pool, size=num_sample, replace=False).tolist()
    else:
        vals = np.round(np.random.uniform(lo, hi, size=num_sample), num_digits).tolist()

    return make_distinct(vals, num_digits)

# # Test STEP 2
# semantic_values = {"int5": [1, 5]}
# np.random.seed(123)
# print(get_sample_values_numeric(semantic_values, "int5", 3, num_digits=0))
# # → [4, 5, 3]


# -----------------------------------------------
# STEP 3: Filter values by keep/remove lists
# -----------------------------------------------
# Flattens structured values and applies filtering logic.

def get_values_from_names(names_and_values: dict, val_keep: list, val_remove: list) -> list:
    names = names_and_values.get('names', [])
    vals = names_and_values.get('values', [])
    flat = []

    for i, v in enumerate(vals):
        name = names[i] if i < len(names) else f"name{i}"
        if isinstance(v, list):
            for sub in v:
                flat.append(f"{name}.{sub}")
        else:
            flat.append(f"{name}.{v}")

    if val_keep:
        return [f for f in flat if any(k in f for k in val_keep)]
    if val_remove:
        return [f for f in flat if all(r not in f for r in val_remove)]
    return flat

# # Test STEP 3
# sample = {
#     "names": ["country", "year"],
#     "values": [["USA", "UK"], [2020, 2021]]
# }
# print(get_values_from_names(sample, [], []))         # → ['country.USA', 'country.UK', 'year.2020', 'year.2021']
# print(get_values_from_names(sample, ['USA'], []))    # → ['country.USA']
# print(get_values_from_names(sample, [], ['UK']))     # → ['country.USA', 'year.2020', 'year.2021']


# -----------------------------------------------
# STEP 4: Sample consecutive values
# -----------------------------------------------
# Picks a block of values of random length within a given range.

def sample_values(val_list, val_sample):
    """
    Picks a block of values of random length within a given range.
    If val_sample is not a 2-element list/tuple, returns ALL values.
    """
    # “[0]” or any single-element val_sample → keep everything
    if not (isinstance(val_sample, (list, tuple)) and len(val_sample) == 2):
        return {'listAttrNames': val_list, 'isAggPossible': 'true'}

    total = len(val_list)
    n, m = val_sample
    # clamp n,m to [1,total]
    n = max(1, min(n, total))
    m = max(n, min(m, total))
    size = n if n == m else int(np.random.randint(n, m + 1))
    start = int(np.random.randint(0, total - size + 1))
    sel = val_list[start:start + size]
    is_agg = 'false' if len(sel) == 1 else 'true'
    return {'listAttrNames': sel, 'isAggPossible': is_agg}


# # Test STEP 4
# np.random.seed(123)
# val_list = ["A", "B", "C", "D", "E"]
# val_sample = [2, 3]
# print(sample_values(val_list, val_sample))
# # → sample with 2–3 consecutive elements from val_list


# -----------------------------------------------
# STEP 5: Sample hierarchical attributes
# -----------------------------------------------
# Applies step 4 logic recursively for each level in hierarchical names.

def sample_values_from_hierarchy(list_composite, val_sample):
    # Split each “A.B.C” into [A,B,C]
    split_rows = [row.split('.') for row in list_composite]
    depth = len(split_rows[0])

    # Build a matrix of rows
    matrix = [row[:] for row in split_rows]

    # Helper: preserve first‐seen order when uniquifying
    def unique_preserve_order(seq):
        seen = set()
        out = []
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    # --------------------------
    # Level 0: sample among top‐level codes
    # --------------------------
    # Extract the 0th column in order
    tops = unique_preserve_order(row[0] for row in matrix)
    r0 = sample_values(tops, val_sample)
    agg_flags = [r0['isAggPossible']]

    # Keep only rows whose top‐level is in r0['listAttrNames']
    matrix = [row for row in matrix if row[0] in r0['listAttrNames']]

    # --------------------------
    # Levels 1..depth-1
    # --------------------------
    for lvl in range(1, depth):
        next_matrix = []
        lvl_flag = 'true'
        # for each distinct parent at level-(lvl-1)
        parents = unique_preserve_order(row[0] for row in matrix)
        for parent in parents:
            # collect all rows under that parent
            group = [row for row in matrix if row[0] == parent]
            # find the unique values at this level
            vals = unique_preserve_order(r[lvl] for r in group)
            r = sample_values(vals, val_sample)
            if r['isAggPossible'] == 'false':
                lvl_flag = 'false'
            # keep only the rows whose lvl value was picked
            allowed = set(r['listAttrNames'])
            next_matrix.extend([row for row in group if row[lvl] in allowed])
        agg_flags.append(lvl_flag)
        matrix = next_matrix

    # Reconstruct the “A.B.C” strings
    collapsed = ['.'.join(row) for row in matrix]
    return {
        'listAttrNames': collapsed,
        'isAggPossible': '.'.join(agg_flags)
    }


# # Test STEP 5
# composite_attrs = [
#     "Asia.China.Beijing", "Asia.China.Shanghai",
#     "Asia.India.Delhi", "Asia.India.Mumbai",
#     "Europe.France.Paris", "Europe.France.Lyon",
#     "Europe.Germany.Berlin", "Europe.Germany.Munich"
# ]
# val_sample = [1, 2]
# np.random.seed(123)
# print(sample_values_from_hierarchy(composite_attrs, val_sample))


# -----------------------------------------------
# STEP 6: Get index from attribute codes
# -----------------------------------------------
# Returns index of first attribute with matching code.

def get_attr_from_codes(attr_list, codes):
    if isinstance(codes, str):
        codes = [codes]
    for i, attr in enumerate(attr_list):
        if attr.get("code") in codes:
            return i
    return None

# # Test STEP 6
# attr_list_example = [
#     {"code": "x1", "names": ["Country"]},
#     {"code": "x2", "names": ["Year"]},
#     {"code": "x3", "names": ["City"]}
# ]
# print(get_attr_from_codes(attr_list_example, "x2"))  # → 1
# print(get_attr_from_codes(attr_list_example, "x5"))  # → None


# -----------------------------------------------
# STEP 7: Get codes by attribute name
# -----------------------------------------------
# Returns all codes where the name is included.

def get_codes_from_name(semantic_data, attr_name):
    codes = []
    for entry in semantic_data.get("data", []):
        if attr_name in entry.get("names", []):
            codes.append(entry["code"])
    return codes

# # Test STEP 7
# semantic_data = {
#     "data": [
#         {"code": "x1", "names": ["Country"]},
#         {"code": "x2", "names": ["Year"]},
#         {"code": "x3", "names": ["City"]}
#     ]
# }
# print(get_codes_from_name(semantic_data, "Year"))     # → ['x2']
# print(get_codes_from_name(semantic_data, "Unknown"))  # → []

