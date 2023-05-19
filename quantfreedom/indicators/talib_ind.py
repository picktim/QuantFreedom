# https://ta-lib.github.io/ta-lib-python/index.html
from itertools import product

import numpy as np
import pandas as pd
import talib
from talib import get_functions
from talib.abstract import Function

from quantfreedom._typing import Array1d
from quantfreedom.indicators.indicators_cls import Indicator
from quantfreedom.plotting.simple_plots import (plot_on_candles_1_chart,
                                                plot_results_candles_and_chart)

# this is an update

def validate(value, ref_name, ref_value):
    if not isinstance(value, list):
        raise ValueError(f"{ref_name} must be a list")

    if not all(isinstance(x, str) for x in value):
        raise ValueError(
            f"{ref_name} your list has to be made up of strings"
        )

    if len(value) != len(ref_value):
        raise ValueError(
            f"{ref_name} your list length must be {len(ref_value)}"
        )
    

def from_talib(
    func_name: str,
    price_data: pd.DataFrame = None,
    indicator_data: pd.DataFrame = None,
    all_possible_combos: bool = False,
    column_wise_combos: bool = False,
    plot_results: bool = False,
    plot_on_data: bool = False,
    input_names: list = None,
    parameters: dict = {},
) -> pd.DataFrame:
    """
    Function Name
    -------------
    from_talib

    Summary
    -------
    Using talib to create indicator data. If you need a list of the indicators visit the talib website https://ta-lib.github.io/ta-lib-python/funcs.html

    Explainer Video
    ---------------
    Coming Soon but if you want/need it now please let me know in discord or telegram and i will make it for you

    ## Variables needed
    Parameters
    ----------
    func_name : str
        the short form name of the function like dema for Double Exponential Moving Average. Please look at https://ta-lib.github.io/ta-lib-python/funcs.html for a list of all the short form function names
    price_data : pd.DataFrame, None
        price data
    indicator_data : pd.DataFrame, None
        indicator data like if you want to put an ema on the rsi you send the rsi indicator data here and ema the for func name
    all_possible_combos : bool, False
        If you want all possible combinations, aka the cartesian product, or not. Example of what the cart product does
        ```
        [1,2]
        [a,b]
        answer: [(1,a), (1,b), (2,a), (2,b)]
        ```
    column_wise_combos : bool, False
        Standard column wise combos. An example is
        ```
        [1,2,3]
        [a,b,c]
        answer: [(1,a), (2,b), (3,c)]
        ```

    ## Function returns
    Returns
    -------
    pd.DataFrame
        Pandas Dataframe of indicator values
    """

    pd_index = indicator_data.index if indicator_data else price_data.index

    users_args_list = []
    biggest = 1
    indicator_info = Function(func_name).info
    output_names = indicator_info["output_names"]
    ind_params = list(indicator_info["parameters"].keys())
    ind_name = indicator_info["name"]


    if indicator_info.get("parameters"):
        indicator_info["parameters"].update(parameters)

    if biggest == 1 and (column_wise_combos or all_possible_combos):
        raise ValueError(
            f"You have to have a list for paramaters for {ind_params} to use cart product or column_wise_combos"
        )

    elif column_wise_combos:
        final_user_args = []
        for x in users_args_list:
            if x.size == 1:
                final_user_args.append(np.broadcast_to(x, biggest))
            else:
                final_user_args.append(x)
        final_user_args = tuple(final_user_args)

    elif all_possible_combos:
        final_user_args = np.array(list(product(*users_args_list))).T

    else:
        final_user_args = tuple(users_args_list)

    ind_settings_tup = ()
    pd_multind_tuples = ()
    ind_setings_len = final_user_args[0].size
    output_names_len = len(output_names)

    # sending price data as your data to work with
    if price_data is not None:
        symbols = list(price_data.columns.levels[0])
        num_of_symbols = len(symbols)
        final_array = np.empty(
            (price_data.shape[0], ind_setings_len * output_names_len * num_of_symbols)
        )
        counter = 0

        if output_names_len == 1:
            param_keys = [list(price_data.columns.names)[0]] + [
                ind_name + "_" + x for x in ind_params
            ]

            for symbol in symbols:
                temp_price_data_tuple = ()

                for input_name in input_names:
                    temp_price_data_tuple = temp_price_data_tuple + (
                        price_data[symbol][input_name].values,
                    )

                for c in range(ind_setings_len):
                    # x is the array object in the tuple (x,x)
                    for x in final_user_args:
                        if type(x[c]) == np.int_:
                            ind_settings_tup = ind_settings_tup + (int(x[c]),)
                        if type(x[c]) == np.float_:
                            ind_settings_tup = ind_settings_tup + (float(x[c]),)

                    final_array[:, counter] = getattr(talib, func_name.upper())(
                        *temp_price_data_tuple,
                        *ind_settings_tup,
                    )

                    pd_multind_tuples = pd_multind_tuples + (
                        (symbol,) + ind_settings_tup,
                    )

                    ind_settings_tup = ()
                    counter += 1

        elif output_names_len > 1:
            param_keys = (
                [list(price_data.columns.names)[0]]
                + [ind_name + "_output_names"]
                + [ind_name + "_" + x for x in ind_params]
            )

            for symbol in symbols:
                temp_price_data_tuple = ()

                for input_name in input_names:
                    temp_price_data_tuple = temp_price_data_tuple + (
                        price_data[symbol][input_name].values,
                    )

                # these are the names called by the fun like talib('rsi').real - real is the output name
                for out_name_count, out_name in enumerate(output_names):
                    # c is the indicator result of the array within the tuple (array[x], array[x])
                    for c in range(ind_setings_len):
                        # x is the array object in the tuple (x,x)
                        for x in final_user_args:
                            if type(x[c]) == np.int_:
                                ind_settings_tup = ind_settings_tup + (int(x[c]),)
                            if type(x[c]) == np.float_:
                                ind_settings_tup = ind_settings_tup + (float(x[c]),)

                        final_array[:, counter] = getattr(talib, func_name.upper())(
                            *temp_price_data_tuple,
                            *ind_settings_tup,
                        )[out_name_count]

                        pd_multind_tuples = pd_multind_tuples + (
                            (symbol,) + (out_name,) + ind_settings_tup,
                        )

                        ind_settings_tup = ()
                        counter += 1

        else:
            raise ValueError("Something is wrong with the output name length")

    # sending indicator data as the data you want to work with
    elif indicator_data is not None:
        counter = 0
        user_ind_settings = tuple(indicator_data.columns)
        user_ind_values = indicator_data.values
        user_ind_names = list(indicator_data.columns.names)
        user_ind_name = user_ind_names[1].split("_")[0]
        param_keys = [user_ind_name + "_" + ind_name + "_" + x for x in ind_params]
        param_keys = user_ind_names + param_keys
        final_array = np.empty(
            (
                indicator_data.shape[0],
                ind_setings_len * output_names_len * indicator_data.shape[1],
            )
        )
        if output_names_len == 1:
            for col in range(user_ind_values.shape[1]):
                # c is the indicator result of the array within the tuple (array[x], array[x])
                for c in range(ind_setings_len):
                    # x is the array object in the tuple (x,x)
                    for x in final_user_args:
                        if type(x[c]) == np.int_:
                            ind_settings_tup = ind_settings_tup + (int(x[c]),)
                        if type(x[c]) == np.float_:
                            ind_settings_tup = ind_settings_tup + (float(x[c]),)
                    final_array[:, counter] = getattr(talib, func_name.upper())(
                        user_ind_values[:, col],
                        *ind_settings_tup,
                    )

                    pd_multind_tuples = pd_multind_tuples + (
                        user_ind_settings[col] + ind_settings_tup,
                    )

                    counter += 1
                    ind_settings_tup = ()

        elif output_names_len > 1:
            user_ind_col_names = []
            for col_name in list(indicator_data.columns.names):
                user_ind_col_names.append(col_name)
            param_keys = (
                user_ind_col_names
                + [ind_name + "_output_names"]
                + [ind_name + "_" + x for x in ind_params]
            )

            # these are the names called by the fun like talib('rsi').real - real is the output name
            for col in range(user_ind_values.shape[1]):
                for out_name_count, out_name in enumerate(output_names):
                    # c is the indicator result of the array within the tuple (array[x], array[x])
                    for c in range(ind_setings_len):
                        # x is the array object in the tuple (x,x)
                        for x in final_user_args:
                            if type(x[c]) == np.int_:
                                ind_settings_tup = ind_settings_tup + (int(x[c]),)
                            if type(x[c]) == np.float_:
                                ind_settings_tup = ind_settings_tup + (float(x[c]),)

                        final_array[:, counter] = getattr(talib, func_name.upper())(
                            user_ind_values[:, col],
                            *ind_settings_tup,
                        )[out_name_count]

                        pd_multind_tuples = pd_multind_tuples + (
                            user_ind_settings[col] + (out_name,) + ind_settings_tup,
                        )

                        counter += 1
                        ind_settings_tup = ()

        else:
            raise ValueError(
                "Something is wrong with the output name length for user ind data"
            )
    else:
        raise ValueError(
            "Something is wrong with either df price_data or user indicator"
        )
    ta_lib_data = pd.DataFrame(
        final_array,
        index=pd_index,
        columns=pd.MultiIndex.from_tuples(
            tuples=list(pd_multind_tuples),
            names=param_keys,
        ),
    )

    if plot_on_data:
        if price_data is not None:
            plot_on_candles_1_chart(
                ta_lib_data=ta_lib_data,
                price_data=price_data,
            )
    elif plot_results:
        if price_data is not None:
            plot_results_candles_and_chart(
                ta_lib_data=ta_lib_data,
                price_data=price_data,
            )

    ind = Indicator(data=ta_lib_data, name=func_name)
    return ind


def talib_ind_info(func_name: str):
    return Function(func_name).info


def talib_func_list_website_link():
    print("https://ta-lib.github.io/ta-lib-python/funcs.html")


def talib_list_of_indicators():
    return get_functions()