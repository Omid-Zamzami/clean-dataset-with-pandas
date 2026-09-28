from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pandas as pd
import pytest

from src.cleaner import (
    clean_data_types,
    clean_missing_values,
    clean_text_and_columns,
    cleaner,
    load_data,
    parse_argument,
    remove_duplicate_rows,
    save_data,
)


@pytest.fixture
def sample_raw_dataframe() -> pd.DataFrame:
    """
    Fixture providing a representative messy DataFrame covering
    duplicates, null values, malformed data types, and combined columns.
    """
    return pd.DataFrame(
        {
            "Employee_ID": ["EMP1001", "EMP1001", "EMP1002", None],
            "First_Name": ["John", "John", "Jane", "Alice"],
            "Last_Name": ["Doe", "Doe", "Smith", "Brown"],
            "Age": [30.0, 30.0, np.nan, 25.0],
            "Department_Region": ["Tech-West", "Tech-West", "HR-East", "Sales-North"],
            "Status": ["Active", "Active", "Pending", "Active"],
            "Join_Date": ["2022-01-15", "2022-01-15", "invalid_date", "2021-05-10"],
            "Salary": [70000.0, 70000.0, 90000.0, np.nan],
            "Email": [
                " John.Doe@Example.com ",
                " John.Doe@Example.com ",
                "JANE@DOMAIN.COM",
                "alice@example.com",
            ],
            "Phone": ["-987654321", "-987654321", 1234567890.0, np.nan],
            "Performance_Score": ["Good", "Good", None, "Average"],
            "Remote_Work": [True, True, False, True],
        }
    )


# CLI Argument Parsing Tests

def test_parse_argument_valid_input() -> None:
    """Verify CLI accepts the short and long flags for file name."""
    args_short = parse_argument(["-f", "sample_dataset.csv"])
    assert args_short.file == "sample_dataset.csv"

    args_long = parse_argument(["--file", "employees.xlsx"])
    assert args_long.file == "employees.xlsx"


def test_parse_argument_missing_required_file() -> None:
    """Verify parser raises SystemExit when required argument is missing."""
    with pytest.raises(SystemExit):
        parse_argument([])


# File Loading Tests

