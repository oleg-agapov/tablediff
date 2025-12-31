from pprint import pprint

from reladiff import connect_to_table, diff_tables
from reladiff.databases import connect
from reladiff.diff_tables import DiffStats


def get_schema(db_path, table_name):
    db = connect(db_path)
    return db.query_table_schema([table_name])


def query_table(db_path, table_name, columns, where= "1 = 1"):
    db = connect(db_path)
    cols = ", ".join(columns)
    return db.query(f"select {cols} from {table_name} where {where}", list)


def get_differences(diffing_result) -> DiffStats:
    list(diffing_result)  # Consume the iterator into result_list, if we haven't already
    key_columns = diffing_result.info_tree.info.tables[0].key_columns
    diff_by_key = {}
    for sign, values in diffing_result.result_list:
        k = values[: len(key_columns)]
        if k in diff_by_key:
            assert sign != diff_by_key[k]
            diff_by_key[k] = "!"
        else:
            diff_by_key[k] = sign
    
    diff_by_sign = {k: [] for k in "+-!"}
    for key in diff_by_key:
        curr_sign = diff_by_key[key]
        diff_by_sign[curr_sign].append(key)
    
    #print(key_columns) # {<key_id>: <sign>}
    #print(diff_by_sign["!"]) # changed rows





def main(db_path, table_a_name, table_b_name, primary_key):
    table_a = connect_to_table(db_path, table_a_name, primary_key)
    table_b = connect_to_table(db_path, table_b_name, primary_key)

    schema_a = get_schema(db_path, table_a_name)
    schema_b = get_schema(db_path, table_b_name)
    
    cols_a = [x for x in schema_a]
    cols_b = [x for x in schema_b]

    common_cols = set(cols_a).intersection(cols_b) - set(primary_key)

    diffing = diff_tables(table_a, table_b, extra_columns=tuple(common_cols))
    stats = diffing.get_stats_dict()

    from tablediff.renderers import render_summary_rich
    from tablediff.models import DiffResult, DiffCounts
    from tablediff.adapters.base import TableMeta
    
    results = DiffResult(
        table_a=TableMeta(name=table_a_name, columns=cols_a, row_count=stats["rows_A"]),
        table_b=TableMeta(name=table_b_name, columns=cols_b, row_count=stats["rows_B"]),
        primary_key=primary_key,
        common_columns=common_cols,
        counts=DiffCounts(
            only_in_a=stats["exclusive_A"],
            only_in_b=stats["exclusive_B"],
            in_both_same=stats["unchanged"],
            in_both_diff=stats["updated"]
        )
    )
    render_summary_rich(results)

if __name__ == "__main__":
    db_path = "duckdb://./sample.duckdb"
    table_a = "users_dev"
    table_b = "users_prod"
    primary_key = "id"
    main(db_path, table_a, table_b, primary_key)
