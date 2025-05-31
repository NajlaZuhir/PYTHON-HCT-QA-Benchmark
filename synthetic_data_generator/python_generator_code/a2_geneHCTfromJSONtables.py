import os
import json
import random

import pandas as pd
import itertools
import os
import json
import pandas as pd
import numpy as np
      
import csv
import json

# Optional libraries if later used for table generation
# import pandas as pd

# External scripts (equivalent to source in R)
from config import *               # assumes you have config.py with constants
from toolbox_tables_generator import *  # assumes a toolbox file with functions

# Set seed for reproducibility
random.seed(0)

# Define I/O folders
input_folder = PARAMETERS_FOLDER
output_folder = SEMANTIC_TABLES_FOLDER
semantics_json_file = PARAM_SEMANTICS_JSON  # semantic metadata JSON file
tables_json_file = PARAM_TABLE_TO_GEN_JSON  # table instructions JSON file

# Create the output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Debug flags (set to True for debugging)
DO_NOT_SAVE = False #False
DO_NOT_SAVE_DB_HTML = False
DO_NOT_GENERATE_PIVOT = False

##############
##############
##############

# Initialize signature tracker
SIGNATURES = []

# Load semantic metadata JSON
semantics_json_file = "C:/Users/kasif/OneDrive/Documents/Spring 2025/Internship_QCRI/QCRI/PYTHON-HCT-QA-Benchmark-main/PYTHON-HCT-QA-Benchmark-main/synthetic_data_generator/python_generator_code/PARAM_semantics.json"

with open(semantics_json_file, 'r') as f:
    allSemanticAttributes = json.load(f)



# Load table generation templates JSON
tables_json_file = "C:/Users/kasif/OneDrive/Documents/Spring 2025/Internship_QCRI/QCRI/PYTHON-HCT-QA-Benchmark-main/PYTHON-HCT-QA-Benchmark-main/synthetic_data_generator/python_generator_code/Py_PARAM_tablesToGenerate.json"

with open(tables_json_file, 'r') as f:
    allTablesJSON = json.load(f)


# Initialize table generation counter
totalNumTableGene = 0

# Initialize pivot table and signature container
allPivot = {
    "df": [],
    "signature": []
}

# Extract table names from templates
tableJSONname = [table["name"] for table in allTablesJSON]

# Count number of tables to generate
numTables = len(allTablesJSON)


