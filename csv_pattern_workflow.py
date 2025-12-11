#!/usr/bin/env python3
"""
CSV Pattern Recognition Workflow
Analyzes CSV data to find patterns with highest Revenue per CV (Conversion)

This workflow:
1. Loads a CSV file
2. Allows selection of up to 4 parameters for pattern analysis
3. Finds all value combinations across selected parameters
4. Calculates Revenue/CV ratio for each pattern
5. Ranks and reports top performing patterns
"""

import csv
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from itertools import combinations
from collections import defaultdict
import argparse


@dataclass
class CSVData:
    """Represents loaded CSV data with headers and rows"""
    headers: List[str]
    rows: List[Dict[str, str]]
    revenue_column: str = ""
    cv_column: str = ""

    def get_numeric_columns(self) -> List[str]:
        """Identify columns that contain numeric data"""
        numeric_cols = []
        for header in self.headers:
            try:
                # Check first few non-empty values
                values = [row[header] for row in self.rows[:10] if row.get(header)]
                if values and all(self._is_numeric(v) for v in values):
                    numeric_cols.append(header)
            except (ValueError, KeyError):
                continue
        return numeric_cols

    def get_categorical_columns(self) -> List[str]:
        """Identify columns suitable for pattern recognition (categorical)"""
        numeric_cols = self.get_numeric_columns()
        categorical = []
        for header in self.headers:
            if header not in numeric_cols:
                # Check if column has reasonable number of unique values
                unique_values = set(row.get(header, "") for row in self.rows)
                if 1 < len(unique_values) <= 50:  # Not too few, not too many
                    categorical.append(header)
        return categorical

    @staticmethod
    def _is_numeric(value: str) -> bool:
        """Check if a string value is numeric"""
        try:
            cleaned = value.replace(",", "").replace("$", "").replace("%", "").strip()
            if cleaned:
                float(cleaned)
            return True
        except ValueError:
            return False


@dataclass
class Pattern:
    """Represents a discovered pattern with its metrics"""
    parameters: Dict[str, str]  # Parameter name -> value
    total_revenue: float = 0.0
    total_cv: int = 0
    row_count: int = 0
    revenue_per_cv: float = 0.0

    def calculate_metrics(self):
        """Calculate revenue per CV ratio"""
        if self.total_cv > 0:
            self.revenue_per_cv = self.total_revenue / self.total_cv
        else:
            self.revenue_per_cv = 0.0

    def pattern_key(self) -> str:
        """Generate a unique key for this pattern"""
        return " | ".join(f"{k}={v}" for k, v in sorted(self.parameters.items()))

    def __str__(self) -> str:
        return self.pattern_key()


@dataclass
class AnalysisResult:
    """Contains the full analysis results"""
    patterns: List[Pattern] = field(default_factory=list)
    parameters_analyzed: List[str] = field(default_factory=list)
    total_rows: int = 0
    total_revenue: float = 0.0
    total_cv: int = 0

    def get_top_patterns(self, n: int = 10, min_cv: int = 1) -> List[Pattern]:
        """Get top N patterns by revenue per CV, with minimum CV threshold"""
        filtered = [p for p in self.patterns if p.total_cv >= min_cv]
        return sorted(filtered, key=lambda p: p.revenue_per_cv, reverse=True)[:n]

    def get_bottom_patterns(self, n: int = 10, min_cv: int = 1) -> List[Pattern]:
        """Get bottom N patterns by revenue per CV"""
        filtered = [p for p in self.patterns if p.total_cv >= min_cv]
        return sorted(filtered, key=lambda p: p.revenue_per_cv)[:n]


