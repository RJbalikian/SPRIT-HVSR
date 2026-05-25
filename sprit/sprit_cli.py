"""This module/script is used to run sprit from the command line. 

The arguments here should correspond to any of the keyword arguments that can be used with sprit.run() (or sprit_hvsr.run()). See the run() function's documentation for more information, or the individual functions that are run within it.

For list inputs, you should pass the argument multiple times(e.g., --report_format "csv" --report_format "print" --report_format "plot"). (In the case of --report_format, you can also just use "all" to get csv, print, and plot report types)

The input_data parameter of input_params() is the only required argument, though for your data processing to work correctly and to be formatted correctly, you may need to pass others as well.
"""

import argparse
import inspect
import numbers 

#try:
#    from sprit import sprit_hvsr
#except Exception:
#    import sprit_hvsr

from . import sprit_hvsr, sprit_plot, sprit_calibration

def get_param_docstring(func, param_name):
    function_docstring = func.__doc__

    # Search for the parameter's docstring within the function's docstring
    param_docstring = None
    if function_docstring:
        param_start = function_docstring.find(f'{param_name} :')
        param_start = param_start + len(f'{param_name} :')
        if param_start != -1:
            param_end_line1 = function_docstring.find('\n', param_start + 1)
            param_end = function_docstring.find('\n', param_end_line1 + 1)
            if param_end != -1:
                param_docstring = function_docstring[param_start:param_end].strip()

    if param_docstring is None:
        param_docstring = ''
    return param_docstring