def test_load_data_csv_success(tmp_path: Path) -> None:
    """Verify CSV file loading."""
    csv_file: Path = tmp_path / "test_data.csv"
    pd.DataFrame({"id": [1, 2], "val": ["A", "B"]}).to_csv(csv_file, index=False)

    df: pd.DataFrame = load_data(csv_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_load_data_json_success(tmp_path: Path) -> None:
    """Verify JSON file loading."""
    json_file: Path = tmp_path / "test_data.json"
    pd.DataFrame({"id": [1, 2], "val": ["A", "B"]}).to_json(
        json_file, orient="records"
    )

    df: pd.DataFrame = load_data(json_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2


def test_load_data_excel_success(tmp_path: Path) -> None:
    """Verify Excel file loading by mocking pandas read_excel."""
    fake_excel: Path = tmp_path / "test_data.xlsx"
    fake_excel.touch()  # Create empty file so path.exists() passes

    with patch("src.cleaner.pd.read_excel") as mock_read_excel:
        mock_read_excel.return_value = pd.DataFrame({"id": [1]})
        df: pd.DataFrame = load_data(fake_excel)
        mock_read_excel.assert_called_once_with(fake_excel)
        assert len(df) == 1


def test_load_data_file_not_found(tmp_path: Path) -> None:
    """Verify FileNotFoundError is raised when file does not exist."""
    non_existent_file: Path = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError, match="not found"):
        load_data(non_existent_file)


def test_load_data_unsupported_format(tmp_path: Path) -> None:
    """Verify ValueError is raised for unsupported file formats."""
    unsupported_file: Path = tmp_path / "data.txt"
    unsupported_file.touch()

    with pytest.raises(ValueError, match="is not supported"):
        load_data(unsupported_file)


# Cleaning Pipeline Functions Tests

def test_remove_duplicate_rows(sample_raw_dataframe: pd.DataFrame) -> None:
    """Verify exact duplicate rows are eliminated."""
    initial_count: int = len(sample_raw_dataframe)
    cleaned_df: pd.DataFrame = remove_duplicate_rows(sample_raw_dataframe)

    assert len(cleaned_df) == initial_count - 1


def test_clean_missing_values(sample_raw_dataframe: pd.DataFrame) -> None:
    """
    Verify:
    1. Rows without Employee_ID are removed.
    2. Age and Salary missing values are imputed with median.
    3. Categorical missing values are filled with 'Unknown'.
    4. Excluded columns are not filled with 'Unknown'.
    """
    df: pd.DataFrame = remove_duplicate_rows(sample_raw_dataframe)
    df = clean_missing_values(df)

    # 1. Null Employee_ID dropped (row 3 was None)
    assert df["Employee_ID"].isnull().sum() == 0
    assert len(df) == 2

    # 2. Age median imputed (original valid age was 30.0)
    assert df["Age"].isnull().sum() == 0
    assert (df["Age"] == 30.0).all()

    # 3. Categorical missing filled with 'Unknown'
    assert df["Performance_Score"].iloc[1] == "Unknown"

    # 4. Join_Date and Phone were excluded from 'Unknown' replacement
    assert "Unknown" not in df["Join_Date"].values


def test_clean_data_types(sample_raw_dataframe: pd.DataFrame) -> None:
    """
    Verify:
    1. Join_Date is converted to datetime, invalid entries coerced to NaT.
    2. Age is cast to nullable integer 'Int64'.
    3. Phone trailing float suffixes (.0) and 'nan' representations are removed.
    """
    df: pd.DataFrame = remove_duplicate_rows(sample_raw_dataframe)
    df = clean_missing_values(df)
    df = clean_data_types(df)

    # 1. Datetime conversion
    assert pd.api.types.is_datetime64_any_dtype(df["Join_Date"])
    assert pd.isna(df["Join_Date"].iloc[1])  # 'invalid_date' converted to NaT

    # 2. Int64 nullable integer
    assert str(df["Age"].dtype) == "Int64"

    # 3. Phone float cleanup (1234567890.0 -> '1234567890')
    assert df["Phone"].iloc[1] == "1234567890"


def test_clean_text_and_columns(sample_raw_dataframe: pd.DataFrame) -> None:
    """
    Verify:
    1. Phone leading hyphens are stripped and zero-padded to 10 digits.
    2. Emails are stripped of whitespace and lowercased.
    3. Department_Region is split into Department and Region, then dropped.
    4. Preferred columns order is enforced.
    """
    df: pd.DataFrame = remove_duplicate_rows(sample_raw_dataframe)
    df = clean_missing_values(df)
    df = clean_data_types(df)
    df = clean_text_and_columns(df)

    # 1. Phone padding and hyphen removal ('-987654321' -> '0987654321')
    assert df["Phone"].iloc[0] == "0987654321"

    # 2. Email normalization
    assert df["Email"].iloc[0] == "john.doe@example.com"
    assert df["Email"].iloc[1] == "jane@domain.com"

    # 3. Column splitting
    assert "Department_Region" not in df.columns
    assert "Department" in df.columns
    assert "Region" in df.columns
    assert df["Department"].iloc[0] == "Tech"
    assert df["Region"].iloc[0] == "West"

    # 4. Column ordering (Employee_ID first)
    assert df.columns[0] == "Employee_ID"
    assert "Department" in df.columns[:6]


# File Export Tests

def test_save_data_csv(tmp_path: Path) -> None:
    """Verify DataFrame is saved to CSV without index column."""
    df = pd.DataFrame({"id": ["EMP1"], "name": ["John"]})
    output_path: Path = tmp_path / "cleaned_output.csv"

    save_data(df, output_path)

    assert output_path.exists()
    reloaded_df = pd.read_csv(output_path)
    # Ensure no index column such as 'Unnamed: 0' was written
    assert list(reloaded_df.columns) == ["id", "name"]


def test_save_data_json(tmp_path: Path) -> None:
    """Verify DataFrame is saved to JSON in records format."""
    df = pd.DataFrame({"id": ["EMP1"], "name": ["John"]})
    output_path: Path = tmp_path / "cleaned_output.json"

    save_data(df, output_path)

    assert output_path.exists()
    reloaded_df = pd.read_json(output_path)
    assert list(reloaded_df.columns) == ["id", "name"]


# End-to-End CLI Pipeline Integration Test

@patch("src.cleaner.parse_argument")
@patch("src.cleaner.load_data")
@patch("src.cleaner.save_data")
def test_cleaner_pipeline_orchestration(
    mock_save_data: MagicMock,
    mock_load_data: MagicMock,
    mock_parse_argument: MagicMock,
    sample_raw_dataframe: pd.DataFrame,
) -> None:
    """
    Test full execution of the cleaner() entry point by mocking I/O operations.
    """
    mock_parse_argument.return_value = MagicMock(file="Messy_Employee_dataset.csv")
    mock_load_data.return_value = sample_raw_dataframe

    # Execute main CLI orchestrator
    cleaner()

    mock_load_data.assert_called_once()
    mock_save_data.assert_called_once()

    # Inspect cleaned DataFrame passed to save_data
    saved_df: pd.DataFrame = mock_save_data.call_args[1]["df"]
    assert "Department_Region" not in saved_df.columns
    assert "Department" in saved_df.columns
    assert saved_df["Employee_ID"].isnull().sum() == 0