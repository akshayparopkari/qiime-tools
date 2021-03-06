#!/usr/bin/env python
"""
Abstract: This script calculates and returns LDA plots based on normalized relative
          abundances or distance matrices (for e.g. unifrac distance matrix).
"""

import sys
import argparse
from itertools import cycle
from phylotoast import util, biom_calc as bc, graph_util as gu
errors = []
try:
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    mpl.rc("font", family="Arial")  # define font for figure text
except ImportError as ie:
    errors.append(ie)
try:
    import numpy as np
except ImportError as ie:
    errors.append(ie)
try:
    import pandas as pd
except ImportError as ie:
    errors.append(ie)
try:
    import biom
except ImportError as ie:
    errors.append(ie)
try:
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA
except ImportError as ie:
    errors.append(ie)
try:
    from palettable.colorbrewer.qualitative import Set3_12
except ImportError as ie:
    errors.append("No module named palettable")
if len(errors) != 0:
    for item in errors:
        print("Import Error:", item)
    sys.exit()


def plot_LDA(X_lda, y_lda, class_colors, exp_var, style, fig_size, label_pad,
             font_size, sids, dim=2, zangles=None, pt_size=250, out_fp=""):
    """
    Plot transformed LDA data.
    """
    cats = class_colors.keys()
    fig = plt.figure(figsize=fig_size)
    if dim == 3:
        try:
            assert X_lda.shape[1] >= 3
        except AssertionError:
            sys.exit("\nLinear Discriminant Analysis requires at least 4 groups of "
                     "samples to create a 3D figure. Please update group information or "
                     "use the default 2D view of the results.\n")
        if sids is not None:
            print("\nPoint annotations are available only for 2D figures.\n")
        ax = fig.add_subplot(111, projection="3d")
        ax.view_init(elev=zangles[1], azim=zangles[0])
        try:
            ax.set_zlabel("LD3 (Percent Explained Variance: {:.3f}%)".
                          format(exp_var[2]*100), fontsize=font_size, labelpad=label_pad)
        except:
            ax.set_zlabel("LD3", fontsize=font_size, labelpad=label_pad)
        for i, target_name in zip(range(len(cats)), cats):
            cat_x = X_lda[:, 0][y_lda == target_name]
            cat_y = X_lda[:, 1][y_lda == target_name]
            cat_z = X_lda[:, 2][y_lda == target_name]
            ax.scatter(xs=cat_x, ys=cat_y, zs=cat_z, label=target_name,
                       c=class_colors[target_name], alpha=0.85, s=pt_size, edgecolors="k",
                       zdir="z")
    else:
        ax = fig.add_subplot(111)
        for i, target_name in zip(range(len(cats)), cats):
            cat_x = X_lda[:, 0][y_lda == target_name]
            if X_lda.shape[1] == 1:
                cat_y = np.ones((cat_x.shape[0], 1)) + i
            else:
                cat_y = X_lda[:, 1][y_lda == target_name]
            ax.scatter(x=cat_x, y=cat_y, label=target_name, alpha=0.85, s=pt_size,
                       color=class_colors[target_name], edgecolors="k")
        # Annotate data points with sample IDs
        if sids is not None:
            for sample, point, group in zip(sids, X_lda, y_lda):
                try:
                    assert len(point) >= 2
                except AssertionError:
                    point = (point[0], cats.index(group)+1)
                finally:
                    ax.annotate(s=sample, xy=point[:2], xytext=(0, -15), ha="center",
                                va="center", textcoords="offset points")
    if X_lda.shape[1] == 1:
        plt.ylim((0.5, 2.5))
    try:
        ax.set_xlabel("LD1 (Percent Explained Variance: {:.3f}%)".
                      format(exp_var[0]*100), fontsize=font_size, labelpad=label_pad)
    except:
        ax.set_xlabel("LD1", fontsize=font_size, labelpad=label_pad)
    try:
        ax.set_ylabel("LD2 (Percent Explained Variance: {:.3f}%)".
                      format(exp_var[1]*100), fontsize=font_size, labelpad=label_pad)
    except:
        ax.set_ylabel("LD2", fontsize=font_size, labelpad=label_pad)

    leg = plt.legend(loc="best", scatterpoints=3, frameon=True, framealpha=1, fontsize=15)
    leg.get_frame().set_edgecolor('k')
    if dim == 2 and style:
        gu.ggplot2_style(ax)
        fc = "0.8"
    else:
        fc = "none"

    # save or display result
    if out_fp:
        plt.savefig(out_fp, facecolor=fc, edgecolor="none", dpi=300, bbox_inches="tight",
                    pad_inches=0.1)
    else:
        plt.show()


def run_LDA(df):
    """
    Run LinearDiscriminantAnalysis on input dataframe (df) and return
    transformed data, scalings and explained variance by discriminants.
    """
    # Prep variables for sklearn LDA
    X = df.iloc[:, 1:df.shape[1]].values     # input data matrix
    y = df["Condition"].values               # data categories list

    # Calculate LDA
    sklearn_lda = LDA()
    X_lda_sklearn = sklearn_lda.fit_transform(X, y)
    try:
        exp_var = sklearn_lda.explained_variance_ratio_
    except AttributeError as ae:
        print("\n{}: explained variance cannot be computed.\nPlease check this GitHub PR:"
              " https://github.com/scikit-learn/scikit-learn/pull/6027".format(ae))
        return X_lda_sklearn, y, "NA"
    return X_lda_sklearn, y, exp_var


