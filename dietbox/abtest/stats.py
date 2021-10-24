import numpy as np
import scipy.stats as scs
from dietbox.abtest.stats_util import (
    cal_conversion_rate,
    cal_conversion_uplift,
    cal_difference_standard_error,
    cal_p_value,
    cal_pooled_probability,
    cal_pooled_std_err,
    cal_standard_error,
    cal_z_score,
)


class ABTestRatiosNaive:
    def __init__(self, ab_test_data, test_name=None):

        self.data = ab_test_data
        self.A_total = ab_test_data.get("A_total")
        self.A_converted = ab_test_data.get("A_converted")
        self.B_total = ab_test_data.get("B_total")
        self.B_converted = ab_test_data.get("B_converted")
        if test_name:
            self.name = test_name
        else:
            self.name = None

    def conversion_rate(self):
        """Conversion rate for a specific group"""

        self.A_cr = cal_conversion_rate(self.A_total, self.A_converted)
        self.B_cr = cal_conversion_rate(self.B_total, self.B_converted)

        return self.A_cr, self.B_cr

    def standard_error(self):
        """standard error"""

        self.A_std_err = cal_standard_error(self.A_total, self.A_converted)
        self.B_std_err = cal_standard_error(self.B_total, self.B_converted)

        return self.A_std_err, self.B_std_err

    def pooled_probability(self):
        """Pooled probability for two samples

        This is better used as an intermediate value.
        """

        A_total, B_total, A_converted, B_converted = (
            self.A_total,
            self.B_total,
            self.A_converted,
            self.B_converted,
        )

        self.probability = cal_pooled_probability(
            A_total, B_total, A_converted, B_converted
        )

        return self.probability

    def pooled_std_err(self):
        """Pooled standard error for two samples

        For more information about the definition, refer to wikipedia:
        https://en.wikipedia.org/wiki/Pooled_variance
        """

        self.pooled_probability()

        # Pooled standard error
        pp = self.probability
        self.pld_std_err = cal_pooled_std_err(pp, self.A_total, self.B_total)

        return self.pld_std_err

    def conversion_uplift(self):
        """Uplift in conversion rate

        Relative uplift is the relative conversion rate difference between the test groups
        """

        A_total, B_total, A_converted, B_converted = (
            self.A_total,
            self.B_total,
            self.A_converted,
            self.B_converted,
        )

        self.uplift = cal_conversion_uplift(A_total, B_total, A_converted, B_converted)

        return self.uplift

    def p_value(self, test=None):
        """"""

        # self.conversion_rate()

        self.p = cal_p_value(self.data)

        return self.p

    def z_score(self, significance_level=None, two_tailed=None):

        if significance_level is None:
            significance_level = self.p

        if two_tailed is None:
            two_tailed = True

        self.z = cal_z_score(significance_level, two_tailed)

        return self.z

    def difference_std_err(self):
        """"""

        A_total, B_total, A_converted, B_converted = (
            self.A_total,
            self.B_total,
            self.A_converted,
            self.B_converted,
        )

        self.diff_std_err = cal_difference_standard_error(
            A_total, B_total, A_converted, B_converted
        )

        return self.diff_std_err

    def report(self, with_data=None, pipeline=None):
        """Run pipeline and"""
        if pipeline is None:
            pipeline = "all"
        if with_data is None:
            with_data = True

        all_pipes = [
            meth
            for meth in dir(self)
            if callable(getattr(self, meth)) and "__" not in meth and meth != "report"
        ]

        for method in all_pipes:
            getattr(self, method)()

        res = {
            "kpi": {"a": self.A_cr, "b": self.B_cr},
            "std_err": {"a": self.A_std_err, "b": self.B_std_err},
            "pooled_std_err": self.pld_std_err,
            "probability": self.probability,
            "uplift": self.uplift,
            "p_value": self.p,
            "z_score": self.z,
            "diff_std_err": self.diff_std_err,
        }

        if self.name:
            res["name"] = self.name
        if with_data:
            res["data"] = self.data

        return res


