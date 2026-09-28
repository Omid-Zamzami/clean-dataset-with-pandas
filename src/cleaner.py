import argparse
from pathlib import Path
import pandas as pd


# Root directory of the project.
BASE_DIR = Path(__file__).resolve().parent.parent


def parse_argument(arg: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments and return the parsed arguments."""
    parser = argparse.ArgumentParser(
        description="CLI tool for fetching messy dataset file name."
    )

    parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="File name of the messy dataset in need for cleaning"
    )

    return parser.parse_args(arg)


def load_data(file_path: Path) -> pd.DataFrame:
    """Load a dataset from a supported file format."""
    if not file_path.exists():
        raise FileNotFoundError(f"file in {file_path} was not found!")

    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(file_path)
    elif suffix in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    elif suffix == ".json":
        return pd.read_json(file_path)
    else:
        raise ValueError(
            f"{suffix} is not supported. Allowed formats: csv, xlsx, json."
        )


def remove_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate rows from the dataset."""
    return df.drop_duplicates().copy()


def clean_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values according to each column's data type."""
    # Employee records without an Employee_ID cannot be reliably identified.
    df = df.dropna(subset=["Employee_ID"])

    # Replace missing numerical values with the median of each column.
    if "Age" in df.columns:
        age_median = df["Age"].median()
        df["Age"] = df["Age"].fillna(age_median)

    if "Salary" in df.columns:
        salary_median = df["Salary"].median()
        df["Salary"] = df["Salary"].fillna(salary_median)

    # Use "Unknown" for missing categorical/text values.
    excluded_columns = ["Employee_ID", "Age", "Salary", "Join_Date", "Phone"]

    for column in df.columns:
        if column not in excluded_columns:
            df[column] = df[column].fillna("Unknown")

    return df

def clean_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert columns to appropriate data types."""
    # Convert date values to datetime; invalid dates become NaT.
    if "Join_Date" in df.columns:
        df["Join_Date"] = pd.to_datetime(df["Join_Date"], errors="coerce")

    # Convert Age to numeric values and use Pandas' nullable integer type.
    if "Age" in df.columns:
        df["Age"] = pd.to_numeric(df["Age"], errors="coerce").round().astype("Int64")

    # Normalize phone numbers stored as numeric values.
    if "Phone" in df.columns:
        df["Phone"] = (
            df["Phone"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .replace("nan", "")
        )

    return df


def clean_text_and_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Clean text-based columns and split combined columns."""
    # Remove leading hyphens and pad phone numbers to 10 digits.
    if "Phone" in df.columns:
        df["Phone"] = df["Phone"].str.lstrip("-")
        df["Phone"] = df["Phone"].apply(lambda x: x.zfill(10) if x and x != "Unknown" else x)

    # Normalize email addresses by removing whitespace and converting to lowercase.
    if "Email" in df.columns:
        df["Email"] = df["Email"].astype(str).str.strip().str.lower()

    # Split the combined Department_Region column into separate columns.
    if "Department_Region" in df.columns:
        split_data = df["Department_Region"].astype(str).str.split("-", expand=True)
        df["Department"] = split_data[0].str.strip() if 0 in split_data.columns else "Unknown"
        df["Region"] = split_data[1].str.strip() if 1 in split_data.columns else "Unknown"
        df = df.drop(columns=["Department_Region"])
        
        # Define the preferred order for the cleaned dataset columns.
        preferred_order = [
            "Employee_ID", "First_Name", "Last_Name", "Age",
            "Department", "Region", "Status", "Join_Date",
            "Salary", "Email", "Phone", "Performance_Score", "Remote_Work"
        ]

        # Keep known columns in the preferred order and preserve any # additional columns after them.
        existing_ordered = [col for col in preferred_order if col in df.columns]
        remaining = [col for col in df.columns if col not in existing_ordered]
        df = df[existing_ordered + remaining]

    return df


def save_data(df: pd.DataFrame, cleaned_file_path: Path) -> None:
    """Save the cleaned dataset using the appropriate file format."""
    suffix = cleaned_file_path.suffix.lower()

    if suffix == ".csv":
        df.to_csv(cleaned_file_path, index=False)
    elif suffix in [".xlsx", ".xls"]:
        df.to_excel(cleaned_file_path, index=False)
    elif suffix == ".json":
        df.to_json(cleaned_file_path, orient="records", indent=4)


def cleaner() -> None:
    """Run the complete data-cleaning pipeline."""
    # Read the input file name from the command line.
    arg = parse_argument()

    # Build the path to the input dataset.
    file_path = BASE_DIR / "data" / f"{arg.file}"

    # Load and clean the dataset step by step.
    df = load_data(file_path=file_path)
    df = remove_duplicate_rows(df=df)
    df = clean_missing_values(df=df)
    df = clean_data_types(df=df)
    df = clean_text_and_columns(df=df)

    # Save the cleaned dataset with a "cleaned_" prefix.
    cleaned_file_path = BASE_DIR / "data" / f"cleaned_{arg.file}"

    save_data(df=df, cleaned_file_path=cleaned_file_path)


if __name__ == "__main__":
    cleaner()