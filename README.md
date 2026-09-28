# Clean Dataset with Pandas

A Python command-line data-cleaning tool for transforming messy employee datasets into cleaner, more consistent, and analysis-ready data.

The project combines an exploratory Jupyter Notebook with a reusable cleaning pipeline implemented in Python. It uses **Pandas** for data processing and **pytest** for automated testing.

## Features

- Load datasets from:
  - CSV
  - Excel (`.xlsx`, `.xls`)
  - JSON
- Remove exact duplicate rows
- Remove records without a reliable `Employee_ID`
- Handle missing numerical values using column medians
- Fill missing categorical/text values with `Unknown`
- Convert dates to Pandas datetime values
- Convert `Age` to a nullable integer type
- Normalize phone-number values stored as numeric or string data
- Remove unwanted leading hyphens from phone numbers
- Zero-pad phone numbers to 10 digits
- Normalize email addresses by trimming whitespace and converting them to lowercase
- Split the combined `Department_Region` column into separate `Department` and `Region` columns
- Reorder known columns into a consistent schema while preserving additional columns
- Export cleaned data in CSV, Excel, or JSON format
- Provide automated unit and integration tests with pytest
- Separate data exploration from the reusable cleaning pipeline

## Project Structure

```text
clean-dataset-with-pandas/
│
├── data/
│   └── Messy_Employee_dataset.csv
│
├── src/
│   └── cleaner.py
│
├── tests/
│   └── test_cleaner.py
│
├── notebooks/
│   └── clean_data.ipynb
│
├── .gitignore
├── LICENSE
├── pytest.ini
├── requirements.txt
└── README.md
```


## How the Cleaning Pipeline Works

The command-line pipeline applies the following operations in order:

1. **Load the dataset**
2. **Remove duplicate rows**
3. **Handle missing values**
4. **Convert data types**
5. **Clean and normalize text-based fields**
6. **Split combined columns**
7. **Save the cleaned dataset**

This order allows the data to be progressively transformed from a raw dataset into a more consistent structure.

### Missing Values

The cleaning strategy depends on the column:

- Rows without `Employee_ID` are removed because the employee cannot be reliably identified.
- Missing `Age` values are replaced with the median age.
- Missing `Salary` values are replaced with the median salary.
- Other text/categorical columns are filled with `Unknown`.
- `Join_Date` and `Phone` are handled separately during type conversion and normalization.

### Data Type Conversion

The pipeline converts:

- `Join_Date` → `datetime`
- `Age` → Pandas nullable integer (`Int64`)
- `Phone` → normalized string representation

Invalid date values are converted to `NaT` instead of causing the entire cleaning process to fail.

### Text and Column Cleaning

The pipeline also:

- Strips whitespace and lowercases email addresses.
- Removes leading hyphens from phone numbers.
- Pads shorter phone numbers with leading zeros to produce 10-digit values.
- Splits values such as `Tech-West` into:
  - `Department = Tech`
  - `Region = West`
- Removes the original `Department_Region` column.
- Applies a preferred column order to the cleaned dataset.

## Installation

Clone the repository:

```bash
git clone https://github.com/Omid-Zamzami/clean-dataset-with-pandas.git
cd clean-dataset-with-pandas
```

Create and activate a virtual environment:

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Place the input dataset inside the `data/` directory.

For example:

```text
data/
└── Messy_Employee_dataset.csv
```

Run the cleaner with the required `--file` argument:

```bash
python src/cleaner.py --file Messy_Employee_dataset.csv
```

The short option is also supported:

```bash
python src/cleaner.py -f Messy_Employee_dataset.csv
```

The cleaned file is written to the same `data/` directory with a `cleaned_` prefix:

```text
data/
├── Messy_Employee_dataset.csv
└── cleaned_Messy_Employee_dataset.csv
```

### Supported Input Formats

| Format | Extension | Read | Write |
|---|---|---:|---:|
| CSV | `.csv` | Yes | Yes |
| Excel | `.xlsx` | Yes | Yes |
| Excel | `.xls` | Yes | Yes |
| JSON | `.json` | Yes | Yes |

For Excel support, the project includes both `openpyxl` and `xlrd` because Pandas uses different engines depending on the Excel format.

## Example Transformation

A messy record may contain values such as:

```text
Email:             " John.Doe@Example.com "
Phone:             "-987654321"
Department_Region: "Tech-West"
Age:               missing
```

After cleaning, the corresponding values become:

```text
Email:      john.doe@example.com
Phone:      0987654321
Department: Tech
Region:     West
Age:        median age of the dataset
```

## Testing

The project includes automated tests for the main cleaning functions and the command-line pipeline.

Run the complete test suite:

```bash
pytest
```

The test suite covers:

### CLI argument parsing

- Valid short and long file arguments
- Missing required arguments

### File loading

- CSV loading
- JSON loading
- Excel loading
- Missing files
- Unsupported file formats

### Data cleaning

- Duplicate removal
- Missing-value handling
- Date conversion
- Numeric conversion
- Phone normalization
- Email normalization
- Splitting `Department_Region`
- Column ordering

### File export

- CSV output
- JSON output
- Prevention of an unwanted DataFrame index column

### Pipeline integration

The `cleaner()` entry point is also tested to verify that the major pipeline stages are orchestrated correctly while external I/O operations are mocked.

## Exploratory Analysis

The Jupyter Notebook (`clean_data.ipynb`) documents the exploratory data-cleaning process before the logic was organized into reusable functions.

The notebook includes:

- Initial dataset inspection
- Dataset shape and information
- Missing-value analysis
- Unique-value and frequency analysis
- Employee ID inspection
- Duplicate detection
- Age range inspection
- Date inspection and conversion
- Phone-number inspection and normalization
- Splitting `Department_Region`
- Final column ordering
- Exporting the cleaned dataset

This separation provides both an exploratory workflow for understanding the data and a reusable Python pipeline for repeatable execution.

## Technologies

- **Python**
- **Pandas**
- **NumPy**
- **pytest**
- **Jupyter Notebook**
- **openpyxl**
- **xlrd**

## Design Notes

The project is intentionally organized around small, focused functions rather than putting the entire cleaning process inside one large function.

The main responsibilities are separated into:

```text
parse_argument()
        ↓
load_data()
        ↓
remove_duplicate_rows()
        ↓
clean_missing_values()
        ↓
clean_data_types()
        ↓
clean_text_and_columns()
        ↓
save_data()
```

This structure makes individual cleaning operations easier to test, reuse, and modify independently.

The tests also use tools such as fixtures, temporary paths, mocking, and exception assertions to test both individual functions and pipeline orchestration.

## Requirements

The project currently targets a modern Python 3 environment.

Dependencies are listed in `requirements.txt`:

```text
pandas>=2.2.0
openpyxl>=3.1.0
xlrd>=2.0.1
pytest>=8.0.0
```

## License

This project is licensed under the MIT License.

See the [LICENSE](LICENSE) file for the full license text.

## Author

**Omid Zamzami**

GitHub: [Omid-Zamzami](https://github.com/Omid-Zamzami)

Repository: [clean-dataset-with-pandas](https://github.com/Omid-Zamzami/clean-dataset-with-pandas)