def handle_program_options():
    parser = argparse.ArgumentParser(description="This script calculates and returns LDA "
                                                 "plots based on normalized relative "
                                                 "abundances or distance matrices "
                                                 "(for e.g. unifrac distance matrix).")
    parser.add_argument("-m", "--map_fp", required=True,
                        help="Metadata mapping file. [REQUIRED]")
    parser.add_argument("-g", "--group_by", required=True,
                        help="A column name in the mapping file containing categorical "
                             "values that will be used to identify groups. Each sample "
                             "ID must have a group entry. Default is no categories and "
                             "all the data will be treated as a single group. [REQUIRED]")
    parser.add_argument("-c", "--colors",
                        help="A column name in the mapping file containing hexadecimal "
                             "(#FF0000) color values that will be used to color the "
                             "groups. Each sample ID must have a color entry.")
    parser.add_argument("-ot", "--otu_table", help="Input biom file format OTU table.")
    parser.add_argument("-dm", "--dist_matrix_file", help="Input distance matrix file.")
    parser.add_argument("--save_lda_input",
                        help="Save a CSV-format file of the transposed LDA-input table to"
                             " the file specifed by this option.")
    parser.add_argument("--plot_title", default=None,
                        help="Plot title. Default is no title.")
    parser.add_argument("-o", "--out_fp", default="",
                        help="The path and file name to save the LDA plot under. If "
                             "specified, the figure will be saved directly instead of "
                             "opening a window in which the plot can be viewed before "
                             "saving.")
    parser.add_argument("-d", "--dimensions", default=2, type=int, choices=[2, 3],
                        help="Choose whether to plot 2D or 3D. Default is a 2D view.")
    parser.add_argument("-s", "--point_size", default=100, type=int,
                        help="Specify the size of the circles representing each of the "
                        "samples in the plot")
    parser.add_argument("--z_angles", type=float, nargs=2, default=[45., 30.],
                        help="Specify the azimuth and elevation angles for a 3D plot.")
    parser.add_argument("--figsize", default=[14, 8], type=int, nargs=2,
                        help="Specify the 'width height' in inches for LDA plots. Default"
                        " figure size is 14x8 inches.")
    parser.add_argument("--font_size", default=12, type=int,
                        help="Sets the font size for text elements in the plot.")
    parser.add_argument("--label_padding", default=15, type=int,
                        help="Sets the spacing in points between the each axis and its "
                        "label.")
    parser.add_argument("--annotate_points", action="store_true",
                        help="If specified, each data point will be labeled with its "
                        "sample ID. Default is False.")
    parser.add_argument("--ggplot2_style", action="store_true",
                        help="Apply ggplot2 styling to the figure. Default is False.")
    return parser.parse_args()


def main():
    args = handle_program_options()

    # Parse and read mapping file
    try:
        header, imap = util.parse_map_file(args.map_fp)
        category_idx = header.index(args.group_by)
    except IOError as ioe:
        err_msg = "\nError in metadata mapping filepath (-m): {}\n"
        sys.exit(err_msg.format(ioe))

    # Obtain group colors
    try:
        assert args.colors is not None
    except AssertionError:
        categories = {v[category_idx] for k, v in imap.items()}
        color_cycle = cycle(Set3_12.hex_colors)
        class_colors = {c: color_cycle.next() for c in categories}
    else:
        class_colors = util.color_mapping(imap, header, args.group_by, args.colors)

    if args.dist_matrix_file:
        try:
            dm_data = pd.read_csv(args.dist_matrix_file, sep="\t", index_col=0)
        except IOError as ioe:
            err_msg = "\nError with unifrac distance matrix file (-d): {}\n"
            sys.exit(err_msg.format(ioe))
        dm_data.insert(0, "Condition", [imap[str(sid)][category_idx] for sid in dm_data.index])
        if args.annotate_points:
            sampleids = [str(sid) for sid in dm_data.index]
        else:
            sampleids = None
        if args.save_lda_input:
            dm_data.to_csv(args.save_lda_input, sep="\t")
        # Run LDA
        X_lda, y_lda, exp_var = run_LDA(dm_data)
    else:
        # Load biom file and calculate relative abundance
        try:
            biomf = biom.load_table(args.otu_table)
        except IOError as ioe:
            err_msg = "\nError with biom format file (-d): {}\n"
            sys.exit(err_msg.format(ioe))
        # Get normalized relative abundances
        rel_abd = bc.relative_abundance(biomf)
        rel_abd = bc.arcsine_sqrt_transform(rel_abd)
        df_rel_abd = pd.DataFrame(rel_abd).T
        df_rel_abd.insert(0, "Condition", [imap[sid][category_idx]
                                           for sid in df_rel_abd.index])
        if args.annotate_points:
            sampleids = df_rel_abd.index
        else:
            sampleids = None
        if args.save_lda_input:
            df_rel_abd.to_csv(args.save_lda_input, sep="\t")
        # Run LDA
        X_lda, y_lda, exp_var = run_LDA(df_rel_abd)

    # Plot LDA
    if args.dimensions == 3:
        plot_LDA(X_lda, y_lda, class_colors, exp_var, style=args.ggplot2_style,
                 fig_size=args.figsize, label_pad=args.label_padding,
                 font_size=args.font_size, sids=sampleids, dim=3,
                 zangles=args.z_angles, pt_size=args.point_size, out_fp=args.out_fp)
    else:
        plot_LDA(X_lda, y_lda, class_colors, exp_var, style=args.ggplot2_style,
                 fig_size=args.figsize, label_pad=args.label_padding,
                 font_size=args.font_size, sids=sampleids, pt_size=args.point_size,
                 out_fp=args.out_fp)


if __name__ == "__main__":
    sys.exit(main())
