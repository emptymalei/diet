from ast import literal_eval
import datetime
from loguru import logger
import os

import dateutil
import numpy as np
import pandas as pd
import simplejson as json


def load_schema(schema_path):
    """
    load_schema loads the schema file into dictionary for pandas to use
    """
    col_rename_dict = {}
    if not os.path.isfile(schema_path):
        raise Exception("Schema path is not a file: {}".format(schema_path))
    else:
        with open(schema_path, "r") as fp:
            schema = json.load(fp)

        return schema


def datetime_to_timestamp(data):

    return datetime.datetime.timestamp(data)


def convert_to_datetime(input_date, dayfirst=None, input_tz=None, output_tz=None):
    """
    Convert input to *datetime* object.
    This is the last effort of converting input to datetime.
    The order of instance check is
    1. datetime.datetime
    2. str
    3. float or int
    >>> handle_strange_dates(1531323212311)
    datetime(2018, 7, 11, 17, 33, 32, 311000)
    >>> handle_strange_dates(datetime(2085,1,1))
    datetime(2050, 1, 1)
    :param input_date: input data of any possible format
    :param input_tz: input timezone, defaults to utc
    :param output_tz: output timezone, defaults to utc
    :return: converted datetime format
    :rtype: datetime.datetime
    """
    if dayfirst is None:
        dayfirst = True
    if input_tz is None:
        input_tz = datetime.timezone.utc
    if output_tz is None:
        output_tz = datetime.timezone.utc

    res = None
    if isinstance(input_date, datetime.datetime):
        res = input_date
        if input_tz:
            res = res.replace(tzinfo=input_tz)
        if output_tz:
            res = res.astimezone(output_tz)
    elif isinstance(input_date, str):
        try:
            res = dateutil.parser.parse(input_date, dayfirst=dayfirst)
            if input_tz:
                res = res.replace(tzinfo=input_tz)
            if output_tz:
                res = res.astimezone(output_tz)
        except:
            logger.warning(f"Could not convert {input_date} to datetime!")
            pass
    elif isinstance(input_date, (float, int)):
        try:
            res = datetime.datetime.utcfromtimestamp(input_date / 1000)
            if input_tz:
                res = res.replace(tzinfo=input_tz)
            if output_tz:
                res = res.astimezone(output_tz)
        except:
            logger.warning(f"Could not convert {input_date} to datetime!")
            pass
    else:
        raise Exception(
            "Could not convert {} to datetime: type {} is not handled".format(
                input_date, type(input_date)
            )
        )

    return res


def unpack_datetime(data):
    res = {}
    dt = convert_to_datetime(data, dayfirst=False)
    if dt:
        try:
            res["year"] = dt.year
        except Exception as e:
            logger.error(f"Could not find year for {dt} (raw: {data})")

        try:
            res["month"] = dt.month
        except Exception as e:
            logger.error(f"Could not find month for {dt} (raw: {data})")

        try:
            res["day"] = dt.day
        except Exception as e:
            logger.error(f"Could not find day for {dt} (raw: {data})")

        try:
            res["weekday"] = dt.weekday() + 1
        except Exception as e:
            logger.error(f"Could not find weekday for {dt} (raw: {data})")

    return res


def date_range_has_weekday(dt_start, dt_end):
    """
    date_range_has_weekday decides if the given date range contains weekday

    :param dt_start: datetime of the start of date range
    :param dt_end: datetime of the end of date range
    """
    res = []

    if pd.isnull(dt_start) or pd.isnull(dt_end):
        logger.warning(f"date start end not specified: {dt_start}, {dt_end}")
        return None

    if isinstance(dt_start, str):
        dt_start = pd.to_datetime(dt_start)
    if isinstance(dt_end, str):
        dt_end = pd.to_datetime(dt_end)

    for dt in pd.date_range(dt_start, dt_end):
        if dt.weekday() < 5:
            res.append(True)
        else:
            res.append(False)

    return True in res


def unpack_location_types(location_type):
    """
    unpack_location_types unpacks the location type strings into binary features

    Location types can be 'com_without_ramp_with_forklift', 'com_with_ramp',
    'com_without_ramp_without_forklift', 'residential', or null.

    :param location_type: location type string
    :type location_type: str
    """

    if isinstance(location_type, str) and "[" not in location_type:
        dispatcher = {
            "com_without_ramp_with_forklift": {
                "commercial": True,
                "ramp": False,
                "forklift": True,
            },
            "com_with_ramp": {"commercial": True, "ramp": True, "forklift": False},
            "com_without_ramp_without_forklift": {
                "commercial": True,
                "ramp": False,
                "forklift": False,
            },
            "residential": {"commercial": False, "ramp": False, "forklift": False},
        }

        if isinstance(location_type, str):
            if "[" in location_type:
                location_type = literal_eval(location_type)

        if isinstance(location_type, list):
            location_type = location_type[0]

        res = {"commercial": None, "ramp": None, "forklift": None}
        if pd.isnull(location_type):
            res = {"commercial": None, "ramp": None, "forklift": None}
        elif isinstance(location_type, str):
            res = dispatcher.get(location_type, res)
        else:
            logger.error(f"{location_type} can not be parsed")
    else:
        location_type = (
            location_type.replace("[", "")
            .replace("]", "")
            .replace('"', "")
            .replace("'", "")
            .split(",")
        )
        location_type = [i.strip() for i in location_type]
        # possible_types = ['commercial', 'forklift', 'no_equipment', 'ramp', 'residential']
        res = {"commercial": None, "ramp": None, "forklift": None}
        if "commercial" in location_type:
            res["commercial"] = True
        elif "residential" in location_type:
            res["commercial"] = False

        if "forklift" in location_type:
            res["forklift"] = True
        else:
            res["forklift"] = False

        if "ramp" in location_type:
            res["ramp"] = True
        else:
            res["ramp"] = False

        if "no_equipment" in location_type:
            res["forklift"] = False
            res["ramp"] = False

    return res


