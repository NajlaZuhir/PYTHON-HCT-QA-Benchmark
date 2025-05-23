#!/usr/bin/env python3
import os
import json
import pandas as pd

try:
    from config import BENCHMARK_FOLDER
except ImportError:
    BENCHMARK_FOLDER = "./benchmark"

class BenchmarkCounter:
    """
    Counts synthetic Q&A templates per table and set in the benchmark folder,
    then summarizes by base table name and prints a total.
    """

    def __init__(self, folder=BENCHMARK_FOLDER):
        self.folder = folder
        self.suffix = "_QandA.json"

    def list_qanda_files(self):
        """
        Returns all filenames ending with '_QandA.json' in the target folder.
        """
        return [f for f in os.listdir(self.folder) if f.endswith(self.suffix)]

    def parse_filename(self, fname):
        """
        Splits 'Evolution_of_pollution_set1_2_QandA.json' →
          baseTableName='Evolution_of_pollution'
          setNum='1_2'
        """
        root = fname[:-len(self.suffix)]
        base, set_num = root.split("_set", 1)
        return base, set_num

    def load_question_count(self, fname):
        """
        Opens the JSON file, returns the number of entries in 'questions'.
        """
        path = os.path.join(self.folder, fname)
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return len(data.get("questions", []))

    def build_dataframe(self):
        """
        Constructs a DataFrame with columns: baseTableName, setNum, numQuestions.
        """
        records = []
        for fname in self.list_qanda_files():
            base, set_num = self.parse_filename(fname)
            count = self.load_question_count(fname)
            records.append({
                "baseTableName": base,
                "setNum": set_num,
                "numQuestions": count
            })
        return pd.DataFrame(records)

    def summarize(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggregates by baseTableName, counting distinct sets and summing questions,
        then appends a 'Total' row.
        """
        summary = (
            df.groupby("baseTableName")
              .agg(NumTables=("setNum", "nunique"),
                   NumQuestions=("numQuestions", "sum"))
              .reset_index()
              .rename(columns={"baseTableName": "NameTables"})
        )
        total = pd.DataFrame([{
            "NameTables": "Total",
            "NumTables": summary["NumTables"].sum(),
            "NumQuestions": summary["NumQuestions"].sum()
        }])
        return pd.concat([summary, total], ignore_index=True)

    def run(self):
        """
        Executes the count → summarize → print sequence.
        """
        print(f"Scanning '{self.folder}' for Q&A JSON files...")
        df = self.build_dataframe()
        if df.empty:
            print("No Q&A files found.")
            return
        result = self.summarize(df)
        print("\nSynthetic Benchmark Summary:\n")
        # print without the pandas index
        print(result.to_string(index=False))


if __name__ == "__main__":
    BenchmarkCounter().run()
