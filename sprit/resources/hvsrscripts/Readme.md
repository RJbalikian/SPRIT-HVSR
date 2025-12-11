# HVSR Script
# Introduction
The HVSR script is shell script designed for use with Raspberry Shake instruments. 
It allows a script to be run in the background to wait for a specified time while data is being acquired, then to combine the three channels into a single file just for the specified time interval.
This means that data can be collected on a per-site basis, with one file corresponding to the data acquired for that site.

The script will also perform a graceful shutdown of the shake at the end of the specified time, reducing the number of visits to an instrument. 

The current version of the script is located in the same directory as this readme. Instructions for setup and usage are below.

# Copy HVSR Script File to Shake
To set up the script for easy usage in the field, the following steps are recommended.

> 1) Copy file to the shake and move into /opt/hvsr directory
> 2) Set up hvsr function to be defined at instrument startup
> 3) Reboot
> 4) Test

## 1) Copy file to the shake and move into /opt/hvsr directory
Using Copy/Paste, the scp command, filezilla, or any other method transfer the hvsr_vx-x.sh to your Raspberry Shake 3D. Examples for this are included below:

> TROUBLESHOOTING
> If you are doing this from a Windows computer, it may convert your file to DOS format, which uses a different "carraige return"/endline character than unix (which is what the shake uses).
> If you can install the dos2unix tool on your shake (`sudo apt-get install dos2unix`) then run that command (`sudo dos2unix /path/to/hvsr_vx-x.sh`), you may be able to get around this issue.

