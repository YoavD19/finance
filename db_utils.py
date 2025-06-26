from sqlalchemy import text, bindparam, create_engine
import pandas as pd
from streamlit import secrets, cache_data
import bcrypt


user = secrets["postgres"]["user"]
password = secrets["postgres"]["password"]
host = secrets["postgres"]["host"]
port = secrets["postgres"]["port"]
database = secrets["postgres"]["database"]

engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}')


def read_query_df(query_str, params=None):

    params = params or {}

    # Identify which parameters are lists/tuples -> need expanding=True
    bind_params = [
        bindparam(name, expanding=True)
        for name, value in params.items()
        if isinstance(value, (list, tuple))
    ]

    query = text(query_str).bindparams(*bind_params)

    return pd.read_sql_query(query, engine, params=params)


def run_query(query_str, params=None):

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

def return_run_query(query_str, params=None):
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
    
@cache_data
def cache_read_query(query_str, params=None):
    
    return return_run_query(query_str, params)

def hash_password(password):
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(password, hashed):
    """Check a password against a hashed password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
