from sqlalchemy import text, bindparam, create_engine
import pandas as pd

def create_db(user, password, host, port, database):

    return create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}')

def read_query_df(query_str, engine, params=None):

    params = params or {}

    # Identify which parameters are lists/tuples -> need expanding=True
    bind_params = [
        bindparam(name, expanding=True)
        for name, value in params.items()
        if isinstance(value, (list, tuple))
    ]

    query = text(query_str).bindparams(*bind_params)

    return pd.read_sql_query(query, engine, params=params)


def run_query(query_str, engine, params=None):

    params = params or {}

    # Identify which parameters are lists/tuples -> need expanding=True
    bind_params = [
        bindparam(name, expanding=True)
        for name, value in params.items()
        if isinstance(value, (list, tuple))
    ]

    query = text(query_str).bindparams(*bind_params)

    with engine.begin() as conn:
        conn.execute(query, params)

def return_run_query(query_str, engine, params=None):
    "return a query not as a DataFrame"

    params = params or {}

    # Identify which parameters are lists/tuples -> need expanding=True
    bind_params = [
        bindparam(name, expanding=True)
        for name, value in params.items()
        if isinstance(value, (list, tuple))
    ]

    query = text(query_str).bindparams(*bind_params)

    with engine.begin() as conn:
        return conn.execute(query, params).fetchall()

