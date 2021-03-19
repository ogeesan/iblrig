#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Niccolò Bonacchi
# @Date:   2018-02-20 14:46:10
# matplotlib.use('Qt5Agg')
import argparse
import time
from pathlib import Path

import alf.folders
import ibllib.io.raw_data_loaders as raw
import matplotlib.pyplot as plt
import numpy as np
from ibllib.io.extractors.ephys_fpga import ProbaContrasts


def load_raw_session(fpath):
    session_path = alf.folders.session_path(fpath)
    if session_path is None:
        print("Session path is None, can't load anything...")
        return
    data = raw.load_data(session_path, time="raw")
    sett = raw.load_settings(session_path)
    stim_vars = ProbaContrasts.get_pregenerated_events(data, sett)
    return data, sett, stim_vars


def make_fig(sett):
    plt.ion()
    f = plt.figure(figsize=(20,10))  # figsize=(19.2, 10.8), dpi=100)
    ax_bars = plt.subplot2grid((2, 2), (0, 0), rowspan=1, colspan=1)
    ax_psych = plt.subplot2grid((2, 2), (0, 1), rowspan=1, colspan=1)
    ax_chron = plt.subplot2grid((2, 2), (1, 0), rowspan=1, colspan=1)
    ax_vars = plt.subplot2grid((2, 2), (1, 1), rowspan=1, colspan=1)
    ax_vars2 = ax_vars.twinx()
    #     plt.show()

    f.suptitle(
        f"{sett['PYBPOD_SUBJECTS'][0]} - {sett['SUBJECT_WEIGHT']}gr - {sett['SESSION_DATETIME']}"
    )  # noqa
    # f.tight_layout()
    axes = (ax_bars, ax_psych, ax_chron, ax_vars, ax_vars2)
    f.canvas.flush_events()
    return (f, axes)


def update_fig(f, axes, data_file_path):
    ax_bars, ax_psych, ax_chron, ax_vars, ax_vars2 = axes

    data, sett, stim_vars = load_raw_session(data_file_path)
    bar_data = get_barplot_data(data)
    psych_data = get_psych_data(data, stim_vars)
    chron_data = get_chron_data(data, sett, stim_vars)
    vars_data = get_vars_data(data)

    plot_bars(bar_data, ax=ax_bars)
    plot_psych(psych_data, ax=ax_psych)
    plot_chron(chron_data, ax=ax_chron)
    plot_vars(vars_data, ax=ax_vars, ax2=ax_vars2)

    f.canvas.flush_events()

    # mgr = mgr = plt.get_current_fig_manager()
    # pos = mgr.window.geometry().getRect()
    # size = f.get_size_inches()

    # f.set_visible(False)
    # f.set_size_inches(18,10)
    # f.set_visible(True)
    fname = Path(data_file_path).parent / "online_plot.png"
    f.savefig(fname, dpi=100)
    # mgr.window.setGeometry(*pos)
    # f.set_size_inches(size)


def get_barplot_data(data):
    out = {}
    out["trial_num"] = data[-1]["trial_num"]
    out["block_num"] = data[-1]["block_num"]
    out["block_trial_num"] = data[-1]["block_trial_num"]
    out["block_len"] = data[-1]["block_len"]
    out["ntrials_correct"] = data[-1]["ntrials_correct"]
    out["ntrials_err"] = out["trial_num"] - out["ntrials_correct"]
    out["water_delivered"] = np.round(data[-1]["water_delivered"], 3)
    out["time_from_start"] = data[-1]["elapsed_time"]
    out["stim_pl"] = data[-1]["stim_probability_left"]
    return out