class CSVLoader:
    """Handles CSV file loading and validation"""

    REVENUE_ALIASES = ["revenue", "rev", "income", "sales", "amount", "total_revenue", "gross"]
    CV_ALIASES = ["cv", "conversion", "conversions", "conv", "converts", "sales_count", "orders"]

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data: Optional[CSVData] = None

    def load(self) -> CSVData:
        """Load and parse CSV file"""
        rows = []
        headers = []

        try:
            with open(self.filepath, 'r', encoding='utf-8-sig') as f:
                # Try to detect delimiter
                sample = f.read(4096)
                f.seek(0)

                # Detect delimiter
                delimiter = ','
                if '\t' in sample and sample.count('\t') > sample.count(','):
                    delimiter = '\t'
                elif ';' in sample and sample.count(';') > sample.count(','):
                    delimiter = ';'

                reader = csv.DictReader(f, delimiter=delimiter)
                headers = reader.fieldnames or []

                for row in reader:
                    rows.append(row)

        except FileNotFoundError:
            raise ValueError(f"File not found: {self.filepath}")
        except Exception as e:
            raise ValueError(f"Error reading CSV: {e}")

        if not headers:
            raise ValueError("CSV file has no headers")
        if not rows:
            raise ValueError("CSV file has no data rows")

        self.data = CSVData(headers=list(headers), rows=rows)
        self._detect_revenue_cv_columns()

        return self.data

    def _detect_revenue_cv_columns(self):
        """Auto-detect revenue and CV columns"""
        if not self.data:
            return

        headers_lower = {h.lower(): h for h in self.data.headers}

        # Detect revenue column
        for alias in self.REVENUE_ALIASES:
            for header_lower, header in headers_lower.items():
                if alias in header_lower:
                    self.data.revenue_column = header
                    break
            if self.data.revenue_column:
                break

        # Detect CV column
        for alias in self.CV_ALIASES:
            for header_lower, header in headers_lower.items():
                if alias in header_lower:
                    self.data.cv_column = header
                    break
            if self.data.cv_column:
                break

    def validate_columns(self, revenue_col: str = None, cv_col: str = None) -> Tuple[bool, str]:
        """Validate that required columns exist"""
        if not self.data:
            return False, "No data loaded"

        if revenue_col:
            self.data.revenue_column = revenue_col
        if cv_col:
            self.data.cv_column = cv_col

        if not self.data.revenue_column:
            return False, f"Revenue column not found. Available: {', '.join(self.data.headers)}"
        if not self.data.cv_column:
            return False, f"CV column not found. Available: {', '.join(self.data.headers)}"

        if self.data.revenue_column not in self.data.headers:
            return False, f"Revenue column '{self.data.revenue_column}' not in CSV headers"
        if self.data.cv_column not in self.data.headers:
            return False, f"CV column '{self.data.cv_column}' not in CSV headers"

        return True, "Validation successful"


