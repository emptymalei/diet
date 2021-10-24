import json
import os

from dietbox.data.wrangling.json import isoencode
from dietbox.data.wrangling.misc import (
    get_value_in_dict_recursively as _get_value_in_dict_recursively,
)
from loguru import logger


def cache_dataframe(dataframe, file, engine=None):
    """
    Write dataframe to a line-delineated json file.

    .. warning::
       pandas engine doesn't respect the date encoder define since it has its own.

    :param dataframe: inut pandas dataframe
    :param str file: path of file to be written to
    :param engine: we have two engines to convert the data to json, pandas and json.
    :return: if the engine is json, the converted json records are returned for inspections
    :rtype: list
    """

    if engine is None:
        engine = "json"

    if os.path.isfile(file):
        logger.error("File '{}' exists, overwriting...".format(file))

    if engine == "json":
        res = []
        with open(file, "w") as f:
            for _, row in dataframe.iterrows():
                row_dict = row.to_dict()
                logger.debug("cache_dataframe::", row_dict)
                res.append(row_dict)
                f.write(
                    json.dumps(row.to_dict(), default=isoencode, ignore_nan=True) + "\n"
                )
        return res
    elif engine == "pandas":
        dataframe.to_json(
            file,
            orient="records",
            lines=True,
            date_format="iso",
            default_handler=isoencode,
        )
    else:
        raise Exception(f"No engine defined for {engine}")


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
                logger.warning("could not load ", line, "\n", ee)
            data.append(line_data)

    return data


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
            logger.warning("Input data is not string")
            try:
                record_identifier = str(record_identifier)
            except Exception as ee:
                logger.error(
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
            logger.debug(f"{company} already exists! No need to save again!")
        save_records(record, self.target, is_flush=True)
