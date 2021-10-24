import matplotlib.pyplot as plt
import seaborn as sns


def count_plot_with_percentage(dataframe, column, ax=None):
    if ax is None:
        fig, ax = plt.subplots()

    total_counts = len(dataframe)
    vc = dataframe[column].value_counts()
    vc_fraction = vc / total_counts

    sns.countplot(x=dataframe[column], ax=ax, order=vc.index)

    for p in ax.patches:
        x = p.get_bbox().get_points()[:, 0]
        y = p.get_bbox().get_points()[1, 1]
        ax.annotate(
            f"{y:0.0f} ({100.*y/total_counts:.1f}%)",
            (x.mean(), y),
            ha="center",
            va="bottom",
        )

    return ax