class ABTestRatios:
    """This test uses the difference between the ratios $d=A_cr - B_cr$ as the signature.

    According to central limit theorem, we could approximate the distribution of d as a normal distribution.

    Null hypothesis: d = 0, sigma = pooled standard error
    Alternative: d !=0, sigma = pooled std error

    """

    def __init__(self, ab_test_data, test_name=None):

        self.data = ab_test_data
        self.A_total = ab_test_data.get("A_total")
        self.A_converted = ab_test_data.get("A_converted")
        self.B_total = ab_test_data.get("B_total")
        self.B_converted = ab_test_data.get("B_converted")
        if test_name:
            self.name = test_name
        else:
            self.name = None

    def conversion_rate(self):
        """Conversion rate for a specific group"""

        self.A_cr = cal_conversion_rate(self.A_total, self.A_converted)
        self.B_cr = cal_conversion_rate(self.B_total, self.B_converted)

        return self.A_cr, self.B_cr

    def standard_error(self):
        """standard error"""

        self.A_std_err = cal_standard_error(self.A_total, self.A_converted)
        self.B_std_err = cal_standard_error(self.B_total, self.B_converted)

        return self.A_std_err, self.B_std_err

    def conversion_uplift(self):
        """Uplift in conversion rate

        Relative uplift is the relative conversion rate difference between the test groups
        """

        A_total, B_total, A_converted, B_converted = (
            self.A_total,
            self.B_total,
            self.A_converted,
            self.B_converted,
        )

        self.uplift = cal_conversion_uplift(A_total, B_total, A_converted, B_converted)

        return self.uplift

    def pooled_probability(self):
        """Pooled probability for two samples

        This is better used as an intermediate value.
        """

        A_total, B_total, A_converted, B_converted = (
            self.A_total,
            self.B_total,
            self.A_converted,
            self.B_converted,
        )

        self.probability = cal_pooled_probability(
            A_total, B_total, A_converted, B_converted
        )

        return self.probability

    def pooled_std_err(self):
        """Pooled standard error for two samples

        For more information about the definition, refer to wikipedia:
        https://en.wikipedia.org/wiki/Pooled_variance
        """

        self.pooled_probability()

        # Pooled standard error
        pp = self.probability
        self.pld_std_err = cal_pooled_std_err(pp, self.A_total, self.B_total)

        return self.pld_std_err

    def difference_std_err(self):
        """"""

        A_total, B_total, A_converted, B_converted = (
            self.A_total,
            self.B_total,
            self.A_converted,
            self.B_converted,
        )

        self.diff_std_err = cal_difference_standard_error(
            A_total, B_total, A_converted, B_converted
        )

        return self.diff_std_err

    def null_distribution(self):
        """Generate the distribution for the null hypothesis"""

        self.pooled_std_err()

        return scs.norm(0, self.pld_std_err)

    def alt_distribution(self):
        """Generate the distribution for the null hypothesis"""

        self.conversion_uplift()
        self.pooled_std_err()

        return scs.norm(self.uplift, self.pld_std_err)

    def p_value(self):

        self.conversion_uplift()

        nd = self.null_distribution()
        ad = self.alt_distribution()

        self.p = nd.sf(self.uplift)

    def z_score(self, significance_level=None, two_tailed=None):

        if significance_level is None:
            significance_level = self.p

        if two_tailed is None:
            two_tailed = True

        self.z = cal_z_score(significance_level, two_tailed)

        return self.z

    def report(self, with_data=None, pipeline=None):
        """Run pipeline and generate report"""
        if pipeline is None:
            pipeline = "all"
        if with_data is None:
            with_data = True

        all_pipes = [
            meth
            for meth in dir(self)
            if callable(getattr(self, meth)) and "__" not in meth and meth != "report"
        ]

        for method in all_pipes:
            getattr(self, method)()

        res = {
            "kpi": {"a": self.A_cr, "b": self.B_cr},
            "std_err": {"a": self.A_std_err, "b": self.B_std_err},
            "pooled_std_err": self.pld_std_err,
            "probability": self.probability,
            "uplift": self.uplift,
            "p_value": self.p,
            "z_score": self.z,
            "diff_std_err": self.diff_std_err,
        }

        if self.name:
            res["name"] = self.name
        if with_data:
            res["data"] = self.data

        return res