def _get_response_side_buffer(data):
    correct = ~np.isnan([x["behavior_data"]["States timestamps"]["correct"][0][0] for x in data])
    error = ~np.isnan([x["behavior_data"]["States timestamps"]["error"][0][0] for x in data])
    no_go = ~np.isnan([x["behavior_data"]["States timestamps"]["no_go"][0][0] for x in data])

    np.all(np.bitwise_or(np.bitwise_or(correct, error), no_go))

    position = np.array([x["position"] for x in data])
    response_side_buffer = np.zeros(len(data)) * np.nan
    response_side_buffer[
        np.bitwise_or(np.bitwise_and(correct, position < 0), np.bitwise_and(error, position > 0))
    ] = 1
    response_side_buffer[
        np.bitwise_or(np.bitwise_and(correct, position > 0), np.bitwise_and(error, position < 0))
    ] = -1
    response_side_buffer[no_go] = 0

    return response_side_buffer


def get_psych_data(data, stim_vars):
    sig_contrasts_all = np.array(data[-1]["contrast_set"])
    sig_contrasts_all = np.append(sig_contrasts_all, [-x for x in sig_contrasts_all if x != 0])
    sig_contrasts_all = np.sort(sig_contrasts_all)

    signed_contrast_buffer = np.array([tr["signed_contrast"] for tr in data])

    response_side_buffer = _get_response_side_buffer(data)

    stim_probability_left_buffer = stim_vars["probabilityLeft"]

    def get_prop_ccw_resp(stim_prob_left):
        ntrials_ccw = np.array(
            [
                sum(
                    response_side_buffer[
                        (stim_probability_left_buffer == stim_prob_left)
                        & (signed_contrast_buffer == x)
                    ]
                    < 0
                )
                for x in sig_contrasts_all
            ]
        )
        ntrials = np.array(
            [
                sum(
                    (signed_contrast_buffer == x)
                    & (stim_probability_left_buffer == stim_prob_left)
                )
                for x in sig_contrasts_all
            ]
        )
        prop_resp_ccw = [x / y if y != 0 else 0 for x, y in zip(ntrials_ccw, ntrials)]
        return prop_resp_ccw

    prop_resp_ccw02 = get_prop_ccw_resp(0.2)
    prop_resp_ccw05 = get_prop_ccw_resp(0.5)
    prop_resp_ccw08 = get_prop_ccw_resp(0.8)

    return sig_contrasts_all, prop_resp_ccw02, prop_resp_ccw05, prop_resp_ccw08


def get_chron_data(data, sett, stim_vars):
    sig_contrasts_all = sett["CONTRAST_SET"]
    sig_contrasts_all.extend([-x for x in sig_contrasts_all])
    sig_contrasts_all = np.sort(sig_contrasts_all)

    signed_contrast_buffer = np.array([tr["signed_contrast"] for tr in data])

    response_time_buffer = np.array(
        [
            x["behavior_data"]["States timestamps"]["closed_loop"][0][1]
            - x["behavior_data"]["States timestamps"]["stim_on"][0][0]
            for x in data
        ]
    )

    stim_probability_left_buffer = stim_vars["probabilityLeft"]

    def get_rts(stim_prob_left):
        rts = [
            np.median(
                response_time_buffer[
                    (signed_contrast_buffer == x)
                    & (stim_probability_left_buffer == stim_prob_left)
                ]
            )
            for x in sig_contrasts_all
        ]
        rts = [x if not np.isnan(x) else 0 for x in rts]
        return rts

    rts02, rts05, rts08 = get_rts(0.2), get_rts(0.5), get_rts(0.8)

    return sig_contrasts_all, rts02, rts05, rts08


def get_vars_data(data):
    response_time_buffer = np.array(
        [
            x["behavior_data"]["States timestamps"]["closed_loop"][0][1]
            - x["behavior_data"]["States timestamps"]["stim_on"][0][0]
            for x in data
        ]
    )

    out = {}
    out["median_rt"] = np.median(response_time_buffer) * 1000
    out["prop_correct"] = data[-1]["ntrials_correct"] / data[-1]["trial_num"]
    out["Temperature_C"] = data[-1]["as_data"]["Temperature_C"]
    out["AirPressure_mb"] = data[-1]["as_data"]["AirPressure_mb"]
    out["RelativeHumidity"] = data[-1]["as_data"]["RelativeHumidity"]
    return out


