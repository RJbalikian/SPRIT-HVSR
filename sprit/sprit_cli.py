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

    for i, param in enumerate(parameters.items()):
        for name, parameter in param.items():
            # Add arguments and options here
            parser.add_argument(F'--{name}', help=f'Keyword argument {hvsrFunctions[i].__str__} in function')
    
    # Add more arguments/options as needed
    
    args = parser.parse_args()
    
    kwargs = {}
    
    #MAKE THIS A LOOP!!!
    # Map command-line arguments/options to kwargs
    if args.arg1:
        kwargs['arg1'] = args.arg1
    if args.arg2:
        kwargs['arg2'] = args.arg2
    # Map more arguments/options as needed
    
    # Call the sprit.run function with the generated kwargs
    sprit.run(**kwargs)

if __name__ == '__main__':
    main()

