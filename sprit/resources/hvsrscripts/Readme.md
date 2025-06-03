# HVSR Script
# Introduction
The HVSR script is shell script designed for use with Raspberry Shake instruments. 
It allows a script to be run in the background to wait for a specified time while data is being acquired, then to combine the three channels into a single file just for the specified time interval.
This means that data can be collected on a per-site basis, with one file corresponding to the data acquired for that site.

The script will also perform a graceful shutdown of the shake at the end of the specified time, reducing the number of visits to an instrument. 

The current version of the script is located in the same directory as this readme. Instructions for setup and usage are below.

# Setup
To set up the script for easy usage in the field, the following steps are recommended.

> 1) Copy file to the shake and move into /opt/hvsr directory
> 2) Set up hvsr function to be defined at instrument startup
> 3) Reboot
> 4) Test

## 1) Copy file to the shake and move into /opt/hvsr directory
Using the scp command, filezilla, or any other method transfer the hvsr_vx-x.sh to your Raspberry Shake 3D. Examples for this are included below:

### SCP
Using this command, you will only be able to copy the file to the home directory. Then you will need to move the file to the specified hvsr folder

After running the scp command and ssh command, you will be asked for the Raspberry Shake's password (`shakeme` by default).

```bash
scp "/path/to/local/copy/of/hvsr_v1-3.sh" "myshake@rs.local:"
ssh myshake@rs.local
sudo mkdir /opt/hvsr
sudo mv ~/hvsr_v1-3.sh /opt/hvsr/hvsr_v1-3.sh
```

### Filezilla
Instructions are similar to what is described [here](https://github.com/RJbalikian/SPRIT-HVSR/wiki/Data-Processing:-Raspberry-Shake-3D#filezilla)

You can use filezilla to create the directory at /opt/hvsr if it is not already there, then copy the hvsr shell script file into that directory.

## Set up an `hvsr` function to be defined at instrument startup
Open and edit the .bashrc file using the nano text editor:

```bash
sudo nano ~/.bashrc
```

Now, the nano text editor should open in your terminal. Navigate down to the section where aliases are defined near the end of the file. 
Enter the following lines (the first two lines below are not strictly necessary, they are just used to provide user feedback that the program is running as intended in a "screen" session (see note at the bottom of this page)):

```bash
hvsr(){
    if [ "$1" == "-h"] ; then
        sudo bash /opt/hvsr/hvsr_v1-3.sh -h
        return 0
    fi
    echo "Starting HVSR script in screen session.
    sleep 1
    screen -mS hvsr sudo bash /opt/hvsr/hvsr_v1-3.sh "$@"
    }
```

Type `Ctrl + s` to save and `ctrl + x` to exit nano and return to your terminal.

## Reboot
Enter the following command to reboot your Shake:

```bash 
sudo reboot
```
## Test hvsr script
Now that you have set up the hvsr function in .bashrc, it should be defined immediately upon boot.

Use the following script as a test run:
```bash
hvsr -n "TEST1" -t TRUE -d 0.1 -s 5 -c 1
```

You will see a message like "Starting HVSR Script in screen session" (this is the first line of the hvsr() function you defined above).
Then, the terminal will open a new "screen", which will display information about the site.

The following is true of the test run as defined above:
* The site name will be TEST1
* It will run as a test program (i.e., it will not shut down your shake at the end of the site).
* There will be a 5-second starting timer before acquisition begins
* The data acquisition will last 0.1 minutes (6 seconds)
* The status of the site will be checked and printed to the terminal at 1 second intervals.

After your script has run, the acquisition screen will close and you will be returned to the main terminal, where the following will be printed:
`[screen is terminating]`

You can check that the file was saved by looking in the `/opt/hvsr/data` folder. Use the `-l -h` flags to see the size of the file in human readable format:

> Note: The files should be about 5-10kb in size (or at least that was our results from a six-second test as defined above)

```bash
ls /opt/hvsr/data -l -h
```

See the [Usage](#Usage) section below for more details on the arguments and options you can use with the HVSR script.

# Usage
The intended purpose of this file is that you can set up everything before acquiring data at a site and to eliminate the need to reconnect a computer at the end of the acquisition.

The data will also be collated into a single file with all three components, thereby saving work and potential for error later. 
For example, if the instrument time is not updated, you will still be able to find your data because it will be associated with a specific file and not just associated with a time.

After setting up as specified above, you may get help by using the `-h` flag in the hvsr script:

```bash
hvsr -h
```
This will print up a help file to your terminal, which will show all the flags and their meanings and usage.

For example, see below:



