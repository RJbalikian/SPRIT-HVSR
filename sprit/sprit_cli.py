"""This module/script is used to run sprit from the command line. 

The arguments here should correspond to any of the keyword arguments that can be used with sprit.run()
"""

import argparse
import inspect
import sprit  # Assuming you have a module named 'sprit'

def main():
    parser = argparse.ArgumentParser(description='CLI for SPRIT HVSR package (specifically the sprit.run() function)')
    
    hvsrFunctions = [sprit.input_params,
                     sprit.fetch_data,
                     sprit.remove_noise,
                     sprit.generate_ppsds,
                     sprit.process_hvsr,
                     sprit.check_peaks,
                     sprit.get_report,
                     sprit.hvplot]

    parameters = []

    for f in hvsrFunctions:
        parameters.append(inspect.signature(f).parameters)

    paramNamesList = []
    for i, param in enumerate(parameters):
        for name, parameter in param.items():
            print(name, ',Default=', parameter.default)
            # Add arguments and options here
            if name not in paramNamesList:
                paramNamesList.append(name)
                parser.add_argument(F'--{name}', help=f'Keyword argument {hvsrFunctions[i].__str__} in function')
    # Add more arguments/options as needed
    
    args = parser.parse_args()
    
    kwargs = {}
    
    #MAKE THIS A LOOP!!!
    # Map command-line arguments/options to kwargs
    for arg_name, arg_value in vars(args).items():
        if arg_value is None:
            pass
            print(f"{arg_name}={arg_value}")
        else:
            print(f"!!!{arg_name}={arg_value}")

    
    # Call the sprit.run function with the generated kwargs
    sprit.run(**kwargs)

if __name__ == '__main__':
    main()