# plotters


def plot_bars(bar_data, ax=None):
    if ax is None:
        # f = plt.figure()  # figsize=(19.2, 10.8), dpi=100)
        ax = plt.subplot2grid((1, 1), (0, 0), rowspan=1, colspan=1)
    ax.cla()

    width = 0.5
    xlabels = [
        "Water\nDelivered\n(µl)",
        "Trial\nOutcome",
        "Current\nBlock",
        "Session\nDuration",
    ]
    x = range(len(xlabels))  # the x locations for the groups
    #############################################################
    ax.barh(3, 0, width, color="black")
    # ax.barh(0, bar_data['trial_num'], width, color="gray")
    ax.text(
        1,
        3,
        str(bar_data["time_from_start"]),
        color="black",
        fontweight="bold",
        size="x-large",
    )
    #############################################################
    if bar_data["stim_pl"] == 0.2:
        clr = "green"
    elif bar_data["stim_pl"] == 0.5:
        clr = "black"
    elif bar_data["stim_pl"] == 0.8:
        clr = "blue"
    ax.barh(2, bar_data["block_len"], width, color=clr, label="Block Length")
    ax.barh(
        2,
        bar_data["block_trial_num"],
        width,
        color="gray",
        label="Trials in current block",
    )
    ax.barh(
        2,
        bar_data["block_num"],
        width,
        left=bar_data["block_len"],
        color="orange",
        label="Block number",
    )

    ax.text(
        1,
        2.26,  # bar_data['block_len'] + bar_data['block_num'] +
        "{} / {} of block #{}".format(
            bar_data["block_trial_num"], bar_data["block_len"], bar_data["block_num"]
        ),
        color="black",
        fontweight="bold",
        size="x-large",
    )
    #############################################################
    ax.barh(1, bar_data["ntrials_correct"], width, color="green", label="Correct")
    ax.barh(
        1,
        bar_data["ntrials_err"],
        width,
        left=bar_data["ntrials_correct"],
        color="red",
        label="Error",
    )

    left = 0
    ax.text(
        left + 1,
        1.26,
        str(bar_data["ntrials_correct"]),
        color="green",
        fontweight="bold",
        size="x-large",
    )
    left += bar_data["ntrials_correct"]
    ax.text(
        left + 1,
        1.26,  # - (bar_data['ntrials_err'] / 2)
        str(bar_data["ntrials_err"]),
        color="red",
        fontweight="bold",
        size="x-large",
    )
    left += bar_data["ntrials_err"]
    ax.text(
        left + 1,
        1,
        str(bar_data["ntrials_correct"] + bar_data["ntrials_err"]),
        color="black",
        fontweight="bold",
        size="x-large",
    )

    #############################################################
    ax.barh(0, bar_data["water_delivered"], width, color="blue")
    ax.text(
        1,
        0.26,  # bar_data['water_delivered'] +
        str(bar_data["water_delivered"]),
        color="blue",
        fontweight="bold",
        size="x-large",
    )
    #############################################################

    ax.set_yticks([i for i in x])
    ax.set_yticklabels(xlabels, minor=False)
    # ax.set_xlim([0, 100])
    ax.legend()
    ax.figure.canvas.draw_idle()


