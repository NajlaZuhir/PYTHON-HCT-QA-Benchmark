import os
import json
import itertools
import random

# Try to import configuration from a config.py file.
try:
    from config import PARAMETERS_FOLDER, PARAM_SEMANTICS_JSON, PARAM_TABLE_TEMPLATES_JSON, PARAM_TABLE_TO_GEN_JSON
except ImportError:
    # If no config.py exists, we define default paths.
    PARAMETERS_FOLDER = "./"
    PARAM_SEMANTICS_JSON = "semantics.json"
    PARAM_TABLE_TEMPLATES_JSON = "tableTemplates.json"
    PARAM_TABLE_TO_GEN_JSON = "tableToGen.json"

class TableGenerator:
    """
    A simple table generator class that reads semantic and template JSON files,
    creates table instances based on provided parameters, and writes the output
    to a JSON file.
    """

    def __init__(self,
                 input_folder=PARAMETERS_FOLDER,
                 semantics_file=PARAM_SEMANTICS_JSON,
                 table_templates_file=PARAM_TABLE_TEMPLATES_JSON,
                 output_file=PARAM_TABLE_TO_GEN_JSON):
        """
        Initialize the table generator with file paths.
        """
        self.input_folder = input_folder
        self.semantics_file = semantics_file
        self.table_templates_file = table_templates_file
        self.output_file = output_file
        
        # These will hold the loaded data.
        self.allSemanticAttributes = None
        self.tablePatterns = None
        self.replica = None
        
        # This list will contain all generated table dictionaries.
        self.generated_tables = []
        
        # Set random seed to mimic the R code’s reproducibility.
        random.seed(1)

    def get_filepath(self, filename):
        """
        Returns the full filepath for a given filename located in the input folder.
        """
        return os.path.join(self.input_folder, filename)

    # 1. Reading JSON Files
    
    def load_data(self):
        """
        Loads semantic attributes and table template data from JSON files.
        """
        with open(self.get_filepath(self.semantics_file), 'r') as f:
            self.allSemanticAttributes = json.load(f)
        
        with open(self.get_filepath(self.table_templates_file), 'r') as f:
            self.tablePatterns = json.load(f)
        
        # Retrieve the 'replica' attribute if it is specified.
        self.replica = self.tablePatterns.get("replica")

    # 2. Generating Parameter Combinations
    
    def generate_param_combinations(self):
        """
        Build all parameter combinations in R’s order (first list fastest).
        Returns a list of tuples in the form
          (shuffle, col_row_name_pos, col_row_agg_pos, col_row_levels, row_format)
        """
        combos = {
            "shuffle":                self.tablePatterns.get("shuffle", []),
            "col_row_name_pos":       self.tablePatterns.get("col_row_name_pos", []),
            "col_row_agg_pos":        self.tablePatterns.get("col_row_agg_pos", []),
            "col_row_levels":         self.tablePatterns.get("col_row_levels", []),
            "row_format":             self.tablePatterns.get("row_format", [])
        }

        # Reverse the order so that `shuffle` is the *first* argument to cycle fastest
        rev_lists = [
            combos["row_format"],
            combos["col_row_levels"],
            combos["col_row_agg_pos"],
            combos["col_row_name_pos"],
            combos["shuffle"],
        ]

        # itertools.product iterates the *last* list fastest, so reversed → R’s behavior
        raw = itertools.product(*rev_lists)

        # Un-reverse each tuple so it becomes (shuffle, col_row_name_pos, ...)
        param_combinations = [
            (shuffle, col_row_name_pos, col_row_agg_pos, col_row_levels, row_format)
            for row_format, col_row_levels, col_row_agg_pos, col_row_name_pos, shuffle
            in raw
        ]

        return param_combinations


    # 3. Creating Table Instances
    
    def generate_tables(self):
        """
        Iterates over each table template and each parameter combination and 
        generates a detailed table dictionary which is appended to self.generated_tables.
        """
        param_combi = self.generate_param_combinations()
        table_templates = self.tablePatterns.get("tables", [])
        table_count = 0

        for tbl_index, curTable in enumerate(table_templates, start=1):
            # Extract shared table parameters.
            sval = curTable.get("values")
            if isinstance(sval, list):
                if len(sval) == 1:
                    values_type = sval[0]
                else:
                    values_type = sval  # Keep as list if it has more than one element.
            else:
                values_type = sval

            valueName = curTable.get("valueName", "table")
            rowCodes = curTable.get("rowCodes", [])
            rowSamples = curTable.get("rowSamples", [])
            colCodes = curTable.get("colCodes", [])
            colSamples = curTable.get("colSamples", [])
            agg_name1 = curTable.get("agg_name1")
            agg_fun1 = curTable.get("agg_fun1")

            # Loop over each parameter combination.
            for combi_index, (shuffle, col_row_name_pos, col_row_agg_pos, col_row_levels, row_format) in enumerate(param_combi, start=1):
                print(f"{tbl_index}/{len(table_templates)} -- {combi_index}/{len(param_combi)}")

                # Process the "col_row_levels", expected format: "colLevels_rowLevels" (e.g., "2_3").
                try:
                    col_levels_str, row_levels_str = col_row_levels.split("_")
                    col_levels = int(col_levels_str)
                    row_levels = int(row_levels_str)
                except Exception as e:
                    print(f"Error processing 'col_row_levels' with value {col_row_levels}: {e}")
                    continue

                # Process "col_row_name_pos", expected format: "colNamePos_rowNamePos"
                try:
                    col_name_pos, row_name_pos = col_row_name_pos.split("_")
                except Exception as e:
                    print(f"Error processing 'col_row_name_pos' with value {col_row_name_pos}: {e}")
                    continue

                # Process "col_row_agg_pos", expected format: "colAggPos_rowAggPos"
                try:
                    col_agg_pos, row_agg_pos = col_row_agg_pos.split("_")
                except Exception as e:
                    print(f"Error processing 'col_row_agg_pos' with value {col_row_agg_pos}: {e}")
                    continue

                # Skip generation if row_format is "new" and row_agg_pos equals "top".
                if row_format == "new" and row_agg_pos == "top":
                    print("NOT GENERATED")
                    continue

                # Create a table name by replacing spaces with underscores.
                tabName = valueName.replace(" ", "_")
                tableName = f"{tabName}_set{combi_index}"

                # Build column attributes.
                colAttribs = []
                nColCodes = min(col_levels, len(colCodes))
                for i in range(nColCodes):
                    sample = colSamples[i] if i < len(colSamples) else []
                    if not isinstance(sample, list) or len(sample) != 2:
                        sample_value = [0]
                    else:
                        sample_value = sample

                    colAttribs.append({
                        "code": colCodes[i],
                        "pos": col_name_pos,
                        "sample": sample_value,
                        "agg_pos1": col_agg_pos
                    })

                # Build row attributes.
                rowAttribs = []
                nRowCodes = min(row_levels, len(rowCodes))
                for i in range(nRowCodes):
                    sample = rowSamples[i] if i < len(rowSamples) else []
                    if not isinstance(sample, list) or len(sample) != 2:
                        sample_value = [0]
                    else:
                        sample_value = sample

                    rowAttribs.append({
                        "code": rowCodes[i],
                        "pos": row_name_pos,
                        "sample": sample_value,
                        "agg_pos1": row_agg_pos
                    })

                # Build the table dictionary.
                newTable = {
                    "name": tableName,
                    "replica": self.replica,
                    "shuffle": shuffle,
                    "agg_fun1": agg_fun1,
                    "agg_name1": agg_name1,
                    "values": values_type,
                    "valueName": valueName,
                    "row_format": row_format,
                    "columns": {
                        "groups": [{
                            "attributes": colAttribs
                        }]
                    },
                    "rows": {
                        "groups": [{
                            "attributes": rowAttribs
                        }]
                    }
                }

                self.generated_tables.append(newTable)
                table_count += 1
        
        print("NUMBER OF TABLES:")
        print(table_count)

    # 4. Writing Output
    
    def write_output(self):
        output_path = self.get_filepath(self.output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                self.generated_tables,
                f,
                indent=4,         # <-- 4 spaces per level
                separators=(', ', ': '),  # <-- default spacing
                ensure_ascii=False
            )
        print(f"Output written to {output_path}")


    def run(self):
        """
        Runs the full process: loading data, generating tables, and writing the output.
        """
        self.load_data()
        self.generate_tables()
        self.write_output()


# Test Execution Flow
if __name__ == "__main__":
    generator = TableGenerator()
    generator.run()
