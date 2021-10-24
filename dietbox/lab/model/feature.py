import pandas as pd
from loguru import logger
from sklearn.preprocessing import LabelEncoder, StandardScaler


class MultiColumnCategicalEncoder:
    """
    Labelencoder applied to multiple columns
    """

    def __init__(self, encoders=None, columns=None, encode_with=None):
        """
        __init__ initializes the MultiColumnCategicalEncoder with encoder and scaler types.

        :param encoders: dictionary of encoders to be used on cols, defaults to {}
        :type encoders: dict, optional
        :param columns: list of columns to be encoded, defaults to None
        :type columns: list, optional
        :param encode_with: scikit learn categorical encoders to be applied on cols
        """
        self.columns = columns
        if encode_with is None:
            encode_with = LabelEncoder
        self.encode_with = encode_with
        if encoders:
            self.encoders = encoders
        else:
            self.encoders = {}

    def fit(self, X, y=None):
        self.check_encoders = []
        return self

    def transform(self, X):
        """
        Transforms columns of X specified in self.columns using
        LabelEncoder(). If no columns specified, transforms all
        columns in X.

        :param X: dataset to be transformed
        :return: transformed dataset
        """
        output = X.copy()
        if self.columns is not None:
            for col in self.columns:
                _le = self.encode_with()
                if self.encoders.get(col):
                    output[col] = self.encoders.get(col).transform(output[col])
                else:
                    output[col] = _le.fit_transform(output[col])
                    logger.debug(f"1. preparing encoder for {col}")
                    self.encoders[col] = _le
                    self.check_encoders.append({col: _le})
        else:
            for colname, col in output.iteritems():
                _le = self.encode_with()
                if self.encoders.get(col):
                    output[colname] = self.encoders.get(colname).transform(col)
                else:
                    output[colname] = _le.fit_transform(col)
                    logger.debug(f"2. preparing encoder for {col}")
                    self.encoders[colname] = _le
                    self.check_encoders.append({colname: _le})
        return output

    def fit_transform(self, X, y=None):
        return self.fit(X, y).transform(X)


class MultiColumnScaler:
    """
    Scalers to be applied to multiple columns.
    """

    def __init__(self, encoders=None, columns=None, encode_with=None):
        """
        __init__ initializes the MultiColumnScaler with encoder and scaler types.

        :param encoders: dictionary of encoders to be used on cols, defaults to {}
        :type encoders: dict, optional
        :param columns: list of columns to be encoded, defaults to None
        :type columns: list, optional
        :param encode_with: scaler to be applied, defaults to StandardScaler
        """
        if encode_with is None:
            encode_with = StandardScaler
        self.encode_with = encode_with
        self.columns = columns  # array of column names to encode
        if encoders:
            self.encoders = encoders
        else:
            self.encoders = {}

    def fit(self, X, y=None):
        self.check_encoders = []
        return self

    def transform(self, X):
        """
        Transforms columns of X specified in self.columns using
        LabelEncoder(). If no columns specified, transforms all
        columns in X.

        :param X: dataset to be transformed
        :return: transformed dataset
        """
        output = X.copy()
        if self.columns is not None:
            for col in self.columns:
                _scaler = self.encode_with()
                if self.encoders.get(col):
                    output[col] = self.encoders.get(col).transform(output[[col]])
                else:
                    output[col] = _scaler.fit_transform(output[[col]])
                    logger.debug(f"1. preparing encoder for {col}")
                    self.encoders[col] = _scaler
                    self.check_encoders.append({col: _scaler})
        else:
            for colname, col in output.iteritems():
                _scaler = self.encode_with()
                if self.encoders.get(col):
                    output[colname] = self.encoders.get(colname).transform(
                        pd.DataFrame(col)
                    )
                else:
                    output[colname] = _scaler.fit_transform(pd.DataFrame(col))
                    logger.debug(f"2. preparing encoder for {col}")
                    self.encoders[colname] = _scaler
                    self.check_encoders.append({colname: _scaler})
        return output

    def fit_transform(self, X, y=None):
        return self.fit(X, y).transform(X)