#########################################################
for itab in range(len(allTablesJSON)): #########len(allTablesJSON)):######2100 times
#########################################################
    
    tableJSON = allTablesJSON[itab]

    # Output file name prefix (used in saved CSV/HTML/PDF/etc.)
    outputNamePrefix = tableJSON["name"]

    # Number of replicas (copies) to generate
    numReplica = tableJSON["replica"]

    # Aggregation function and name (e.g., avg, sum)
    agg_fun = tableJSON["agg_fun1"]
    agg_name = tableJSON["agg_name1"]

    # Title of the table
    tableTitle = tableJSON["valueName"]

    # Track the current replica number
    curReplica = 0

    # Control variables for retrying table generation if duplicate
    trialCnt = 0
    trialCntMAX = 10
    geneNextReplica = True
    ################################################################
    ################################################################
    # For each replica of a table instruction, 
    # get the colum and row info from semantic data 
    # then filter using valkeep and valremove and sample 
    # based on the instructions, then finally check for 
    # multi level attributes, (1 or more - 2 conditions). 
    # Load the labels to be used for the HCT in [L]
    # Applied to : while loop & colum vector & row vector
    ################################################################
    ################################################################
    while geneNextReplica:

        curReplica += 1

        # Set seed to allow debugging if some replica is wrong
        seedValue = (itab - 1) * numReplica + curReplica
        random.seed(seedValue)

        print(f"\nNAME: {outputNamePrefix}_{curReplica} Generate DB table: {itab}/{numTables} -- Replica: {curReplica}/{numReplica}")

        if curReplica == numReplica:
            geneNextReplica = False

        # Get list of attributes for the DB table

        # Read all column and row attributes (assume a single group)
        groupInd = 0  # Python uses 0-based indexing

        L = None
        DO_AGG = None
        colCodes = None
        colCodeNames = None
        rowCodes = None
        rowCodeNames = None

        rowTableFormat = tableJSON["row_format"]
        colAttr = tableJSON["columns"]["groups"][groupInd]["attributes"]
        rowAttr = tableJSON["rows"]["groups"][groupInd]["attributes"]
        # namesAndValues$names = ["State", "City"]
        # namesAndValues$values = list of all states and their cities
        

        # Sample values for this example:
        semantic_data = allSemanticAttributes["data"]
        

        colCodes = []
        colCodeNames = []
        DO_AGG = {}
        L = {}

        for j in range(len(colAttr)):
            colCode = colAttr[j]["code"]
            valKeep = colAttr[j].get("keep", [])
            valRemove = colAttr[j].get("remove", [])
            valSample = colAttr[j]["sample"]
            isSymmetric = colAttr[j].get("symmetric", "true")

            # === getNamesValues ===
            namesAndValues = {}
            for entry in allSemanticAttributes["data"]:
                if entry["code"] == colCode:
                    namesAndValues["names"] = entry["names"]
                    namesAndValues["values"] = entry["values"]
                    break

            depthAttr = len(namesAndValues["names"])

            if depthAttr > 1:
                # === getValuesFromNames ===
                Ltmp = []
                for v in namesAndValues["values"]:
                    key = list(v.keys())[0]
                    if valKeep and key not in valKeep:
                        continue
                    if valRemove and key in valRemove:
                        continue
                    Ltmp.append(v)

                # === multilevel processing ===
                colNames = ".".join(namesAndValues["names"])
                colCodes.append(colCode)
                colCodeNames.append(colNames)

                # === sampleValuesFromHierarchy ===
                result = []
                for parent in Ltmp:
                    k, v = list(parent.items())[0]
                    if isinstance(valSample, list) and len(valSample) == 2:
                        sample_size = random.randint(valSample[0], valSample[1])
                    else:
                        print(f"⚠️ Invalid valSample for {colCode or rowCode}: {valSample}")
                        sample_size = 1  # or set a default fallback

                    sampled = random.sample(v, min(sample_size, len(v)))
                    for child in sampled:
                        result.append(f"{k}.{child}")

                L[colNames] = result
                DO_AGG[colNames] = "true"

            else:
                # === getValuesFromNames ===
                Ltmp = []
                for v in namesAndValues["values"]:
                    key = v
                    if valKeep and key not in valKeep:
                        continue
                    if valRemove and key in valRemove:
                        continue
                    Ltmp.append(key)

                colNames = ".".join(namesAndValues["names"])

                if isSymmetric == "false" and j > 0:
                    colCodeParent = colCodes[-1]
                    colNameParent = colCodeNames[-1]
                    Lparent = L[colNameParent]
                    Lnew = []
                    DO_AGGnew = "true"

                    for itm in Lparent:
                        if isinstance(valSample, list) and len(valSample) == 2:
                            sample_size = random.randint(valSample[0], valSample[1])
                        else:
                            print(f"⚠️ Invalid valSample for {colCode or rowCode}: {valSample}")
                            sample_size = 1  # or set a default fallback

                        sampled = random.sample(Ltmp, min(sample_size, len(Ltmp)))
                        Lnew.extend([f"{itm}.{x}" for x in sampled])

                    colCodeNew = f"{colCodeParent}.{colCode}"
                    colCodes[-1] = colCodeNew
                    colNamesNew = f"{colNameParent}.{colNames}"
                    colCodeNames[-1] = colNamesNew

                    L.pop(colNameParent, None)
                    L[colNamesNew] = Lnew
                    DO_AGG.pop(colNameParent, None)
                    DO_AGG[colNamesNew] = DO_AGGnew

                else:
                    colCodes.append(colCode)
                    colCodeNames.append(colNames)
                    if isinstance(valSample, list) and len(valSample) == 2:
                        sample_size = random.randint(valSample[0], valSample[1])
                    else:
                        print(f"⚠️ Invalid valSample for {colCode or rowCode}: {valSample}")
                        sample_size = 1  # or set a default fallback

                    sampled = random.sample(Ltmp, min(sample_size, len(Ltmp)))
                    L[colNames] = sampled
                    DO_AGG[colNames] = "true"
        
        rowCodes = []
        rowCodeNames = []

        for j in range(len(rowAttr)):
            rowCode = rowAttr[j]["code"]
            valKeep = rowAttr[j].get("keep", [])
            valRemove = rowAttr[j].get("remove", [])
            valSample = rowAttr[j]["sample"]
            isSymmetric = rowAttr[j].get("symmetric", "true")

            # === getNamesValues ===
            namesAndValues = {}
            for entry in allSemanticAttributes["data"]:
                if entry["code"] == rowCode:
                    namesAndValues["names"] = entry["names"]
                    namesAndValues["values"] = entry["values"]
                    break

            depthAttr = len(namesAndValues["names"])

            if depthAttr > 1:
                # === getValuesFromNames ===
                Ltmp = []
                for v in namesAndValues["values"]:
                    key = list(v.keys())[0]
                    if valKeep and key not in valKeep:
                        continue
                    if valRemove and key in valRemove:
                        continue
                    Ltmp.append(v)

                rowNames = ".".join(namesAndValues["names"])
                rowCodes.append(rowCode)
                rowCodeNames.append(rowNames)

                # === sampleValuesFromHierarchy ===
                result = []
                for parent in Ltmp:
                    k, v = list(parent.items())[0]
                    if isinstance(valSample, list) and len(valSample) == 2:
                        sample_size = random.randint(valSample[0], valSample[1])
                    else:
                        print(f"⚠️ Invalid valSample for {colCode or rowCode}: {valSample}")
                        sample_size = 1  # or set a default fallback

                    sampled = random.sample(v, min(sample_size, len(v)))
                    for child in sampled:
                        result.append(f"{k}.{child}")

                L[rowNames] = result
                DO_AGG[rowNames] = "true"

            else:
                # === getValuesFromNames ===
                Ltmp = []
                for v in namesAndValues["values"]:
                    key = v
                    if valKeep and key not in valKeep:
                        continue
                    if valRemove and key in valRemove:
                        continue
                    Ltmp.append(key)

                rowNames = ".".join(namesAndValues["names"])

                if isSymmetric == "false" and j > 0:
                    rowCodeParent = rowCodes[-1]
                    rowNameParent = rowCodeNames[-1]
                    Lparent = L[rowNameParent]
                    Lnew = []
                    DO_AGGnew = "true"

                    for itm in Lparent:
                        if isinstance(valSample, list) and len(valSample) == 2:
                            sample_size = random.randint(valSample[0], valSample[1])
                        else:
                            print(f"⚠️ Invalid valSample for {colCode or rowCode}: {valSample}")
                            sample_size = 1  # or set a default fallback
                        sampled = random.sample(Ltmp, min(sample_size, len(Ltmp)))
                        Lnew.extend([f"{itm}.{x}" for x in sampled])

                    rowCodeNew = f"{rowCodeParent}.{rowCode}"
                    rowCodes[-1] = rowCodeNew
                    rowNamesNew = f"{rowNameParent}.{rowNames}"
                    rowCodeNames[-1] = rowNamesNew

                    L.pop(rowNameParent, None)
                    L[rowNamesNew] = Lnew
                    DO_AGG.pop(rowNameParent, None)
                    DO_AGG[rowNamesNew] = DO_AGGnew
                else:
                    rowCodes.append(rowCode)
                    rowCodeNames.append(rowNames)
                    if isinstance(valSample, list) and len(valSample) == 2:
                        sample_size = random.randint(valSample[0], valSample[1])
                    else:
                        print(f"⚠️ Invalid valSample for {colCode or rowCode}: {valSample}")
                        sample_size = 1  # or set a default fallback

                    sampled = random.sample(Ltmp, min(sample_size, len(Ltmp)))
                    L[rowNames] = sampled
                    DO_AGG[rowNames] = "true"
        print("\n=== COLUMN VECTORS ===")
        for key in colCodeNames:
            if key in L:
                print(f"{key}: {L[key]}")

        print("\n=== ROW VECTORS ===")
        for key in rowCodeNames:
            if key in L:
                print(f"{key}: {L[key]}")
        
   
        
        #============================================
        #============================================
        # Here we are just displaying the table
        #============================================
        #============================================
        expL = pd.DataFrame(list(itertools.product(*L.values())), columns=L.keys())
        print(expL)

        cleaned_columns = []
        final_df = pd.DataFrame()

        # Loop over each column in expL
        for col in expL.columns:
            col_parts = col.split(".")
            cleaned_columns.extend(col_parts)

            if len(col_parts) == 1:
                # If not a composite column name, keep as-is
                final_df = pd.concat([final_df, expL[[col]]], axis=1)
            else:
                # Split values in the column
                split_values = expL[col].apply(lambda x: pd.Series(str(x).split(".")))
                split_values.columns = col_parts
                final_df = pd.concat([final_df, split_values], axis=1)

        # Final output
        final_df.columns = cleaned_columns

        #===================================================
                # ==== GENERATE VALUE COLUMN =====
        #===================================================
        valCode = tableJSON["values"]  # could be range like [-100, 100]
        numSample = len(final_df)
        semanticValues = allSemanticAttributes["values"]

        # If valCode is a numeric range (e.g. [min, max]), sample from that
        if isinstance(valCode, list) and len(valCode) == 2:
            low = valCode[0]
            high = valCode[1]
            VAL = np.round(np.random.uniform(low, high, numSample), NUM_DECIMAL_DIGITS_REAL_FORMAT)

        # If valCode is a predefined semantic code (e.g. "realUnit"), sample from that
        elif isinstance(valCode, str) and valCode in semanticValues:
            low, high = semanticValues[valCode]
            VAL = np.round(np.random.uniform(low, high, numSample), NUM_DECIMAL_DIGITS_REAL_FORMAT)

        # Default fallback if value code not understood
        else:
            VAL = np.zeros(numSample)

        # ==== DETERMINE FORMAT TYPE ====
        if np.issubdtype(type(VAL[0]), np.integer):
            strValFormat = STR_INT_VAL_FORMAT
        else:
            strValFormat = STR_REAL_VAL_FORMAT

        # ==== ASSEMBLE FINAL TABLE ====
        final_df["Value"] = pd.to_numeric(VAL)

        # Create canAggTable equivalent
        canAggTable = pd.DataFrame(
            [list(DO_AGG.keys())],
            columns=[key.split(".")[-1] for key in DO_AGG.keys()],
            index=["canAggregate"]
        )

        # ==== DEBUG OUTPUT ====
        if DO_NOT_SAVE:
            print("\n=== FINAL TABLE ===")
            print(final_df)
        
        shuffle_mode = tableJSON["shuffle"]
        
        NO_SHUFFLE= True
        if shuffle_mode == "rows":
            final_df = final_df.sample(frac=1).reset_index(drop=True)
            NO_SHUFFLE= False
        elif shuffle_mode == "cols":
            non_value_cols = [col for col in final_df.columns if col != "Value"]
            shuffled_cols = random.sample(non_value_cols, len(non_value_cols))
            final_df = final_df[shuffled_cols + ["Value"]]  # Keep 'Value' at end
            NO_SHUFFLE= False
        elif shuffle_mode == "rowscols":
            # Shuffle both rows and columns (except 'Value')
            final_df = final_df.sample(frac=1).reset_index(drop=True)
            non_value_cols = [col for col in final_df.columns if col != "Value"]
            shuffled_cols = random.sample(non_value_cols, len(non_value_cols))
            final_df = final_df[shuffled_cols + ["Value"]]
            NO_SHUFFLE= False
        elif shuffle_mode == "all":
            # Combine all columns including "Value", shuffle everything
            shuffled_cols = random.sample(final_df.columns.tolist(), len(final_df.columns))
            final_df = final_df[shuffled_cols]
            NO_SHUFFLE= False
        print("shuffle")
        print(final_df)

        addBorderLines = random.choice([False, True])  # Randomly selects True or False
        # 1. Border style as string
        border = "WithBorderLines" if addBorderLines else "WithoutBorderLines"

        # 2. Flatten all values in L into a single string separated by '&&&'
        allColsRowsValuesSTR = "&&&".join([str(item) for sublist in L.values() for item in sublist])

        # 3. Join colCodeNames and rowCodeNames into strings
        colCodeNamesSTR = "&&&".join(colCodeNames)  # assumes list of strings
        rowCodeNamesSTR = "&&&".join(rowCodeNames)

        # 4. Construct the base signature with values, structure, and style
        curSignatureDB = (
            f"ALL&&&{allColsRowsValuesSTR}"
            f"&&&COLS&&&{colCodeNamesSTR}"
            f"&&&ROWS&&&{rowCodeNamesSTR}"
            f"&&&STYLE&&&{border}"
        )

        # 5. Empty aggregation placeholders (can be updated later)
        signatureAGGempty = (
            "&&&AGG_NAME&&&"
            "&&&AGG_FUN&&&"
            "&&&AGG_COLS&&&"
            "&&&AGG_ROWS&&&"
        )

        # 6. Final full signature string
        curSignature = curSignatureDB + signatureAGGempty
        print(curSignature)

        # =====================================================