def plot_psych(psych_data, ax=None):
    if ax is None:
        # f = plt.figure()  # figsize=(19.2, 10.8), dpi=100)
        ax = plt.subplot2grid((1, 1), (0, 0), rowspan=1, colspan=1)
    ax.cla()

    x = psych_data[0]
    y02 = psych_data[1]
    y05 = psych_data[2]
    y08 = psych_data[3]

    ax.plot(x, y05, c="k", label="CCW responses 50/50", marker="o", ls="-", alpha=0.5)
    ax.plot(x, y02, c="g", label="CCW responses 20/80", marker="o", ls="-")
    ax.plot(x, y08, c="b", label="CCW responses 80/20", marker="o", ls="-")

    ax.axhline(0.5, color="gray", ls="--", alpha=0.5)
    ax.axvline(0.0, color="gray", ls="--", alpha=0.5)
    ax.set_ylim([-0.1, 1.1])
    ax.legend(loc="best")
    ax.grid()
    ax.figure.canvas.draw_idle()
    return


def plot_chron(chron_data, ax=None):
    if ax is None:
        # f = plt.figure()  # figsize=(19.2, 10.8), dpi=100)
        ax = plt.subplot2grid((1, 1), (0, 0), rowspan=1, colspan=1)
    ax.cla()

    x = chron_data[0]
    y02 = chron_data[1]
    y05 = chron_data[2]
    y08 = chron_data[3]

    ax.plot(x, y05, c="k", label="Median response time 50/50", marker="o", ls="-", alpha=0.5)
    ax.plot(x, y02, c="g", label="Median response time 20/80", marker="o", ls="-")
    ax.plot(x, y08, c="b", label="Median response time 80/20", marker="o", ls="-")

    ax.axhline(0.5, color="gray", ls="--", alpha=0.5)
    ax.axvline(0.0, color="gray", ls="--", alpha=0.5)
    ax.legend(loc="best")
    ax.grid()
    ax.figure.canvas.draw_idle()
    return


def plot_vars(vars_data, ax=None, ax2=None):
    if ax is None:
        # f = plt.figure()  # figsize=(19.2, 10.8), dpi=100)
        ax = plt.subplot2grid((1, 1), (0, 0), rowspan=1, colspan=1)
        ax2 = ax.twinx()
    if ax2 is None:
        ax2 = ax.twinx()

    ax.cla()
    ax2.cla()

    # ax.figure.tight_layout()  # or right y-label is slightly clipped
    width = 0.5

    x = [0, 1, 2, 3, 4]
    median_rt = vars_data["median_rt"] / 10
    prop_correct = vars_data["prop_correct"]
    temp = vars_data["Temperature_C"]
    rel_hum = vars_data["RelativeHumidity"] / 100

    ax.bar(x[0], median_rt, width, color="cyan", label="Median RT (10^1ms)")
    ax.bar(x[1], temp, width, color="magenta", label="Temperature (ºC)")

    ax2.bar(x[3], rel_hum, width, color="yellow", label="Relative humidity")
    ax2.bar(x[4], prop_correct, width, color="black", label="Proportion correct")
    ax2.set_ylim([0, 1.1])
    ax.legend(loc="lower left")
    ax2.legend(loc="lower right")
    ax.figure.canvas.draw_idle()
    ax2.figure.canvas.draw_idle()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot ongoing session")
    parser.add_argument("folder", help="Session folder")
    args = parser.parse_args()
    print(args.folder)

    data, sett, stim_vars = load_raw_session(args.folder)
    f, axes = make_fig(sett)

    init = round(time.time(), 1)
    while True:
        f.canvas.flush_events()
        if round(round((round(time.time(), 1) - init), 1) % 1.5, 1) == 0:
            update_fig(f, axes, args.folder)

    #ephys
    fpath = "/home/nico/Downloads/FlatIron/mainenlab/Subjects/ZM_3003/2020-07-30/001/raw_behavior_data/_iblrig_taskData.raw.jsonable"
    fpath = r"C:\iblrig_data\Subjects\ZM_3003\2020-07-27\001"
    pl = subprocess.Popen(["python", r".\iblrig\online_plots.py", r"C:\iblrig_data\Subjects\ZM_3003\2020-07-27\001"])
    pl.kill()
    pl.terminate()
    #biased

    #training
    # Get data file properties, if changed update figure
