# Adapted from
# https://gist.github.com/danallison/7217d76d944ea4d8dabd0ba3041ebefc
from functools import wraps

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sshtunnel import SSHTunnelForwarder


def get_engine_for_port(port, host, config):
    return create_engine(
        "postgresql://{user}:{password}@{host}:{port}/{db}".format(
            user=config.get("sql_username"),
            password=config.get("sql_password"),
            host=host,
            port=port,
            db=config.get("sql_main_database"),
        )
    )


def with_sql_session(function, config, args, kwargs, engine=None):
    if engine is None:
        engine = get_engine_for_port(
            config.get("sql_port", 5432), config.get("sql_hostname"), config
        )
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        return function(session, *args, **kwargs)
    finally:
        session.close()


def with_local_sql_session(function, config, *args, **kwargs):
    return with_sql_session(function, config, args, kwargs)


def with_remote_sql_session(function, config, *args, **kwargs):
    # Hat tip: https://stackoverflow.com/a/38001815
    with SSHTunnelForwarder(
        (config.get("ssh_host"), config.get("ssh_port")),
        ssh_username=config.get("ssh_user"),
        ssh_pkey=config.get("ssh_key"),
        ssh_private_key_password=config.get("ssh_paraphrase"),
        remote_bind_address=(config.get("sql_hostname"), config.get("sql_port", 5432)),
    ) as tunnel:
        tunnel.start()
        engine = get_engine_for_port(tunnel.local_bind_port, "127.0.0.1", config)
        logger.debug("Postgres Engine started...")
        return with_sql_session(function, config, args, kwargs, engine=engine)


# Create Decorators for Remote and Local SQL control flow


def local_sql_session(config):
    """
    local_sql_session creates the control flow for a local sql session

    ```python
    config = {
        "sql_hostname": os.getenv("PLATFORM_SQL_URI"),  # 'sql_hostname'
        "sql_username": os.getenv("PLATFORM_SQL_USERNAME"),  # 'sql_username'
        "sql_password": os.getenv("PLATFORM_SQL_PWD"),  # 'sql_password'
        "sql_main_database": os.getenv("PLATFORM_SQL_DB"),  # 'db_name'
        "sql_port": int(os.getenv("PLATFORM_SQL_PORT")),
        "ssh_host": os.getenv("SSH_HOST"),  #'ssh_hostname'
        "ssh_user": os.getenv("SSH_USER"),  #'ssh_username'
        "ssh_port": 22,
        "ssh_key": os.getenv("SSH_KEY"),
    }

    @local_sql_session(config)
    def main(session):
        q = session.execute('SELECT * from app_prod.shipment LIMIT 10;')
        print( q.fetchall() )

        # or use pandas
        # session.bind refers to the engine
        df = pd.read_sql(query, session.bind)
        print(df.head())
    ```

    :param config: configuration dictionary
    :type config: dict
    """

    def local_sql_session_with_config(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            return with_local_sql_session(function, config, *args, **kwargs)

        return wrapper

    return local_sql_session_with_config


def remote_sql_session(config):
    """
    local_sql_session creates the control flow for a remote sql session

    ```python
    config = {
        "sql_hostname": os.getenv("PLATFORM_SQL_URI"),  # 'sql_hostname'
        "sql_username": os.getenv("PLATFORM_SQL_USERNAME"),  # 'sql_username'
        "sql_password": os.getenv("PLATFORM_SQL_PWD"),  # 'sql_password'
        "sql_main_database": os.getenv("PLATFORM_SQL_DB"),  # 'db_name'
        "sql_port": int(os.getenv("PLATFORM_SQL_PORT")),
        "ssh_host": os.getenv("SSH_HOST"),  #'ssh_hostname'
        "ssh_user": os.getenv("SSH_USER"),  #'ssh_username'
        "ssh_port": 22,
        "ssh_key": os.getenv("SSH_KEY"),
    }

    @remote_sql_session(config)
    def main(session):
        q = session.execute('SELECT * from app_prod.shipment LIMIT 10;')
        print( q.fetchall() )

        # or use pandas
        # session.bind refers to the engine
        df = pd.read_sql(query, session.bind)
        print(df.head())
    ```

    :param config: configuration dictionary
    :type config: dict
    """

    def remote_sql_session_with_config(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            return with_remote_sql_session(function, config, *args, **kwargs)

        return wrapper

    return remote_sql_session_with_config