#  JSON

def get_value_in_dict_recursively(
    dictionary, path_to_destination, ignore_path_fail=None
):
    """
    Get value of a dictionary according to specified path (names)

    :param dict dictionary: input dictionary
    :param names: path to the value to be obtained

    This function always returns the value or None.

    >>> get_value_in_dict_recursively({'lvl_1':{'lvl_2':{'lvl_3':'lvl_3_value'}}},['lvl_1','lvl_3'])
    {'lvl_3':'lvl_3_value'}
    >>> get_value_in_dict_recursively({1:{2:{3:'hi'}}},[1,'2',3])
    {'hi'}
    """
    if ignore_path_fail is None:
        ignore_path_fail = True

    if isinstance(path_to_destination, list):
        path_temp = path_to_destination.copy()
    elif isinstance(path_to_destination, str):
        path_temp = [path_to_destination].copy()
    else:
        raise ValueError("path_to_destination must be str or list")
    if len(path_temp) > 1:
        pop = path_temp.pop(0)
        try:
            pop = int(pop)
        except ValueError:
            if ignore_path_fail:
                pass
            else:
                raise Exception("ill specified path_to_destination")

        try:
            return get_value_in_dict_recursively(dictionary[pop], path_temp)
        except:
            logger.log(20, pop)
            return None
    elif len(path_temp) == 0:
        return None
    else:
        try:
            val = int(path_temp[0])
        except:
            val = path_temp[0]
        try:
            return dictionary[val]
        except KeyError:
            logger.log(20, "KeyError: Could not find {}".format(path_temp[0]))
            return None
        except TypeError:
            logger.log(20, "TypeError: Could not find {}".format(path_temp[0]))
            return None


class JSONEncoder(json.JSONEncoder):
    """
    data serializer for json
    """

    def default(self, obj):
        """
        default serializer
        """
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return {"__type__": "__datetime__", "datetime": obj.isoformat()}

        return json.JSONEncoder.default(self, obj)


def decode(obj):
    """
    decode decodes the JSONEncoder results
    """
    if "__type__" in obj:
        if obj["__type__"] == "__datetime__":
            return dateutil.parser.parse(obj["datetime"])
    return obj


def isoencode(obj):
    """
    isoencode decodes many different objects such as
    np.bool -> regular bool
    """
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.int64):
        return int(obj)
    if isinstance(obj, np.float64):
        return float(obj)
    if isinstance(obj, np.bool_):
        return bool(obj)


def remove_outliers(dataset, criteria=None):
    """
    remove_outliers will filter out the outliers of dataset

    Changes will be made to original dataset.

    :param dataset: dataframe that contains the data to be filtered
    """
    logger.info("Removing outliers ... ")
    if criteria is None:
        criteria = {"target": {"quantile_range": [0.01, 0.99]}}

    for col in criteria:
        if col not in dataset.columns:
            logger.warning(f"Column {col} is not in dataset ({dataset.columns})")
            continue
        # Remove isna if required in criteria
        col_isna = criteria[col].get("isna", False)
        if col_isna:
            dataset = dataset.loc[~dataset[col].isna()]

        # only use between values
        col_range = criteria[col].get("range", [-np.inf, np.inf])
        col_quantile_range = criteria[col].get("quantile_range", ())
        if col_quantile_range:
            col_range_from_quantile_lower = dataset[col].quantile(col_quantile_range[0])
            col_range_from_quantile_upper = dataset[col].quantile(col_quantile_range[1])
            if col_range_from_quantile_lower >= col_range[0]:
                col_range[0] = col_range_from_quantile_lower
            if col_range_from_quantile_upper <= col_range[1]:
                col_range[1] = col_range_from_quantile_upper

        dataset = dataset.loc[dataset[col].between(*col_range)]

    logger.info("Removed outliers!")


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)




# Generic
def convert_str_repr_to_list(inp):
    """
    convert_str_repr_to_list concerts string representation of list to list
    """

    res = []
    if isinstance(inp, str):
        try:
            res = literal_eval(inp)
        except Exception as e:
            raise Exception(f"Could not convert {inp} to list")
    elif isinstance(inp, (list, tuple, set)):
        res = list(inp)

    return res


def convert_str_repr_to_tuple(inp):
    """
    convert_str_repr_to_tuple converts string representation of tuple to tuple
    """

    res = []
    if isinstance(inp, str):
        try:
            res = literal_eval(inp)
        except Exception as e:
            raise Exception(f"Could not convert {inp} to list")
    if isinstance(inp, (list, tuple, set)):
        res = tuple(inp)

    return res



if __name__ == "__main__":

    print(unpack_location_types("['commercial', 'ramp']"))

    pass
