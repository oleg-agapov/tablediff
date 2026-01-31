from __future__ import annotations

from reladiff import connect_to_table, diff_tables, connect
from tablediff.models import TableMeta, DiffResult, SchemaDiffResult


def get_schema(db_path, table_name):
    db = connect(db_path)
    return db.query_table_schema(tuple(table_name.split(".")))


def query_table(db_path, table_name, columns, where= "1 = 1"):
    db = connect(db_path)
    cols = ", ".join(columns)
    return db.query(f"select {cols} from {table_name} where {where}", list)


def calculate_differences(diffing_result):
    list(diffing_result)  # Consume the iterator into result_list, if we haven't already
    key_columns = diffing_result.info_tree.info.tables[0].key_columns
    # collect signs by IDs
    diff_by_key = {}
    for sign, values in diffing_result.result_list:
        k = values[: len(key_columns)]
        if k in diff_by_key:
            assert sign != diff_by_key[k]
            diff_by_key[k] = "!"
        else:
            diff_by_key[k] = sign
    # collect IDs by sign
    diff_by_sign = {k: [] for k in "+-!"}
    for key in diff_by_key:
        curr_sign = diff_by_key[key]
        diff_by_sign[curr_sign].append(key)
    return diff_by_key, diff_by_sign



def table_diff(db_path_a, db_path_b, table_a_name, table_b_name, primary_key, where=None) -> DiffResult:
    table_a = connect_to_table(db_path_a, table_a_name, primary_key)
    table_b = connect_to_table(db_path_b, table_b_name, primary_key)

    schema_a = get_schema(db_path_a, table_a_name)
    schema_b = get_schema(db_path_b, table_b_name)
    
    cols_a = [x for x in schema_a]
    cols_b = [x for x in schema_b]

    common_cols_set = set(cols_a).intersection(cols_b)
    # this is needed to preserve the order of columns
    common_cols = [col for col in cols_b if col in common_cols_set]

    diffing = diff_tables(table_a, table_b, key_columns=tuple([primary_key]), extra_columns=tuple(common_cols), where=where)
    stats = diffing.get_stats_dict()

    diff_by_keys, diff_by_sign = calculate_differences(diffing)
    
    return DiffResult(
        table_a=TableMeta(name=table_a_name, columns=cols_a, rows=stats["rows_A"]),
        table_b=TableMeta(name=table_b_name, columns=cols_b, rows=stats["rows_B"]),
        primary_key=primary_key,
        common_columns=common_cols,
        rows_only_in_a=stats["exclusive_A"],
        rows_only_in_b=stats["exclusive_B"],
        rows_in_both_same=stats["unchanged"],
        rows_in_both_diff=stats["updated"],
        diff_by_keys=diff_by_keys,
        diff_by_sign=diff_by_sign,
        diffing=diffing
    )


def schema_diff(db_path_a, db_path_b, table_a_name, table_b_name) -> SchemaDiffResult:
    """
    Compare schemas of two tables and return a comparison dictionary.
    
    Args:
        db_path_a: Database connection string for table A
        db_path_b: Database connection string for table B
        table_a_name: Name of table A
        table_b_name: Name of table B
    
    Returns:
        SchemaDiffResult with table names and column type comparison
    """
    schema_a = get_schema(db_path_a, table_a_name)
    schema_b = get_schema(db_path_b, table_b_name)
    
    # Get all unique column names from both tables
    all_columns = set(schema_a.keys()).union(set(schema_b.keys()))
    
    # Build the comparison dictionary
    columns = {}
    for col in sorted(all_columns):
        columns[col] = {
            "table_a": str(schema_a[col]) if col in schema_a else None,
            "table_b": str(schema_b[col]) if col in schema_b else None
        }
    
    return SchemaDiffResult(
        table_a=table_a_name,
        table_b=table_b_name,
        columns=columns
    )