# ===============  Tables signature check  ============
# =====================================================

        if curSignature in SIGNATURES:
            print(f"------------------------------------------- WARNING --- Table design already exists, trial: {trialCnt}/{trialCntMAX - 1}")

            # Already exists — try again
            trialCnt += 1

            if trialCnt >= trialCntMAX:
                if curReplica == numReplica:
                    geneNextReplica = False  # stop trying further
                trialCnt = 0
            else:
                curReplica -= 1  # retry this same replica again
                geneNextReplica = True
        else:
            print("Table design is unique, proceed...")
            SIGNATURES.append(curSignature)
            #=======================================================
            #=======================================================
            # CSV has row1- human readable and ro2 is SQL safe headers
            #=======================================================
            #=======================================================
            if not DO_NOT_SAVE:
                # ==============================
                # Save DB table as CSV
                # ==============================
                print("Generate CSV for DB TABLE")

                # Generate SQL-compatible column names (e.g., lowercase, underscores)
                colnamesSQL = [col.replace(" ", "_").lower() for col in final_df.columns]

                # Create a new DataFrame: SQL names as first row, actual data follows
                DBtableCleanAsSTRING = pd.concat([
                    pd.DataFrame([colnamesSQL], columns=final_df.columns),
                    final_df.astype(str)
                ], ignore_index=True)

                filenameCSV = os.path.join(output_folder, f"{outputNamePrefix}_{curReplica}_DB.csv")
                DBtableCleanAsSTRING.to_csv(filenameCSV, index=False, quoting=csv.QUOTE_NONE)

                # ==============================
                # Save DB table as HTML (for humans)
                # ==============================
                if not DO_NOT_SAVE_DB_HTML:
                    print("Generate HTML for DB TABLE")
                    filenameHTML = os.path.join(output_folder, f"{outputNamePrefix}_{curReplica}_DB.html")
                    with open(filenameHTML, "w", encoding="utf-8") as f:
                        f.write(final_df.to_html(index=False, escape=False))

                # ==============================
                # Save JSON signature
                # ==============================
                print("Generate JSON signature (no aggregation info)")

                jsonSTR_SIG_DB = {
                    "id": f"{outputNamePrefix}_{curReplica}",
                    "formatValue": strValFormat,
                    "seedValue": seedValue,
                    "signature": curSignature
                }

                filenameJSON_SIG_DB = os.path.join(output_folder, f"{outputNamePrefix}_{curReplica}_SIG_DB.json")
                with open(filenameJSON_SIG_DB, "w") as f:
                    f.write(json.dumps(jsonSTR_SIG_DB, indent=2))


            ##############################################################               
            ##############################################################            
            # Till here we generate signatures for each table replica
            # The table is saved in CSV, html only if its unique in TABLES (Output Folder) 
            ##############################################################
            ##############################################################
            # Initialize symmetry flags
            rowNestingSymmetric = "true"
            multiLevelColumnSymmetric = "true"

            # Loop over each composite attribute in L
            for iname in L.keys():
                ulName = iname.split(".")
                
                # Only process composite (multi-level) names
                if len(ulName) > 1:
                    print(f"\nChecking composite attribute: {iname}")
                    unfolded_values = [v.split(".") for v in L[iname]]
                    print("Unfolded values:")
                    for val in unfolded_values:
                        print(val)

                    # Build matrix: rows = hierarchy levels, cols = number of entries
                    num_levels = len(unfolded_values[0])  # e.g., 2 if State.City
                    num_entries = len(unfolded_values)

                    # Transpose the matrix to check each level independently
                    mL = list(zip(*unfolded_values))  # mL[level][entry]

                    for level in range(1, num_levels):  # start from second level (index 1)
                        level_values = mL[level]  # all values at this hierarchy level
                        unique_vals = set(level_values)
                        print(f"Level {level} values: {level_values}")
                        print(f"Unique values at level {level}: {unique_vals}")
                        
                        if len(unique_vals) != 1:
                            print(f"Asymmetry detected at level {level} of {iname}")
                            # Determine if it's a column or row attribute
                            if ulName[0] in colCodeNames:
                                print(f"Marked multiLevelColumnSymmetric = false for: {ulName[0]}")
                                multiLevelColumnSymmetric = "false"
                                print('========================================')
                            elif ulName[0] in rowCodeNames:
                                print(f"Marked rowNestingSymmetric = false for: {ulName[0]}")
                                rowNestingSymmetric = "false"
                                print('========================================')
            # Final result
            print("\n=== SYMMETRY RESULTS ===")
            print("Row Nesting Symmetric:", rowNestingSymmetric)
            print("Multi-Level Column Symmetric:", multiLevelColumnSymmetric)

            

            # ---- Initial Setup ----
            if not DO_NOT_GENERATE_PIVOT:
                print("Generate PIVOT TABLE")

                # ---- Column Presets for JSON Table Format ----
                cumColAddTot = 0
                multiLevelColumn = "false"
                columnAggregationLocal = "false"
                columnAggregationGlobal = "false"
                aggColAttrNames = []

                # ---- Row Presets for JSON Table Format ----
                cumRowAddTot = 0
                rowNesting = "false"
                rowAggregationLocal = "false"
                rowAggregationGlobal = "false"
                rowGroupLabel = "false"
                aggRowAttrNames = []

                # ---- Create Pivot Table Object ----
                # Simulate R6 PivotTable object using placeholder class or custom logic

                pt_data = final_df.copy()  # assuming DBtable is a pandas DataFrame

                # ---- Replace "Total" with agg_name (this behavior must be mimicked in formatting or captions) ----
                totalCaption = agg_name
                totalPosition = "after"  # only useful if your pivot tool supports it

                # Custom pivot handling will follow here
                # For now, data is loaded in pt_data (which can be displayed with pivot_ui later)

                # Final result simulation
                pivot_column_setup = []

                # Column Grouping
                
                if NO_SHUFFLE:
                    for clc in colCodes:
                        namesAndValues = next(entry for entry in allSemanticAttributes["data"] if entry["code"] == clc)
                        nam = namesAndValues["names"]
                        for nm in nam:
                            indAttr = clc
                            addTot = colAttr[0]["agg_pos1"] != "none"
                            for full_col_name in canAggTable.columns:
                                if nm in full_col_name:  # partial match
                                    if canAggTable.loc["canAggregate", full_col_name] == "false":
                                        addTot = False
                            if addTot:
                                cumColAddTot += 1
                                aggColAttrNames.append(nm)

                            pivot_column_setup.append({"Column Name": nm, "Add Total": addTot})
                            # Update JSON format indicators
                        if len(colCodes) > 1:
                            multiLevelColumn = "true"
                        if cumColAddTot == len(colCodes):
                            columnAggregationGlobal = "true"
                        if cumColAddTot > 1:
                            columnAggregationLocal = "true"

                        pivot_col_df = pd.DataFrame(pivot_column_setup)
                    # === UPDATE for JSON table format ===
                    multiLevelColumn = "false"
                    columnAggregationGlobal = "false"
                    columnAggregationLocal = "false"

                    if len(colCodeNames) > 1:
                        multiLevelColumn = "true"

                    if cumColAddTot == len(colCodeNames):
                        columnAggregationGlobal = "true"

                    if cumColAddTot > 1:
                        columnAggregationLocal = "true"

                    # === Prepare for row grouping ===
                    row_level = 0
                    indentRowWithTotal = False
                    # Simulate pt$addRowDataGroups()
                    added_row_data_groups = []

                    for rwc in rowCodes:
                        # Get attribute block for this code
                        namesAndValues = next(entry for entry in allSemanticAttributes["data"] if entry["code"] == rwc)
                        nam = namesAndValues["names"]
                        for nm in nam:
                            row_level += 1
                            # Access rowAttr directly by code name (Python dict)
                            indAttr = rwc
                            attr_config = rowAttr[0]["agg_pos1"]  # Assuming dict: {"Pollutions": [{"agg_pos1": "top"}]}
                            # Check if this row can be aggregated
                            addTot = attr_config != "none"
                            # Disable aggregation if not allowed by canAggTable
                            matched_cols = [col for col in canAggTable.columns if nm in col]
                            if matched_cols and canAggTable.loc["canAggregate", matched_cols[0]] == "false":
                                addTot = False

                            # Track aggregatable attributes
                            if addTot:
                                cumRowAddTot += 1
                                aggRowAttrNames.append(nm)

                            # Determine row indent
                            indentRow = len(rowTableFormat) > 0 and rowTableFormat != "new" and row_level == 1
                            print(f"{nm} indentRow {indentRow}")

                            # Format the indented row
                            if indentRow and addTot:
                                attr_config = rowAttr[0]
                                if attr_config["agg_pos1"] == "top":

                                    outlineBefore = {"isEmpty": False, "mergeSpace": "dataGroupsOnly"}
                                    indentRowWithTotal = True
                                else:
                                    outlineBefore = {"isEmpty": True, "mergeSpace": "dataGroupsAndCellsAs1"}
                                    rowGroupLabel = "true"
                            elif indentRow and not addTot:
                                outlineBefore = True
                                rowGroupLabel = "true"
                            else:
                                outlineBefore = False

                            # Block totals at deeper levels
                            if row_level > 1 and indentRowWithTotal:
                                addTot = False
                            if row_level > 1:
                                outlineBefore = False

                            # Simulate: pt$addRowDataGroups(nm, outlineBefore=..., addTotal=...)
                            added_row_data_groups.append({
                                "Row Name": nm,
                                "Outline Before": outlineBefore,
                                "Add Total": addTot
                            })
                            pivot_row_df = pd.DataFrame(added_row_data_groups)
                            
                            


                    # Post-processing flags
                    if len(rowCodeNames) > 1:
                        rowNesting = "true"
                    if cumRowAddTot == len(rowCodeNames):
                        rowAggregationGlobal = "true"
                    if cumRowAddTot > 1:
                        rowAggregationLocal = "true"
                    
                                        # Add a type column to distinguish
                    pivot_col_df["Group Type"] = "Column"
                    pivot_row_df["Group Type"] = "Row"

                    # Align column names
                    pivot_col_df.rename(columns={"Column Name": "Name"}, inplace=True)
                    pivot_row_df.rename(columns={"Row Name": "Name"}, inplace=True)

                    # Combine both
                    pivot_df = pd.concat([pivot_col_df, pivot_row_df], ignore_index=True)

                    # Display full pivot grouping structure
                    print(pivot_df)
                    print('no shuffle')
                else:
                    # Begin conversion for shuffled case
                    pivot_column_setup = []
                    cumColAddTot = 0
                    aggColAttrNames = []

                    # ---- Column Aggregation Handling ----
                    for nm in colCodeNames:
                        for nm, code in zip(colCodeNames, colCodes):
                         # e.g. "USA"
                            entry = next(e for e in allSemanticAttributes["data"] if e["code"] == code)
                            
                        indAttr = 0  # Simulated index (adjust logic as needed)
                        attr_config = colAttr[indAttr]
                        addTot = attr_config["agg_pos1"] != "none"
                        if nm.split(".")[-1] in canAggTable.columns:
                            if canAggTable.loc["canAggregate", nm.split(".")[-1]] == "false":
                                addTot = False
                        if addTot:
                            cumColAddTot += 1
                            aggColAttrNames.append(nm)

                        pivot_column_setup.append({"Column Name": nm, "Add Total": addTot})

                    pivot_col_df = pd.DataFrame(pivot_column_setup)

                    # ---- Row Aggregation Handling ----
                    row_level = 0
                    indentRowWithTotal = False
                    cumRowAddTot = 0
                    aggRowAttrNames = []
                    added_row_data_groups = []

                    for nm in rowCodeNames:
                        row_level += 1
                        for nm, code in zip(rowCodeNames, rowCodes):

                              # e.g. "USA"rr
                            entry = next(e for e in allSemanticAttributes["data"] if e["code"] == code)
                        indAttr = 0
                        attr_config = rowAttr[indAttr]

                        addTot = attr_config["agg_pos1"] != "none"
                        if nm.split(".")[-1] in canAggTable.columns:
                            if canAggTable.loc["canAggregate", nm.split(".")[-1]] == "false":
                                addTot = False
                        if addTot:
                            cumRowAddTot += 1
                            aggRowAttrNames.append(nm)

                        indentRow = len(rowTableFormat) > 0 and rowTableFormat != "new" and row_level == 1
                        if indentRow and addTot:
                            if attr_config["agg_pos1"] == "top":
                                outlineBefore = {"isEmpty": False, "mergeSpace": "dataGroupsOnly"}
                                indentRowWithTotal = True
                            else:
                                outlineBefore = {"isEmpty": True, "mergeSpace": "dataGroupsAndCellsAs1"}
                                rowGroupLabel = "true"
                        elif indentRow and not addTot:
                            outlineBefore = True
                            rowGroupLabel = "true"
                        else:
                            outlineBefore = False

                        if row_level > 1 and indentRowWithTotal:
                            addTot = False
                        if row_level > 1:
                            outlineBefore = False

                        added_row_data_groups.append({
                            "Row Name": nm,
                            "Outline Before": outlineBefore,
                            "Add Total": addTot
                        })

                    pivot_row_df = pd.DataFrame(added_row_data_groups)

                    # ---- Post-Processing ----
                    if len(colCodeNames) > 1:
                        multiLevelColumn = "true"
                    else:
                        multiLevelColumn = "false"

                    if cumColAddTot == len(colCodeNames):
                        columnAggregationGlobal = "true"
                    else:
                        columnAggregationGlobal = "false"

                    if cumColAddTot > 1:
                        columnAggregationLocal = "true"
                    else:
                        columnAggregationLocal = "false"

                    if len(rowCodeNames) > 1:
                        rowNesting = "true"
                    else:
                        rowNesting = "false"

                    if cumRowAddTot == len(rowCodeNames):
                        rowAggregationGlobal = "true"
                    else:
                        rowAggregationGlobal = "false"

                    if cumRowAddTot > 1:
                        rowAggregationLocal = "true"
                    else:
                        rowAggregationLocal = "false"

                    # ---- Combine both groupings for final output ----
                    pivot_col_df["Group Type"] = "Column"
                    pivot_row_df["Group Type"] = "Row"
                    pivot_col_df.rename(columns={"Column Name": "Name"}, inplace=True)
                    pivot_row_df.rename(columns={"Row Name": "Name"}, inplace=True)
                    pivot_df = pd.concat([pivot_col_df, pivot_row_df], ignore_index=True)
                    print(pivot_df)
                    print('shuffle happened')
                import os
                import json
                import pandas as pd
                import numpy as np

                # Sample placeholders - replace with actual values in your code
                
                # ==== Signature Aggregation String ====
                signatureAGG = (
                    f"&&&AGG_NAME&&&{agg_name}"
                    f"&&&AGG_FUN&&&{agg_fun}"
                    f"&&&AGG_COLS&&&{'&&&'.join(aggColAttrNames)}"
                    f"&&&AGG_ROWS&&&{'&&&'.join(aggRowAttrNames)}"
                )

                signatureHCT = curSignatureDB + signatureAGG

                # ==== Define Calculation ====
                # === Fix: Ensure aggRowAttrNames is a valid list ===
                if isinstance(aggRowAttrNames, str):
                    aggRowAttrNames = [aggRowAttrNames]
                elif aggRowAttrNames is None:
                    aggRowAttrNames = []

                print("aggRowAttrNames:", aggRowAttrNames)
                print("final_df.columns:", final_df.columns.tolist())
                
                if aggRowAttrNames:
                    # Flatten aggRowAttrNames if they contain composite 
                    expandedAggRowAttrNames = []
                    for name in aggRowAttrNames:
                        if "." in name:
                            expandedAggRowAttrNames.extend(name.split("."))
                        else:
                            expandedAggRowAttrNames.append(name)

                    # Debug
                    print("Expanded aggregation row attributes:", expandedAggRowAttrNames)

                    if agg_fun == "avg":
                        dfPivot = final_df.groupby(expandedAggRowAttrNames)[["Value"]].mean().reset_index()
                    elif agg_fun == "min":
                        dfPivot = final_df.groupby(expandedAggRowAttrNames)[["Value"]].min().reset_index()
                    elif agg_fun == "max":
                        dfPivot = final_df.groupby(expandedAggRowAttrNames)[["Value"]].max().reset_index()
                    else:
                        dfPivot = final_df.groupby(expandedAggRowAttrNames)[["Value"]].sum().reset_index()
                else:
                    print("⚠️ Warning: No aggregation row attributes found. Skipping pivot table.")
                    dfPivot = final_df.copy()  # or skip saving/pivoting altogether
                    DO_NOT_SAVE = True


                # ==== Check Validity ====
                warningMsg = ""
                DO_NOT_SAVE = False

                if dfPivot.isna().any().any():
                    warningMsg += " Contains NA! "
                if dfPivot.shape[1] < 2:
                    warningMsg += " Only one column! "
                if dfPivot.shape[0] < 2:
                    warningMsg += " Only one row! "

                if len(warningMsg) > 0:
                    DO_NOT_SAVE = True
                    print(f"***** WARNING! ***** {warningMsg}")
                else:
                    DO_NOT_SAVE = False

                # ==== SAVE OUTPUT ====
                if not DO_NOT_SAVE:
                    if HTML_OK:
                        os.makedirs(output_folder, exist_ok=True)
                        filenameHTML = os.path.join(output_folder, f"{outputNamePrefix}_{curReplica}_HCT.html")
                        styleSTR = """
                        <style>
                        table {
                            border: 1px solid;
                            border-collapse: collapse;
                        }
                        th, td {
                            border: 1px solid;
                            padding: 5px;
                            text-align: center;
                            vertical-align: center;
                        }
                        </style>
                        """ if addBorderLines else """
                        <style>
                        table {
                            border: 0px solid;
                            border-collapse: collapse;
                        }
                        th, td {
                            border: 0px solid;
                            padding: 5px;
                            text-align: left;
                            vertical-align: top;
                        }
                        </style>
                        """
                        autoscale_script = """
                        <script>
                        let tb = document.getElementsByTagName('table');
                        let pr = document.getElementsByClassName('mytable');
                        let cw = pr[0].clientWidth, sw = pr[0].scrollWidth, ch = pr[0].clientHeight, sh = window.innerHeight;
                        for (let i=1; i<100; i++) {
                            let scale = cw/sw;
                            tb[0].style.fontSize = (i*scale) + 'px';
                            cw = pr[0].clientWidth;
                            sw = pr[0].scrollWidth;
                            ch = pr[0].clientHeight;
                            sh = window.innerHeight;
                            if ((cw < sw)||(ch > sh)) {
                                let cnt = i-1;
                                tb[0].style.fontSize = (cnt*scale) + 'px';
                                break;
                            }
                        }
                        </script>
                        """

                        html_content = dfPivot.to_html(index=False)
                        full_html = f"<html><head>{styleSTR}</head><body><div class='mytable'><h1>{tableTitle}</h1>{html_content}</div>{autoscale_script}</body></html>"

                        with open(filenameHTML, "w", encoding="utf-8") as f:
                            f.write(full_html)

                        print("HTML saved at:", filenameHTML)
                    print("************** SAVING TABLE *************")

                    # Save CSV
                    filenameCSV = os.path.join(output_folder, f"{outputNamePrefix}_{curReplica}_HCT.csv")
                    dfPivot.to_csv(filenameCSV, index=False)

                    # Save HTML
                    filenameHTML = os.path.join(output_folder, f"{outputNamePrefix}_{curReplica}_HCT.html")
                    dfPivot.to_html(filenameHTML, index=False)

                    # Save JSON Signature
                    jsonSTR_SIG_HCT = {
                        "id": f"{outputNamePrefix}_{curReplica}",
                        "formatValue": strValFormat,
                        "seedValue": seedValue,
                        "signature": signatureHCT
                    }
                    filenameJSON_SIG_HCT = os.path.join(output_folder, f"{outputNamePrefix}_{curReplica}_SIG_HCT.json")
                    with open(filenameJSON_SIG_HCT, "w") as f:
                        json.dump(jsonSTR_SIG_HCT, f, indent=2)

                    # Save Full JSON Description
                    jsonSTR = {
                        "id": f"{outputNamePrefix}_{curReplica}",
                        "formatValue": strValFormat,
                        "seedValue": seedValue,
                        "signature": signatureHCT,
                        "image_source": filenameHTML,
                        "state": "labelled",
                        "concern": False,
                        "notes": "",
                        "properties": {
                            "Standard Relational Table": False,
                            "Multi Level Column": False,
                            "Balanced Multi Level Column": True,
                            "Symmetric Multi Level Column": True,
                            "Unbalanced Multi Level Column": False,
                            "Asymmetric Multi Level Column": False,
                            "Column Aggregation": True,
                            "Global Column Aggregation": True,
                            "Local Column-Group Aggregation": False,
                            "Explicit Column Aggregation Terms": True,
                            "Implicit Column Aggregation Terms": False,
                            "Row Nesting": False,
                            "Balanced Row Nesting": True,
                            "Symmetric Row Nesting": True,
                            "Unbalanced Row Nesting": False,
                            "Asymmetric Row Nesting": False,
                            "Row Aggregation": True,
                            "Global Row Aggregation": True,
                            "Local Row-Group Aggregation": False,
                            "Explicit Row Aggregation Terms": True,
                            "Implicit Row Aggregation Terms": False,
                            "Split Header Cell": False,
                            "Row Group Label": False
                        },
                        "themes": []
                    }
                    filenameJSON = os.path.join(output_folder, f"{outputNamePrefix}_{curReplica}_HCT.json")
                    with open(filenameJSON, "w") as f:
                        json.dump(jsonSTR, f, indent=2)

                print("✅ Done")

                