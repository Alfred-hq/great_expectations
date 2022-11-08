import hashlib
from typing import List, Union

try:
    import polars as pl
except ImportError:
    polars = None

import great_expectations.exceptions as ge_exceptions
from great_expectations.execution_engine.split_and_sample.data_splitter import (
    DataSplitter,
    DatePart,
)


class PolarsDataSplitter(DataSplitter):
    """Methods for splitting data accessible via PolarsExecutionEngine.

    Note, for convenience, you can also access DatePart via the instance variable
    date_part e.g. SparkDataSplitter.date_part.MONTH
    """

    def split_on_year(
        self,
        df: pl.DataFrame,
        column_name: str,
        batch_identifiers: dict,
    ) -> pl.DataFrame:
        """Split on year values in column_name.

        Args:
            df: dataframe from batch data.
            column_name: column in table to use in determining split.
            batch_identifiers: should contain a dateutil parseable datetime whose
                relevant date parts will be used for splitting or key values
                of {date_part: date_part_value}.

        Returns:
            List of boolean clauses based on whether the date_part value in the
                batch identifier matches the date_part value in the column_name column.
        """
        return self.split_on_date_parts(
            df=df,
            column_name=column_name,
            batch_identifiers=batch_identifiers,
            date_parts=[DatePart.YEAR],
        )

    def split_on_year_and_month(
        self,
        df: pl.DataFrame,
        column_name: str,
        batch_identifiers: dict,
    ) -> pl.DataFrame:
        """Split on year and month values in column_name.

        Args:
            df: dataframe from batch data.
            column_name: column in table to use in determining split.
            batch_identifiers: should contain a dateutil parseable datetime whose
                relevant date parts will be used for splitting or key values
                of {date_part: date_part_value}.

        Returns:
            List of boolean clauses based on whether the date_part value in the
                batch identifier matches the date_part value in the column_name column.
        """
        return self.split_on_date_parts(
            df=df,
            column_name=column_name,
            batch_identifiers=batch_identifiers,
            date_parts=[DatePart.YEAR, DatePart.MONTH],
        )

    def split_on_year_and_month_and_day(
        self,
        df: pl.DataFrame,
        column_name: str,
        batch_identifiers: dict,
    ) -> pl.DataFrame:
        """Split on year and month and day values in column_name.

        Args:
            df: dataframe from batch data.
            column_name: column in table to use in determining split.
            batch_identifiers: should contain a dateutil parseable datetime whose
                relevant date parts will be used for splitting or key values
                of {date_part: date_part_value}.

        Returns:
            List of boolean clauses based on whether the date_part value in the
                batch identifier matches the date_part value in the column_name column.
        """
        return self.split_on_date_parts(
            df=df,
            column_name=column_name,
            batch_identifiers=batch_identifiers,
            date_parts=[DatePart.YEAR, DatePart.MONTH, DatePart.DAY],
        )

    def split_on_date_parts(
        self,
        df: pl.DataFrame,
        column_name: str,
        batch_identifiers: dict,
        date_parts: Union[List[DatePart], List[str]],
    ) -> pl.DataFrame:
        """Split on date_part values in column_name.

        Values are NOT truncated, for example this will return data for a
        given month (if only month is chosen for date_parts) for ALL years.
        This may be useful for viewing seasonality, but you can also specify
        multiple date_parts to achieve date_trunc like behavior e.g.
        year, month and day.

        Args:
            df: dataframe from batch data.
            column_name: column in data used to determine split.
            batch_identifiers: should contain a dateutil parseable datetime whose date parts
                will be used for splitting or key values of {date_part: date_part_value}
            date_parts: part of the date to be used for splitting e.g.
                DatePart.DAY or the case-insensitive string representation "day"

        Returns:
            Dataframe with splitting applied.
        """
        self._validate_date_parts(date_parts)

        date_parts = self._convert_date_parts(date_parts)

        column_batch_identifiers: dict = batch_identifiers[column_name]

        date_parts_dict: dict = (
            self._convert_datetime_batch_identifiers_to_date_parts_dict(
                column_batch_identifiers, date_parts
            )
        )

        for date_part, date_part_value in date_parts_dict.items():
            df = df[getattr(df[column_name].dt, date_part)() == date_part_value]

        return df

    @staticmethod
    def split_on_whole_table(
        df: pl.DataFrame,
    ) -> pl.DataFrame:
        """No op. Return the same data that is passed in.

        Args:
            df: DataFrame that will be returned

        Returns:
            Unfiltered DataFrame.
        """
        return df

    @staticmethod
    def split_on_column_value(
        df: pl.DataFrame, column_name: str, batch_identifiers: dict
    ) -> pl.DataFrame:
        """Return a dataframe where rows are filtered based on the specified column value.

        Args:
            df: DataFrame to be filtered.
            column_name: Column to use in comparison.
            batch_identifiers: Contains value to use in comparison e.g. batch_identifiers={ 'col': value }.

        Returns:
            Filtered spark DataFrame.
        """
        return df[df[column_name] == batch_identifiers[column_name]]

    @staticmethod
    def split_on_converted_datetime(
        df: pl.DataFrame,
        column_name: str,
        batch_identifiers: dict,
        date_format_string: str = "%Y-%m-%d",
    ) -> pl.DataFrame:
        """Convert the values in the named column to the given date_format, and split on that"""

        stringified_datetime_series = df[column_name].apply(
            lambda x: x.strftime(date_format_string)
        )
        matching_string = batch_identifiers[column_name]
        return df[stringified_datetime_series == matching_string]

    @staticmethod
    def split_on_divided_integer(
        df: pl.DataFrame, column_name: str, divisor: int, batch_identifiers: dict
    ) -> pl.DataFrame:
        """Divide the values in the named column by `divisor`, and split on that"""

        matching_divisor = batch_identifiers[column_name]
        matching_rows = df[column_name].apply(
            lambda x: int(x / divisor) == matching_divisor
        )

        return df[matching_rows]

    @staticmethod
    def split_on_mod_integer(
        df: pl.DataFrame, column_name: str, mod: int, batch_identifiers: dict
    ) -> pl.DataFrame:
        """Divide the values in the named column by `divisor`, and split on that"""

        matching_mod_value = batch_identifiers[column_name]
        matching_rows = df[column_name].apply(lambda x: x % mod == matching_mod_value)

        return df[matching_rows]

    @staticmethod
    def split_on_multi_column_values(
        df: pl.DataFrame, column_names: List[str], batch_identifiers: dict
    ) -> pl.DataFrame:
        """Split on the joint values in the named columns"""

        subset_df = df.clone()
        for column_name in column_names:
            value = batch_identifiers.get(column_name)
            if not value:
                raise ValueError(
                    f"In order for PolarsExecutionEngine to `_split_on_multi_column_values`, "
                    f"all values in column_names must also exist in batch_identifiers. "
                    f"{column_name} was not found in batch_identifiers."
                )
            subset_df = subset_df[subset_df[column_name] == value]
        return subset_df

    @staticmethod
    def split_on_hashed_column(
        df: pl.DataFrame,
        column_name: str,
        hash_digits: int,
        batch_identifiers: dict,
        hash_function_name: str = "md5",
    ) -> pl.DataFrame:
        """Split on the hashed value of the named column"""
        try:
            hash_method = getattr(hashlib, hash_function_name)
        except (TypeError, AttributeError):
            raise (
                ge_exceptions.ExecutionEngineError(
                    f"""The splitting method used with SparkDFExecutionEngine has a reference to an invalid hash_function_name.
                        Reference to {hash_function_name} cannot be found."""
                )
            )
        matching_rows = df[column_name].apply(
            lambda x: hash_method(str(x).encode()).hexdigest()[-1 * hash_digits :]
            == batch_identifiers["hash_value"]
        )
        return df[matching_rows]
