"""This module/script is used to run sprit from the command line. 

The arguments here should correspond to any of the keyword arguments that can be used with sprit.run()
"""

import argparse
import sprit  # Assuming you have a module named 'sprit'

def main():
    parser = argparse.ArgumentParser(description='CLI for SPRIT HVSR package (specifically the sprit.run() function)')
    
    # Add arguments and options here
    parser.add_argument('--arg1', help='Description of argument 1')
    parser.add_argument('--arg2', help='Description of argument 2')
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

