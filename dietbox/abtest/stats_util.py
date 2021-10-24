import numpy as np
import scipy.stats as scs


def cal_conversion_rate(X_total, X_converted):
    """Conversion rate for a specific group"""

    X_cr = X_converted / X_total if X_total != 0 else 0

    return X_cr


def cal_standard_error(X_total, X_converted):
    """standard error"""

    X_cr = cal_conversion_rate(X_total, X_converted)

    return np.sqrt(X_cr * (1 - X_cr) / X_total)


def cal_difference_standard_error(A_total, B_total, A_converted, B_converted):
    """Standard error of the difference for the AB test"""
    A_se = cal_standard_error(A_total, A_converted)
    B_se = cal_standard_error(B_total, B_converted)

    return np.sqrt(A_se ** 2 + B_se ** 2)


def cal_conversion_uplift(A_total, B_total, A_converted, B_converted):
    """Uplift in conversion rate

    Relative uplift is the relative conversion rate difference between the test groups
    """

    try:
        the_uplift = (
            cal_conversion_rate(B_total, B_converted)
            - cal_conversion_rate(A_total, A_converted)
        ) / cal_conversion_rate(A_total, A_converted)
    except Exception as ee:
        raise Exception(ee)

    return the_uplift


def cal_pooled_probability(A_total, B_total, A_converted, B_converted):
    """Pooled probability for two samples

    This is better used as an intermediate value.
    """

    probability = (A_converted + B_converted) / (A_total + B_total)

    return probability


def cal_pooled_std_err(pooled_prob_inp, A_total, B_total):
    """Pooled standard error for two samples

    For more information about the definition, refer to wikipedia:
    https://en.wikipedia.org/wiki/Pooled_variance
    """

    # Pooled standard error
    pp = pooled_prob_inp
    pld_std_err = np.sqrt(pp * (1 - pp) * (1 / A_total + 1 / B_total))

    return pld_std_err


def cal_z_score(significance_level=None, two_tailed=None):
    """z score

    z score requires at least one parameter which is the significance level.
    By default, significance level for this function is assumed to be 0.05.

    It is better that the user read this Nature article before using this function:
    https://www.nature.com/articles/d41586-019-00857-9
    """

    if significance_level is None:
        significance_level = 0.05

    if two_tailed is None:
        two_tailed = True

    ## construct a z distribution
    z_distribution = scs.norm()

    if two_tailed:
        significance_level = significance_level / 2
        no_rejection_level = 1 - significance_level
    else:
        no_rejection_level = 1 - significance_level

    ## generate z distribution
    z_score = z_distribution.ppf(no_rejection_level)

    return z_score


def cal_confidence_interval(sample_mean=0, sample_std=1, sample_size=1, sig_level=0.05):
    """Confidence interval assuming normal distribution

    Based the z score.
    Reference: https://www.statisticshowto.datasciencecentral.com/probability-and-statistics/confidence-interval/
    """

    z = cal_z_score(sig_level)

    left = sample_mean - z * sample_std / np.sqrt(sample_size)
    right = sample_mean + z * sample_std / np.sqrt(sample_size)

    return (left, right)


def cal_p_value(data, test=None):
    """p-value for the ratio test"""

    if test is None:
        test = "binom"

    if test == "binom":
        A_total, B_total, A_converted, B_converted = (
            data.get("A_total"),
            data.get("B_total"),
            data.get("A_converted"),
            data.get("B_converted"),
        )
        if data.get("A_cr") and data.get("B_cr"):
            p_A = data.get("A_cr")
            p_B = data.get("B_cr")
        else:
            p_A = cal_conversion_rate(A_total, A_converted)
            p_B = cal_conversion_rate(B_total, B_converted)
        return scs.binom_test(B_converted, n=B_total, p=p_A, alternative="greater")
        # return scs.binom(A_total, p_A).sf(B_total * p_B)
    elif test == "mannwhitney":
        A_data, B_data = data.get("A_series"), data.get("B_series")
        _, test_mannwhitney_p_value = scs.mannwhitneyu(x=A_data, y=B_data)

        return test_mannwhitney_p_value


def ab_dist(stderr, d_hat=0, group_type="control"):
    """Function from
    https://towardsdatascience.com/the-math-behind-a-b-testing-with-example-code-part-1-of-2-7be752e1d06f
    Distribution object depending on group type

    Examples:

    Parameters:
        stderr (float): pooled standard error of two independent samples
        d_hat (float): the mean difference between two independent samples
        group_type (string): 'control' and 'test' are supported

    Returns:
        dist (scipy.stats distribution object)
    """
    if group_type == "control":
        sample_mean = 0

    elif group_type == "test":
        sample_mean = d_hat

    # create a normal distribution which is dependent on mean and std dev
    dist = scs.norm(sample_mean, stderr)

    return dist


if __name__ == "__main__":

    print(cal_z_score())

    print("END")