def main():
    parser = argparse.ArgumentParser(description='CLI for SPRIT HVSR package (specifically the sprit.run() function)')

    hvsrFunctions = [sprit_hvsr.run,
                    sprit_hvsr.input_params,
                     sprit_hvsr.fetch_data,
                     sprit_hvsr.calculate_azimuth,
                     sprit_hvsr.remove_noise,
                     sprit_hvsr.generate_psds,
                     sprit_hvsr.process_hvsr,
                     sprit_hvsr.remove_outlier_curves,
                     sprit_hvsr.check_peaks,
                     sprit_hvsr.get_report,
                     sprit_hvsr.export_json,
                     sprit_hvsr.export_data,
                     sprit_hvsr.export_hvsr,
                     sprit_hvsr.export_report,
                     sprit_hvsr.plot_hvsr,
                     sprit_calibration.calculate_depth,
                     sprit_plot.plot_depth_curve,
                     sprit_plot.plot_text]

    hvsrFunDict = {sprit_hvsr.run: inspect.signature(sprit_hvsr.run).parameters,
                   sprit_hvsr.input_params: inspect.signature(sprit_hvsr.input_params).parameters,
                   sprit_hvsr.fetch_data: inspect.signature(sprit_hvsr.fetch_data).parameters,
                   sprit_hvsr.calculate_azimuth: inspect.signature(sprit_hvsr.calculate_azimuth).parameters,
                   sprit_hvsr.remove_noise: inspect.signature(sprit_hvsr.remove_noise).parameters,
                   sprit_hvsr.generate_psds: inspect.signature(sprit_hvsr.generate_psds).parameters,
                   sprit_hvsr.process_hvsr: inspect.signature(sprit_hvsr.process_hvsr).parameters,
                   sprit_hvsr.remove_outlier_curves: inspect.signature(sprit_hvsr.remove_outlier_curves).parameters,
                   sprit_hvsr.check_peaks: inspect.signature(sprit_hvsr.check_peaks).parameters,
                   sprit_hvsr.get_report: inspect.signature(sprit_hvsr.get_report).parameters,
                   sprit_hvsr.export_json: inspect.signature(sprit_hvsr.export_json).parameters,
                   sprit_hvsr.export_data: inspect.signature(sprit_hvsr.export_data).parameters,
                   sprit_hvsr.export_hvsr: inspect.signature(sprit_hvsr.export_hvsr).parameters,
                   sprit_hvsr.export_report: inspect.signature(sprit_hvsr.export_report).parameters,
                   sprit_plot.plot_depth_curve: inspect.signature(sprit_plot.plot_depth_curve).parameters,
                   sprit_calibration.calculate_depth: inspect.signature(sprit_calibration.calculate_depth).parameters,
                   sprit_hvsr.plot_hvsr: inspect.signature(sprit_hvsr.plot_hvsr).parameters,
                   sprit_plot.plot_text: inspect.signature(sprit_plot.plot_text).parameters,
                   }

    # Get default parameters from main functions
    parameters = []
    for f in hvsrFunctions:
        parameters.append(inspect.signature(f).parameters)

    # Add argument and options to the parser
    intermediate_params_list = ['params', 'input_parameters', 'input', 'hvsr_data', 'hvsr_results']
    storeTrueList = ['noise_removal', 'outlier_curves_removal', 'suppress_report_outputs',
                     'show_pdf_report', 'show_plot_report', 'plot_input_stream', 'remove_response',
                      'show_outlier_plot', 'suppress_report_outputs', 'show_report_outputs',
                        'return_json_string', 'include_dataframe', 'include_plots', 'export_edited_stream','use_subplots',
                         'return_fig', 'show_legend', 'close_figs' ]
    paramNamesList = []
    for i, param in enumerate(parameters):
        for name, parameter in param.items():
            # Add arguments and options here
            if name not in paramNamesList and name not in intermediate_params_list:
                paramNamesList.append(name)
                curr_doc_str = get_param_docstring(func=hvsrFunctions[i], param_name=name)
                if name == 'input_data':
                    parser.add_argument(name, default='sample', help=f'{curr_doc_str}')
                elif name  == 'verbose':
                    parser.add_argument('-v', '--verbose',  action='store_true',
                                        help='Print status and results to terminal.',
                                       default=parameter.default)
                elif name in storeTrueList:
                    parser.add_argument(f'--{name}', action='store_true',
                                        help=helpStr,
                                        default=parameter.default)
                else:
                    helpStr = f'Keyword argument {name} in function sprit.{hvsrFunctions[i].__name__}(). default={parameter.default}.\n\t{curr_doc_str}'
                    parser.add_argument(f'--{name}', help=helpStr, default=parameter.default)

    # Add more arguments/options as needed
    args = parser.parse_args()

    # Map command-line arguments/options to kwargs
    kwargs = {}
    for arg_name, arg_value in vars(args).items():
        if arg_name == 'input_data':
            inData = arg_value

        if isinstance(arg_value, str):
            if "=" in arg_value:
                arg_value = {arg_value.split('=')[0]: arg_value.split('=')[1]}

            if arg_value.lower() == 'true':
                arg_value = True
            elif arg_value.lower() == 'false':
                arg_value = False
            elif arg_value.lower() == 'none':
                arg_value = None
            elif "[" in arg_value:
                arg_value = arg_value.replace('[', '').replace(']', '')
                arg_value = arg_value.split(',')
            elif "," in arg_value:
                arg_value = arg_value.split(',')

        is_default = False
        for k, v in hvsrFunDict.items():
            for param in v:
                if param == arg_name and (arg_value == v[arg_name].default or str(arg_value).lower() == str(v[arg_name].default).lower()):
                    is_default = True
                    continue

            if is_default:
                continue

        do_terminal_plot=True
        if not is_default:
            if str(arg_value).replace('.', '').replace(',','').isnumeric():
                arg_value = float(arg_value)
            elif isinstance(arg_value, (tuple, list)):
                avList = []
                for av in arg_value:
                    if str(av).replace('.', '').replace(',','').isnumeric():
                        avList.append(float(av))
                arg_value = avList
            kwargs[arg_name] = arg_value

    if 'input_data' not in kwargs:
        kwargs['input_data'] = inData
    # Call the sprit.run function with the generated kwargs
    kwargs['input_data'] = str(kwargs['input_data']).replace("'", "")  # Remove single quotes to reduce errors
    if str(kwargs['input_data']).lower() == 'gui':
        sprit_hvsr.gui()
    else:
        # Print a summary if not verbose
        if 'verbose' not in kwargs or not kwargs['verbose']:
            print("\nRunning sprit.run() with the following arguments (use --verbose for more information):\n")
            print("\tsprit.run(", end='')
            for key, value in kwargs.items():
                if 'kwargs' in str(key):
                    pass
                else:
                    if type(value) is str:
                        print(f"{key}='{value}'", end=', ')
                    else:
                        print(f"{key}={value}", end=', ')
            print('**ppsd_kwargs, **kwargs', end='')
            print(')')

        print('\tNon-default kwargs:')
        [print(f"\t\t {k} = {v}") for k, v in kwargs.items()]
        print()
        
        hvData =  sprit_hvsr.run(**kwargs)

        if do_terminal_plot:
            ptkwargs = {k: v for k, v in kwargs.items() if k in tuple(inspect.signature(sprit_plot.plot_text).parameters.keys())}
            sprit_plot.plot_text(hvData, **ptkwargs)

if __name__ == '__main__':
    main()