class PatternRecognitionEngine:
    """Core pattern recognition logic"""

    def __init__(self, data: CSVData):
        self.data = data

    def analyze(self, parameters: List[str], min_cv: int = 1) -> AnalysisResult:
        """
        Analyze patterns across selected parameters

        Args:
            parameters: List of column names to analyze (max 4)
            min_cv: Minimum CV threshold for pattern inclusion

        Returns:
            AnalysisResult containing all discovered patterns
        """
        if len(parameters) > 4:
            raise ValueError("Maximum 4 parameters allowed for analysis")

        if not parameters:
            raise ValueError("At least 1 parameter required for analysis")

        # Validate parameters exist in data
        for param in parameters:
            if param not in self.data.headers:
                raise ValueError(f"Parameter '{param}' not found in CSV headers")

        # Group rows by pattern
        pattern_groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)

        for row in self.data.rows:
            # Create pattern key from selected parameters
            pattern_values = {param: row.get(param, "").strip() for param in parameters}
            pattern_key = "|".join(f"{k}:{v}" for k, v in sorted(pattern_values.items()))
            pattern_groups[pattern_key].append(row)

        # Calculate metrics for each pattern
        patterns = []
        total_revenue = 0.0
        total_cv = 0

        for pattern_key, rows in pattern_groups.items():
            # Parse pattern values from key
            param_values = {}
            for part in pattern_key.split("|"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    param_values[k] = v

            pattern = Pattern(parameters=param_values)

            for row in rows:
                revenue = self._parse_numeric(row.get(self.data.revenue_column, "0"))
                cv = int(self._parse_numeric(row.get(self.data.cv_column, "0")))

                pattern.total_revenue += revenue
                pattern.total_cv += cv
                pattern.row_count += 1

                total_revenue += revenue
                total_cv += cv

            pattern.calculate_metrics()
            patterns.append(pattern)

        result = AnalysisResult(
            patterns=patterns,
            parameters_analyzed=parameters,
            total_rows=len(self.data.rows),
            total_revenue=total_revenue,
            total_cv=total_cv
        )

        return result

    def analyze_all_combinations(self, parameters: List[str], min_params: int = 1,
                                  max_params: int = 4) -> Dict[int, AnalysisResult]:
        """
        Analyze all combinations of parameters from min to max

        Returns dict mapping parameter count to AnalysisResult
        """
        results = {}

        for n in range(min_params, min(max_params + 1, len(parameters) + 1)):
            for combo in combinations(parameters, n):
                combo_key = len(combo)
                if combo_key not in results:
                    results[combo_key] = []

                result = self.analyze(list(combo))
                results[combo_key].append((combo, result))

        return results

    @staticmethod
    def _parse_numeric(value: str) -> float:
        """Parse a string value to float, handling currency symbols"""
        if not value:
            return 0.0
        cleaned = value.replace(",", "").replace("$", "").replace("%", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0


class ReportGenerator:
    """Generates analysis reports"""

    def __init__(self, result: AnalysisResult, data: CSVData):
        self.result = result
        self.data = data

    def generate_summary(self) -> str:
        """Generate a summary report"""
        lines = [
            "=" * 70,
            "CSV PATTERN RECOGNITION ANALYSIS REPORT",
            "=" * 70,
            "",
            "OVERVIEW",
            "-" * 40,
            f"Total Rows Analyzed: {self.result.total_rows:,}",
            f"Total Revenue: ${self.result.total_revenue:,.2f}",
            f"Total Conversions (CV): {self.result.total_cv:,}",
            f"Overall Revenue/CV: ${self.result.total_revenue / max(self.result.total_cv, 1):,.2f}",
            "",
            f"Parameters Analyzed: {', '.join(self.result.parameters_analyzed)}",
            f"Unique Patterns Found: {len(self.result.patterns):,}",
            "",
        ]

        return "\n".join(lines)

    def generate_top_patterns_report(self, n: int = 10, min_cv: int = 1) -> str:
        """Generate report of top performing patterns"""
        top_patterns = self.result.get_top_patterns(n, min_cv)

        lines = [
            f"TOP {n} PATTERNS BY REVENUE/CV (min {min_cv} CV)",
            "-" * 70,
            ""
        ]

        if not top_patterns:
            lines.append("No patterns found meeting the minimum CV threshold.")
            return "\n".join(lines)

        for i, pattern in enumerate(top_patterns, 1):
            lines.extend([
                f"#{i} Revenue/CV: ${pattern.revenue_per_cv:,.2f}",
                f"   Pattern: {pattern.pattern_key()}",
                f"   Total Revenue: ${pattern.total_revenue:,.2f} | Total CV: {pattern.total_cv:,} | Rows: {pattern.row_count:,}",
                ""
            ])

        return "\n".join(lines)

    def generate_bottom_patterns_report(self, n: int = 10, min_cv: int = 1) -> str:
        """Generate report of worst performing patterns"""
        bottom_patterns = self.result.get_bottom_patterns(n, min_cv)

        lines = [
            f"BOTTOM {n} PATTERNS BY REVENUE/CV (min {min_cv} CV)",
            "-" * 70,
            ""
        ]

        if not bottom_patterns:
            lines.append("No patterns found meeting the minimum CV threshold.")
            return "\n".join(lines)

        for i, pattern in enumerate(bottom_patterns, 1):
            lines.extend([
                f"#{i} Revenue/CV: ${pattern.revenue_per_cv:,.2f}",
                f"   Pattern: {pattern.pattern_key()}",
                f"   Total Revenue: ${pattern.total_revenue:,.2f} | Total CV: {pattern.total_cv:,} | Rows: {pattern.row_count:,}",
                ""
            ])

        return "\n".join(lines)

    def generate_full_report(self, top_n: int = 10, min_cv: int = 1) -> str:
        """Generate complete analysis report"""
        sections = [
            self.generate_summary(),
            self.generate_top_patterns_report(top_n, min_cv),
            self.generate_bottom_patterns_report(top_n, min_cv),
            "=" * 70,
            "END OF REPORT",
            "=" * 70
        ]

        return "\n".join(sections)


class PatternWorkflowEngine:
    """Main workflow orchestrator"""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.loader: Optional[CSVLoader] = None
        self.data: Optional[CSVData] = None
        self.engine: Optional[PatternRecognitionEngine] = None

    def run(self, parameters: List[str] = None,
            revenue_col: str = None,
            cv_col: str = None,
            top_n: int = 10,
            min_cv: int = 1,
            interactive: bool = False) -> str:
        """
        Run the complete pattern recognition workflow

        Args:
            parameters: List of parameters to analyze (will prompt if None and interactive)
            revenue_col: Revenue column name (auto-detected if None)
            cv_col: CV column name (auto-detected if None)
            top_n: Number of top/bottom patterns to show
            min_cv: Minimum CV threshold for pattern inclusion
            interactive: Whether to run in interactive mode

        Returns:
            Full analysis report as string
        """
        output_lines = []

        # Step 1: Load CSV
        output_lines.append("\n[Step 1/5] Loading CSV file...")
        self.loader = CSVLoader(self.filepath)
        self.data = self.loader.load()
        output_lines.append(f"  Loaded {len(self.data.rows):,} rows with {len(self.data.headers)} columns")
        output_lines.append(f"  Columns: {', '.join(self.data.headers)}")

        # Step 2: Validate columns
        output_lines.append("\n[Step 2/5] Validating revenue and CV columns...")
        valid, message = self.loader.validate_columns(revenue_col, cv_col)

        if not valid:
            if interactive:
                output_lines.append(f"  {message}")
                # In interactive mode, would prompt for columns
                raise ValueError(message)
            else:
                raise ValueError(message)

        output_lines.append(f"  Revenue column: {self.data.revenue_column}")
        output_lines.append(f"  CV column: {self.data.cv_column}")

        # Step 3: Identify analyzable parameters
        output_lines.append("\n[Step 3/5] Identifying categorical parameters...")
        categorical = self.data.get_categorical_columns()
        # Exclude revenue and CV columns from categorical
        categorical = [c for c in categorical
                      if c != self.data.revenue_column and c != self.data.cv_column]
        output_lines.append(f"  Found {len(categorical)} categorical columns: {', '.join(categorical)}")

        # Step 4: Select parameters
        output_lines.append("\n[Step 4/5] Selecting parameters for analysis...")

        if parameters:
            # Validate provided parameters
            for p in parameters:
                if p not in self.data.headers:
                    raise ValueError(f"Parameter '{p}' not found in CSV. Available: {', '.join(self.data.headers)}")
            selected_params = parameters[:4]  # Max 4
        elif interactive:
            # Would prompt user to select parameters
            selected_params = categorical[:4]
        else:
            # Auto-select up to 4 categorical columns
            selected_params = categorical[:4]

        if not selected_params:
            raise ValueError("No parameters available for analysis")

        output_lines.append(f"  Analyzing {len(selected_params)} parameters: {', '.join(selected_params)}")

        # Step 5: Run pattern recognition
        output_lines.append("\n[Step 5/5] Running pattern recognition...")
        self.engine = PatternRecognitionEngine(self.data)
        result = self.engine.analyze(selected_params, min_cv)
        output_lines.append(f"  Found {len(result.patterns):,} unique patterns")

        # Generate report
        output_lines.append("\n")
        reporter = ReportGenerator(result, self.data)
        report = reporter.generate_full_report(top_n, min_cv)
        output_lines.append(report)

        return "\n".join(output_lines)

    def run_multi_level_analysis(self, parameters: List[str],
                                  revenue_col: str = None,
                                  cv_col: str = None,
                                  top_n: int = 5,
                                  min_cv: int = 1) -> str:
        """
        Run analysis at multiple parameter combination levels

        Analyzes patterns with 1 param, 2 params, 3 params, etc.
        """
        output_lines = []

        # Load and validate
        self.loader = CSVLoader(self.filepath)
        self.data = self.loader.load()
        self.loader.validate_columns(revenue_col, cv_col)

        self.engine = PatternRecognitionEngine(self.data)

        output_lines.append("=" * 70)
        output_lines.append("MULTI-LEVEL PATTERN ANALYSIS")
        output_lines.append("=" * 70)
        output_lines.append(f"\nAnalyzing parameters: {', '.join(parameters)}")
        output_lines.append(f"File: {self.filepath}")
        output_lines.append(f"Rows: {len(self.data.rows):,}")

        # Analyze each level
        for n in range(1, min(len(parameters) + 1, 5)):
            output_lines.append(f"\n{'=' * 70}")
            output_lines.append(f"LEVEL {n}: {n}-PARAMETER COMBINATIONS")
            output_lines.append("=" * 70)

            best_combo = None
            best_pattern = None
            best_revenue_per_cv = 0

            for combo in combinations(parameters, n):
                result = self.engine.analyze(list(combo), min_cv)
                top = result.get_top_patterns(1, min_cv)

                if top and top[0].revenue_per_cv > best_revenue_per_cv:
                    best_combo = combo
                    best_pattern = top[0]
                    best_revenue_per_cv = top[0].revenue_per_cv

                # Show top patterns for this combination
                output_lines.append(f"\n  Combination: {' + '.join(combo)}")
                output_lines.append(f"  Patterns found: {len(result.patterns)}")

                top_patterns = result.get_top_patterns(top_n, min_cv)
                if top_patterns:
                    output_lines.append(f"  Top {min(top_n, len(top_patterns))} patterns:")
                    for i, p in enumerate(top_patterns, 1):
                        output_lines.append(f"    {i}. ${p.revenue_per_cv:,.2f}/CV - {p.pattern_key()} (CV: {p.total_cv})")

            if best_pattern:
                output_lines.append(f"\n  BEST AT LEVEL {n}:")
                output_lines.append(f"  Parameters: {' + '.join(best_combo)}")
                output_lines.append(f"  Pattern: {best_pattern.pattern_key()}")
                output_lines.append(f"  Revenue/CV: ${best_pattern.revenue_per_cv:,.2f}")

        output_lines.append("\n" + "=" * 70)
        output_lines.append("END OF MULTI-LEVEL ANALYSIS")
        output_lines.append("=" * 70)

        return "\n".join(output_lines)


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description="CSV Pattern Recognition - Find patterns with highest Revenue/CV"
    )
    parser.add_argument("csv_file", help="Path to CSV file to analyze")
    parser.add_argument(
        "-p", "--parameters",
        nargs="+",
        help="Parameters (columns) to analyze (max 4). Auto-detected if not specified."
    )
    parser.add_argument(
        "-r", "--revenue-column",
        help="Name of revenue column (auto-detected if not specified)"
    )
    parser.add_argument(
        "-c", "--cv-column",
        help="Name of CV/conversion column (auto-detected if not specified)"
    )
    parser.add_argument(
        "-n", "--top-n",
        type=int,
        default=10,
        help="Number of top/bottom patterns to show (default: 10)"
    )
    parser.add_argument(
        "-m", "--min-cv",
        type=int,
        default=1,
        help="Minimum CV threshold for pattern inclusion (default: 1)"
    )
    parser.add_argument(
        "--multi-level",
        action="store_true",
        help="Run multi-level analysis (1-param, 2-param, etc.)"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )

    args = parser.parse_args()

    try:
        engine = PatternWorkflowEngine(args.csv_file)

        if args.multi_level and args.parameters:
            result = engine.run_multi_level_analysis(
                parameters=args.parameters,
                revenue_col=args.revenue_column,
                cv_col=args.cv_column,
                top_n=args.top_n,
                min_cv=args.min_cv
            )
        else:
            result = engine.run(
                parameters=args.parameters,
                revenue_col=args.revenue_column,
                cv_col=args.cv_column,
                top_n=args.top_n,
                min_cv=args.min_cv,
                interactive=args.interactive
            )

        print(result)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
