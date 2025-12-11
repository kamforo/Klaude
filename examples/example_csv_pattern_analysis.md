# CSV Pattern Recognition - Example Usage

## Basic Usage

Analyze marketing data to find patterns with highest Revenue per Conversion:

```bash
python csv_pattern_workflow.py examples/sample_marketing_data.csv
```

## Specify Parameters to Analyze

Analyze specific columns (up to 4):

```bash
python csv_pattern_workflow.py examples/sample_marketing_data.csv \
    -p campaign channel device region
```

## Multi-Level Analysis

Find best patterns at each parameter depth (1-param, 2-param, 3-param, 4-param):

```bash
python csv_pattern_workflow.py examples/sample_marketing_data.csv \
    -p campaign channel device region \
    --multi-level
```

## Custom Column Names

Specify revenue and CV column names:

```bash
python csv_pattern_workflow.py data.csv \
    -r "total_sales" \
    -c "conversions" \
    -p source medium
```

## Filter by Minimum Conversions

Only show patterns with at least 100 conversions:

```bash
python csv_pattern_workflow.py examples/sample_marketing_data.csv \
    -p campaign channel \
    --min-cv 100
```

## Show More Results

Display top/bottom 20 patterns:

```bash
python csv_pattern_workflow.py examples/sample_marketing_data.csv \
    -p channel device \
    --top-n 20
```

---

## Expected Output

The workflow produces:
1. **Overview** - Total rows, revenue, CV, and overall Revenue/CV
2. **Top Patterns** - Highest Revenue/CV patterns ranked
3. **Bottom Patterns** - Lowest Revenue/CV patterns for optimization

### Sample Insights

From `sample_marketing_data.csv`:
- **Best single parameter**: `channel=Google` typically shows highest Revenue/CV
- **Best 2-param combo**: `channel=Google + region=US`
- **Best 3-param combo**: `campaign=Winter Promo + channel=Google + device=Desktop`
