import logging

logging.basicConfig()
_logger = logging.getLogger('utils.data_model')


def get_value_in_dict_recursively(
    dictionary, path_to_destination,
    ignore_path_fail=None
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
        raise ValueError('path_to_destination must be str or list')
    if len(path_temp) > 1:
        pop = path_temp.pop(0)
        try:
            pop = int(pop)
        except ValueError:
            if ignore_path_fail:
                pass
            else:
                raise Exception('ill specified path_to_destination')

        try:
            return get_value_in_dict_recursively(dictionary[pop], path_temp)
        except:
            _logger.log(20, pop)
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
            _logger.log(20, 'KeyError: Could not find {}'.format(path_temp[0]))
            return None
        except TypeError:
            _logger.log(20, 'TypeError: Could not find {}'.format(path_temp[0]))
            return None