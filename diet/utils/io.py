import json
import logging
import os

from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder

from diet.data.wrangling import get_value_in_dict_recursively as _get_value_in_dict_recursively

logging.basicConfig()
_logger = logging.getLogger("utils.io")


def get_environ(env_name, env_default_value):
    """Get current environment variables"""
    if env is None:
        env = env or os.environ.get(env_name, env_default_value)
    env = env.lower()
    return env


def save_records(data_inp, output, is_flush=None, write_mode=None):
    """Save list of dicts to file. Instead of loading pandas for such a simple job, this function does the work in most cases.

    :param data_inp: dict or list of dict to be saved
    :param output: path to output file
    :is_flush: whether to flush data to file for each row written to file
    :return: None
    """

    if write_mode is None:
        write_mode = "a+"

    if is_flush is None:
        is_flush = False

    if isinstance(data_inp, list):
        data = data_inp
    elif isinstance(data_inp, dict):
        data = [data_inp]
    else:
        raise Exception("Input data is neither list nor dict: {}".format(data_inp))

    try:
        with open(output, write_mode) as fp:
            for i in data:
                json.dump(i, fp)
                fp.write("\n")
                if is_flush:
                    fp.flush()
    except Exception as ee:
        raise Exception("Could not load data to file: {}".format(ee))


def load_records(data_path_inp):
    """Load data from a line deliminated json file. Instead of loading pandas for such a simple job, this function does the work in most cases.

    :param data_path_inp: data file path
    :return: list of dicts
    """

    data = []

    with open(data_path_inp, "r") as fp:
        for line in fp:
            line = line.replace("null", ' "None" ')
            try:
                line_data = json.loads(line.strip())
            except Exception as ee:
                _logger.warning("could not load ", line, "\n", ee)
            data.append(line_data)

    return data


def connect_db(db_spec, tunnel=None):
    """Create MongoDB Connections

    To connect to remote mongodb database, ssh tunneling is needed.

    Example config:

    If we are authenticating using username and password

    ```
    db_spec = {
        "host": "mongodb+srv://my_username:my_password@thisismylink.mongodb.net",
        "db_name": "my-database"
    }
    ```

    Or with tunneling

    ```
    db_spec = {
        "host": 'my_host_link_address.mongo.net',
        "db_name": "my_database",
        "port": 22,
        "tunnel": {
            "mongo_host": "127.0.0.1",
            "mongo_port": 27017,
            "ssh_user": "ssh_username",
            "ssh_key": "/path/to/my/ssh/key",
            "ssh_pass": "paraphase_of_my_ssh_key"
        }
    }

    ```

    """

    if tunnel is None:
        if db_spec.get("tunnel"):
            tunnel = True

    db_host = db_spec.get("host")
    db_port = db_spec.get("port")
    db_name = db_spec.get("db_name")
    # username used to directly connect to the database
    db_username = db_spec.get("username")
    # password associated to the username
    db_password = db_spec.get("password")

    if not tunnel:
        client = MongoClient(db_host, readPreference="secondaryPreferred")
        db = client[db_name]
        return db
    else:
        db_tunnel = db_spec.get("tunnel")
        db_tunnel__ssh_user = db_tunnel.get("ssh_user")
        db_tunnel__ssh_key = db_tunnel.get("ssh_key")
        db_tunnel__ssh_pass = db_tunnel.get("ssh_pass")
        db_tunnel__mongo_host = db_tunnel.get("mongo_host")
        db_tunnel__mongo_port = db_tunnel.get("mongo_port")

        mongo_host = tuple([db_host, db_port])
        mongo_db = db_name

        ssh_user = db_tunnel__ssh_user
        ssh_key = db_tunnel__ssh_key
        ssh_pass = db_tunnel__ssh_pass

        assert ssh_pass is not None, "SSH_PASS missing"

        remote_bind_db_host = db_tunnel__mongo_host
        remote_bind_db_port = db_tunnel__mongo_port

        # construct sshtunnelforwarder parameter dictionary
        ssh_tunnel_params = {
            "remote_bind_address": (remote_bind_db_host, remote_bind_db_port),
            "ssh_username": ssh_user,
        }
        if ssh_key:
            ssh_tunnel_params["ssh_pkey"] = ssh_key
            if ssh_pass:
                ssh_tunnel_params["ssh_private_key_password"] = ssh_pass
        else:
            ssh_tunnel_params["ssh_username"] = ssh_pass

        server = SSHTunnelForwarder(ssh_address_or_host=mongo_host, **ssh_tunnel_params)

        server.start()
        client = MongoClient(remote_bind_db_host, server.local_bind_port)
        # server.local_bind_port is assigned local port
        db = client[mongo_db]

        try:
            return db
        finally:
            server.stop()


class LocalStorage:
    """A model for local storage"""

    def __init__(self, target):
        self.target = target
        self.records = []

    def load_records(self, keep_in_memory=True):
        """Load records for target"""

        all_records = load_records(self.target)
        if keep_in_memory:
            self.records = all_records

        return all_records

    def is_in_storage(self, record_identifier, record_identifier_lookup_paths):
        """Check if the record is already in storage"""
        if isinstance(record_identifier_lookup_paths, str):
            record_identifier_lookup_paths = [record_identifier_lookup_paths]

        if not isinstance(record_identifier, str):
            _logger.warning("Input data is not string")
            try:
                record_identifier = str(record_identifier)
            except Exception as ee:
                _logger.error(
                    f"Could not convert input {record_identifier} to string! {ee}"
                )
                return {"exists": False, "record": None}

        record_identifier = record_identifier.lower()

        if not self.records:
            all_existing_records = self.load_records()
        all_existing_records = self.records

        for record in all_existing_records:
            for record_identifier_lookup_path in record_identifier_lookup_paths:
                record_company = _get_value_in_dict_recursively(
                    record, record_identifier_lookup_path
                )
                if record_company:
                    record_company = record_company.lower()
                    if record_identifier == record_company:
                        return {"exists": True, "record": record}

        return {"exists": False, "record": None}

    def save_records(self, record):
        """Save records in target"""
        company = record.get("company")

        if self.is_in_storage(company).get("exists"):
            _logger.debug(f"{company} already exists! No need to save again!")
        save_records(record, self.target, is_flush=True)
