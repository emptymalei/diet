import numpy as np
from dietbox.abtest.stats_util import cal_p_value
from dietbox.abtest.stats import ABTestRatios, ABTestRatiosNaive, ABTestSeries


def test_ab_tests():

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

    print(mw.report(with_data=False))