class ABTestSeries:
    def __init__(self, ab_test_data, kpi_method=None, test_name=None):

        if test_name:
            self.name = test_name
        else:
            self.name = None

        self.data = ab_test_data
        self.A_series = ab_test_data.get("A_series")
        self.B_series = ab_test_data.get("B_series")

        self.A_total = len(self.A_series)
        self.B_total = len(self.B_series)

        if kpi_method is None:
            self.kpi_method = "sum"
        else:
            self.kpi_method = kpi_method

        if self.kpi_method == "sum":
            self.A_converted = np.sum(self.A_series)
            self.B_converted = np.sum(self.B_series)
        elif self.kpi_method == "count":
            self.A_converted = np.count_nonzero(self.A_series)
            self.B_converted = np.count_nonzero(self.B_series)
        elif self.kpi_method == "non_zero_avg":
            self.A_converted = np.sum(self.A_series) / np.count_nonzero(self.A_series)
            self.B_converted = np.sum(self.B_series) / np.count_nonzero(self.B_series)
        elif self.kpi_method == "all_avg":
            self.A_converted = np.sum(self.A_series) / len(self.A_series)
            self.B_converted = np.sum(self.B_series) / len(self.B_series)

    def kpi(self):
        """Conversion rate for a specific group"""

        if self.kpi_method == "count":
            self.A_kpi = cal_conversion_rate(self.A_total, self.A_converted)
            self.B_kpi = cal_conversion_rate(self.B_total, self.B_converted)
        else:
            self.A_kpi = self.A_converted
            self.B_kpi = self.B_converted

        return self.A_kpi, self.B_kpi

    def standard_error(self):
        """standard error"""

        self.A_std_err = cal_standard_error(self.A_total, self.A_converted)
        self.B_std_err = cal_standard_error(self.B_total, self.B_converted)

        return self.A_std_err, self.B_std_err

    def kpi_uplift(self):
        """Uplift in conversion rate

        Relative uplift is the relative conversion rate difference between the test groups
        """

        self.uplift = (self.B_kpi - self.A_kpi) / self.A_kpi

        return self.uplift

    def p_value(self):
        """"""

        self.kpi()

        self.p = cal_p_value(self.data, test="mannwhitney")

        return self.p

    def report(self, with_data=None, pipeline=None):
        """Run pipeline and"""
        if pipeline is None:
            pipeline = "all"
        if with_data is None:
            with_data = True

        all_pipes = [
            meth
            for meth in dir(self)
            if callable(getattr(self, meth)) and "__" not in meth and meth != "report"
        ]

        for method in all_pipes:
            getattr(self, method)()

        res = {
            "kpi": {"a": self.A_kpi, "b": self.B_kpi},
            "std_err": {"a": self.A_std_err, "b": self.B_std_err},
            "uplift": self.uplift,
            "p_value": self.p,
        }

        if self.name:
            res["name"] = self.name
        if with_data:
            res["data"] = self.data

        return res


if __name__ == "__main__":

    one_ab_test = {
        "A_converted": 43,
        "A_total": 17207,
        "B_converted": 68,
        "B_total": 17198,
    }

    print(cal_p_value(one_ab_test))

    dd = ABTestRatios(one_ab_test)
    ab_naive = ABTestRatiosNaive(one_ab_test)

    print("Ratios:\n", dd.report())

    print("Naive Method:\n", ab_naive.report())

    print(dd.data)
    print(cal_p_value(dd.data))

    another_ab_test = {
        "A_series": np.random.choice([1, 0], size=(1000,), p=[0.07, 1 - 0.07]),
        "B_series": np.random.choice([1, 0], size=(1100,), p=[0.1, 1 - 0.1]),
    }

    mw = ABTestSeries(another_ab_test)

    # print(
    #     mw.A_total,
    #     mw.A_converted,
    #     mw.B_total,
    #     mw.B_converted,
    # )

    print(mw.report(with_data=False))

    print("END")