### Alternative 1 for copying HVSR script: Copy/Paste
In your terminal, use ssh to enter the shake (you will be prompted for the shake's password, `shakeme` by default):
```bash
ssh myshake@rs.local
```

Edit/create a new file (replace the `x`'s below with the version number of the file located in the same directory as this Readme):

```bash
sudo nano /opt/hvsr/hvsr_vx-x.sh
```

Copy all the text of the `hvsr_vx-x.sh` file on your local computer. Then, go back to the terminal (with the nano editor opened) and right click to paste the contents of the file. 
Type `Ctrl + s` to save and `Ctrl + x` to exit the nano editor.

### Alternative 2 for copying HVSR script: Secure Copy Protocol (SCP)
Using scp command, copy the HVSR script file to the `/opt` directory. Then move the file to the specified hvsr folder. 

```bash
scp "/path/to/local/copy/of/hvsr_v1-3.sh" "myshake@rs.local:/opt"
ssh myshake@rs.local
sudo mkdir /opt/hvsr
sudo mv /opt/hvsr_vx-x.sh /opt/hvsr/hvsr_vx-.sh
```

### Alternative 3 for copying HVSR script: Filezilla
Filezilla is a graphical user interface for secure file transfer between devices on a network. 
Instructions are similar to what is described [here](https://github.com/RJbalikian/SPRIT-HVSR/wiki/Data-Processing:-Raspberry-Shake-3D#filezilla)

You can use filezilla to create a directory at `/opt/hvsr` if it is not already there, then copy the hvsr shell script file into that directory.

# Create HVSR Function
Now, you will creat a function that is defined every time the instrument starts. 
This allows you to just type "hvsr" in the terminal to activate the HVSR script file.

Open and edit the .bashrc file using the nano text editor:

```bash
sudo nano ~/.bashrc
```

Now, the nano text editor should open in your terminal. Navigate down to the section where aliases are defined near the end of the file
(you can technically put this wherever in the file, but that is a logical location for a function definition of this kind).

Copy/paste or otherwise enter the following lines into the nano editor to define the HVSR function.

```bash
hvsr(){
    if [ "$1" == "-h" ] ; then
        sudo bash /opt/hvsr/hvsr_v1-3.sh -h
        return 0
    fi

    if [ -e "/usr/bin/screen" ]; then
        echo "Starting HVSR script in screen session."
        sleep 1
        screen -mS hvsr sudo bash /opt/hvsr/hvsr_v1-3.sh "$@"
    else
        echo "Starting HVSR script."
        echo "WARNING! SCRIPT WILL STOP ON SSH DISCONNECT!"
        sudo bash /opt/hvsr/hvsr_v1-3.sh "$@"
    fi
}
```

Type `Ctrl + s` to save and `ctrl + x` to exit nano and return to your terminal.

# Install "Screen" tool
You will need to install the `screen` tool for this to work, at least if you want the HVSR script to continue running after you disconnect your SSH device. 
Your Shake will need to be connected to the internet to install the `screen` tool.

```bash
sudo apt update
sudo apt install screen
```

> TROUBLESHOOTING
> For the shake to continue running the HVSR script after being disconnected from the SSH device, you must install screen.
> The HVSR script will work without installing screen, but it will stop if you disconnect the SSH device while it is running.
> TO prevent this, we use the screen tool to run an additional terminal session in the background
> (this won't be interrupted by a signal hangup from disconnecting the SSH device).
> You may not be able to install screen without updating the `apt` package manager.
> You may need to change some configuration settings on your shake to do this.
> For our instruments, this required the following commands (while the Shake was connected to the internet)
> `sudo apt update`
> `sudo apt install screen`
> Then you can run the following to check that the installation worked:
> `screen -h`, which should print the help message for screen. Otherwise, if it did not install, you will receive an error message.

## Reboot
Enter the following command to reboot your Shake:

```bash 
sudo reboot
```

## Test hvsr script
Now that you have set up the hvsr function in .bashrc, it should be defined immediately upon boot.

You will have been logged out of the Shake during reboot, so log back into your shake via ssh:

```powershell
ssh myshake@rs.local
```

It will prompt you for your password.

Use the following script as a test run:
```bash
hvsr -n "TEST_v3" -t TRUE -d 0.1 -s 5 -c 1
```

You will see a message like "Starting HVSR Script in screen session" (this is the first line of the hvsr() function you defined above).
Then, the terminal will open a new "screen", which will display information about the site.

The following is true of the test run as defined above:
* The site name will be TEST_v3 (`-n "TEST_v3"`)
* It will run as a test program (i.e., it will not shut down your shake at the end of the site). (`-t TRUE`)
* There will be a 5-second starting timer before acquisition begins (`-s 5`)
* The duration of acquisition will last 0.1 minutes (6 seconds) (`-d 0.1`)
* The status of the site will be checked and printed to the terminal at 1 second intervals. (`-c 1`)

After your script has run, the acquisition screen will close and you will be returned to the main terminal, where the following will be printed:
`[screen is terminating]`

You can check that the file was saved by looking in the `/opt/hvsr/data` folder. Use the `-l -h` flags to see the size of the file in human readable format:

> Note: The files should be about 5-10kb in size (or at least that was our results from a six-second test as defined above)

```bash
ls /opt/hvsr/data -l -h
```

See the [Usage](#Usage) section below for more details on the arguments and options you can use with the HVSR script.

# Usage
> NOTE: the -n flag signifies a file name. You can use a space in the file name as long as the name is in quotes (e.g., `hvsr -n "Site Name"`), but it is recommended not to use spaces in the site names.
The intended purpose of this file is that you can set up everything before acquiring data at a site and to eliminate the need to reconnect a computer at the end of the acquisition to turn off the Shake.

The data will also be collated into a single file with all three components, thereby saving work and potential for error later. 
For example, if the instrument time is not updated, you will still be able to find your data because it will be associated with a specific file and not just associated with a time.

After setting up as specified above, you may get help by using the `-h` flag in the hvsr script:

```bash
hvsr -h
```
This will print up help text to your terminal, which will show all the flags and their meanings and usage.

For example, see below:
```text
Usage: hvsr_v1-3.sh CAPITALIZED WORD after option indicates variable to which that argument gets passed.

	OPTION |   ARGUMENT   | DESCRIPTION       
	-------|--------------|-------------------
	 -n    | SITE_NAME    | Name of site; this will be used as the first part of the filename; defaults to 'HVSRSite'
	 -d    | DURATION     | Duration of HVSR acquisition, in minutes (default is 20 min; up to one decimal point supported)
	 -c    | CHECK_INT    | The interval at which to check/print status, in seconds (default is 30 sec)
	 -s    | STARTUP_TIME | The amount of time between when the hvsr command is run and when data is saved, in seconds (default is 15 sec)
	 -t    |              | Run this site as a test (does not save data or turn off Shake)
	 -v    |              | Print information to terminal in verbose manner
	 -h    |              | Print this help message (-h should only be used by itself)
	 -e    | EXPORT_DISK* | EXPORT_DISK argument is optional; Export data in /opt/hvsr/data folder to inserted USB disk (experimental)
```



## Examples
### Example 1
Acquire data for site called "HourLongSite" for one hour before ending acquisition, collating data, saving to file, and powering off Shake.

```bash
hvsr -n "HourLongSite" -d 60
```
### Example 2
Acquire data for 30 minutes, save data but do not turn off shake when done.

```bash
hvsr -d 30 -t TRUE
```
> Note: the `TRUE` after -t is not strictly necesssary, but it prevents an error message.

### Example 3
Acquire data for 10 minutes for site called "ShortSite", giving yourself 30 seconds of startup time between the time you run the hvsr command and when it begins to save data for the site.

```bash
hvsr -n "ShortSite" -d 10 -s 30
```
