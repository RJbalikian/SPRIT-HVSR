"""This script contains all the functions, classes, etc. to create a tkinter app for graphical user interface.
"""
import datetime
import functools
import importlib
import json
import os
import pathlib
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.simpledialog import askinteger
from tkinter import messagebox
import traceback
import warnings
import zoneinfo

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import MouseButton, MouseEvent
import numpy as np
#matplotlib.use('TkAgg')

try: #For distribution
    from sprit import sprit_utils
    from sprit import sprit_hvsr
    from sprit import sprit_plot
except: #For local testing
    import sprit_hvsr 
    import sprit_utils
    import sprit_plot
    pass

global spritApp
global current_theme_name
global SPRIT_App

resource_dir = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources')
settings_dir = resource_dir.joinpath('settings')
gui_theme_file = settings_dir.joinpath('gui_theme.json')
with open(gui_theme_file, 'r') as f:
    curr_gui_dict = json.load(f)
current_theme_name = curr_gui_dict['theme_name']

class SPRIT_App:
    global spritApp
    def __init__(self, master):
        self.master = master
        self.master.title("SPRIT")
        self.params = sprit_hvsr.HVSRData({'site':''})

        # Set the theme
        self.darkthemepath = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources').joinpath('themes').joinpath('forest-dark.tcl')
        self.lightthemepath = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources').joinpath('themes').joinpath('forest-light.tcl') 

        # Create the style object
        self.style = ttk.Style(master)
        #
        #self.style.theme_use('forest-light')

        self.create_menubar()
        self.create_tabs()

        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)        


        if 'forest' in current_theme_name:
            if 'light' in current_theme_name:
                self.master.tk.call('source', self.lightthemepath)
            else:
                self.master.tk.call('source', self.darkthemepath)
        else:
            self.style.theme_use(current_theme_name)
        # Create the dark theme
        #self.style.theme_create("dark", parent="alt", settings={
        #    "TLabel": {"configure": {"background": "black", "foreground": "white"}},
        #    "TButton": {"configure": {"background": "black", "foreground": "white"}},
        #    # Add more options here to style other widgets
        #})
        
        # Create the light theme
        #self.style.theme_create("light", parent="alt", settings={
        #    "TLabel": {"configure": {"background": "white", "foreground": "black"}},
        #    "TButton": {"configure": {"background": "white", "foreground": "black"}},
        #    # Add more options here to style other widgets
        #})

    #Method to log error message
    def log_errorMsg(self, logMsg):

        self.log_text.insert('end', logMsg)
        self.tab_control.select(self.log_tab)

    #Not currently working
    def manual_label_update(self):
        for notebook in self.master.winfo_children():
            if isinstance(notebook, ttk.Notebook):
                for tab_id in notebook.tabs():
                    tab_frame = notebook.nametowidget(tab_id)

                    for frame in tab_frame.winfo_children():
                        if isinstance(frame, ttk.LabelFrame):
                            for widget in frame.winfo_children():
                                if isinstance(widget, ttk.Label):
                                    # apply the updated style to the label
                                    
                                    self.style.layout('CustTLabel', [('Label.border', {'sticky': 'nswe', 'border': '1', 'children': [('Label.padding', {'sticky': 'nswe', 'children': [('Label.text', {'sticky': 'nswe'})]})]})])
                                    self.style.configure('CustTLabel', background=self.style.lookup('style', 'background'), foreground=self.style.lookup('style', 'background'))
                                    self.style.map('CustTLabel', {'priority':[('CustTLabel',1)]})
                                    widget.configure(style='CustTLabel')

    def create_menubar(self):
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)
        
        self.sprit_menu = tk.Menu(self.menubar, tearoff=0)

        def on_theme_select():
            # Set the theme based on the selected value
            self.style = ttk.Style()

            #Update the theme file so the new theme opens on reboot
            prev_theme = curr_gui_dict['theme_name']
            curr_gui_dict['theme_name'] = self.theme_var.get()
            with open(gui_theme_file, 'w') as f:
                json.dump(curr_gui_dict, f)

            def apply_theme():
                if 'forest' in self.theme_var.get():
                    if self.theme_var.get()=='forest-dark' and 'forest-dark' not in self.style.theme_names():
                        self.master.tk.call('source', self.darkthemepath)
                    elif self.theme_var.get()=='forest-light' and 'forest-light' not in self.style.theme_names():
                        self.master.tk.call('source', self.lightthemepath)            
                self.master.tk.call("ttk::style", "theme", "use", self.theme_var.get())

            if curr_gui_dict['theme_name']=='forest-light' or curr_gui_dict['theme_name'] == 'forest-dark':
                do_reboot = messagebox.askyesno('App Restart Required', 
                                             f"It is recommended to restart the SpRIT GUI at this time to apply this theme. If not, you may continue but theme errors may occur. Click No to retain current theme ({prev_theme}) \nReboot now?",
                                             )
                print(do_reboot)
                if do_reboot:
                    reboot_app()
                else:
                    self.theme_var.set(prev_theme)
            else:
                apply_theme()

            """An attempt to get the backgrounds right
            def apply_to_all_children(widget, func):
                Recursively apply a function to all child widgets of a given widget
                children = widget.winfo_children()
                for child in children:
                    func(child)
                    apply_to_all_children(child, func)
                return

            def change_background_color(widget):
                if isinstance(widget, tk.Label):
                    widget.option_clear()
                    widget.configure(background=None, foreground=None)
                return
            
            apply_to_all_children(self.master, change_background_color)
            """

            #self.master.tk.call("ttk::setTheme", self.theme_var.get())

            #self.style.theme_use(self.theme_var.get())
            #self.master.tk.call('source', self.lightthemepath)
            #self.style.theme_use(self.theme_var.get())
            #self.style.configure("TLabel", background=self.style.lookup('TLabel', 'background'), foreground=self.style.lookup('TLabel', 'background'))

        def import_parameters(self):
            filepath = filedialog.askopenfilename()
        
        
        def export_parameters(self):
            filepath = filedialog.asksaveasfilename()

        self.theme_menu = tk.Menu(self.menubar, tearoff=0)
        self.theme_var = tk.StringVar(value=current_theme_name)
        self.theme_menu.add_radiobutton(label="Default", variable=self.theme_var, value="default", command=on_theme_select)
        self.theme_menu.add_radiobutton(label="Clam", variable=self.theme_var, value="clam", command=on_theme_select)
        self.theme_menu.add_radiobutton(label="Alt", variable=self.theme_var, value="alt", command=on_theme_select)
        self.theme_menu.add_radiobutton(label="Forest Light (buggy)", variable=self.theme_var, value="forest-light", command=on_theme_select)
        self.theme_menu.add_radiobutton(label="Forest Dark (buggy)", variable=self.theme_var, value="forest-dark", command=on_theme_select)

        self.sprit_menu.add_cascade(label="Theme", menu=self.theme_menu)
        self.sprit_menu.add_command(label="Import Parameters", command=import_parameters)
        self.sprit_menu.add_command(label="Export Parameters", command=export_parameters)
        self.sprit_menu.add_separator()
        self.sprit_menu.add_command(label="Exit", command=self.master.quit)
        self.settings_menu = tk.Menu(self.menubar, tearoff=0)
        self.instrument_menu = tk.Menu(self.settings_menu, tearoff=0)
        self.instrument_var = tk.StringVar(value="Raspberry Shake")
        self.instrument_menu.add_radiobutton(label="Raspberry Shake", variable=self.instrument_var, value="Raspberry Shake")
        self.instrument_menu.add_radiobutton(label="Tromino", variable=self.instrument_var, value="Tromino")
        self.instrument_menu.add_radiobutton(label="Other", variable=self.instrument_var, value="Other")
        self.settings_menu.add_cascade(label="Instrument", menu=self.instrument_menu)
        self.settings_menu.add_command(label="Processing Settings", command=lambda: self.tab_control.select(self.settings_tab))

        self.menubar.add_cascade(label="SPRIT", menu=self.sprit_menu)
        self.menubar.add_cascade(label="Settings", menu=self.settings_menu)
    
    def create_tabs(self):
        self.style = ttk.Style(self.master)

        self.tab_control = ttk.Notebook(self.master)

        # INPUT TAB
        self.input_tab = ttk.Frame(self.tab_control)

        # Configure the row and column of the input_tab to have a non-zero weight
        hvsrFrame = ttk.LabelFrame(self.input_tab, text="Input Parameters")
        #hvsrFrame.rowconfigure(0, weight=1)
        hvsrFrame.columnconfigure(1, weight=1)

        # Logo and Site Name
        # Replace "logo.png" with the path to your logo image
        #self.logo = tk.PhotoImage(file="logo.png")
        #self.logo_label = ttk.Label(hvsrFrame, image=self.logo)
        #self.logo_label.grid(row=0, column=0)
        self.processingData = False

        
        def update_input_labels(hvsr_data):
            #Update labels for data preview tab
            self.input_data_label.configure(text=self.data_filepath_entry.get() + '\n' + str(hvsr_data['stream']))
            
            self.obspySreamLabel_settings.configure(text=str(hvsr_data['stream']))

            self.sensitivityLabelZ_settings.configure(text=hvsr_data['paz']['Z']['sensitivity'])
            self.gainLabelZ_settings.configure(text=hvsr_data['paz']['Z']['gain'])
            self.polesLabelZ_settings.configure(text=hvsr_data['paz']['Z']['poles'])
            self.zerosLabelZ_settings.configure(text=hvsr_data['paz']['Z']['zeros'])
            
            self.sensitivityLabelN_settings.configure(text=hvsr_data['paz']['N']['sensitivity'])
            self.gainLabelN_settings.configure(text=hvsr_data['paz']['N']['gain'])
            self.polesLabelN_settings.configure(text=hvsr_data['paz']['N']['poles'])
            self.zerosLabelN_settings.configure(text=hvsr_data['paz']['N']['zeros'])

            self.sensitivityLabelE_settings.configure(text=hvsr_data['paz']['E']['sensitivity'])
            self.gainLabelE_settings.configure(text=hvsr_data['paz']['E']['gain'])
            self.polesLabelE_settings.configure(text=hvsr_data['paz']['E']['poles'])
            self.zerosLabelE_settings.configure(text=hvsr_data['paz']['E']['zeros'])
            return
        
        self.data_read = False #Initialize
        #FUNCTION TO READ DATA
        @_catch_errors
        def read_data():
            update_progress_bars(prog_percent=0)
            #messagebox.showinfo(title="Reading Data", message='Reading Data...')
            self.log_text.insert('end', f'\n\nReading data [{datetime.datetime.now()}]\n\n')
            self.starttime, self.endtime = get_times()


            self.log_text.insert('end', f"{self.input_params_call['text']}\n\n")
            self.log_text.insert('end', f"{self.fetch_data_call['text']}\n\n")

            if self.file_source.get() == 'batch':
                batchType = self.batch_type.get()
                if isinstance(self.fpath, str):
                    self.fpath = self.fpath
                elif isinstance(self.fpath, tuple) and len(self.fpath)==1:
                    self.fpath = self.fpath[0]
                elif len(self.fpath) > 1:
                    self.fpath = list(self.fpath)
                else:
                    self.fpath = self.fpath[0]


                update_progress_bars(prog_percent=1)            
                self.params = sprit_hvsr.input_params(input_data=self.fpath,
                                    metadata = self.meta_path.get(),
                                    site=self.site_name.get(),
                                    network=self.network.get(),
                                    station=self.station.get(),
                                    location=self.location.get(),
                                    channels=[self.z_channel.get(), self.n_channel.get(), self.e_channel.get()],
                                    acq_date = self.starttime.date(),
                                    starttime = self.starttime,
                                    endtime = self.endtime,
                                    tzone = 'UTC', #Will always be converted to UTC before we get to this point when using gui
                                    xcoord = self.x.get(),
                                    ycoord =  self.y.get(),
                                    elevation = self.z.get(),
                                    input_crs= self.input_crs.get(),
                                    output_crs= self.output_crs.get(),
                                    elev_unit= self.elev_unit.get(),
                                    instrument = self.instrumentSel.get(),
                                    hvsr_band = [self.hvsrBand_min.get(), self.hvsrBand_max.get()] )

                if self.trim_dir.get()=='':
                    trimDir=None
                else:
                    trimDir=self.trim_dir.get()

                update_progress_bars(prog_percent=2)            
                self.hvsr_data = sprit_hvsr.fetch_data(params=self.params,
                                            source=self.file_source.get(), 
                                            trim_dir=trimDir, 
                                            export_format=self.export_format.get(), 
                                            detrend=self.detrend.get(), 
                                            detrend_options=self.detrend_options.get())
                
                update_progress_bars(prog_percent=10)                                
                self.site_options = self.hvsr_data.sites

                self.log_text.insert('end', f"{self.site_options}\n\n")

                firstSite = self.hvsr_data[list(self.hvsr_data.keys())[0]]
                update_input_labels(firstSite)
                update_site_dropdown()

                #Plot data in data preview tab
                self.fig_pre, self.ax_pre = sprit_plot._plot_simple_stream_obspy(stream=firstSite['stream'], params=firstSite, fig=self.fig_pre, axes=self.ax_pre, return_fig=True)

                #Plot data in noise preview tab
                self.fig_noise, self.ax_noise = sprit_plot._plot_simple_stream_obspy(stream=firstSite['stream'], params=firstSite, fig=self.fig_noise, ax=self.ax_noise, fill_gaps=0, component='Z', stack_type='linear', detrend='mean', dbscale=True, return_fig=True, cmap_per=[0.1,0.9])
                select_windows(event=None, initialize=True)
                plot_noise_windows(self.hvsr_data)

            else:
                if isinstance(self.fpath, str):
                    pass
                elif len(self.fpath) > 1:
                    self.fpath = list(self.fpath)
                else:
                    self.fpath = self.fpath[0]

                update_progress_bars(prog_percent=1)
                self.params = sprit_hvsr.input_params( input_data=self.fpath,
                                    metadata = self.meta_path.get(),
                                    site=self.site_name.get(),
                                    network=self.network.get(), 
                                    station=self.station.get(), 
                                    location=self.location.get(), 
                                    channels=[self.z_channel.get(), self.n_channel.get(), self.e_channel.get()],
                                    acq_date = self.starttime.date(),
                                    starttime = self.starttime,
                                    endtime = self.endtime,
                                    tzone = 'UTC', #Will always be converted to UTC before we get to this point when using gui
                                    xcoord = self.x.get(),
                                    ycoord =  self.y.get(),
                                    elevation = self.z.get(),
                                    input_crs= self.input_crs.get(),
                                    output_crs= self.output_crs.get(),
                                    elev_unit= self.elev_unit.get(),
                                    instrument = self.instrumentSel.get(),
                                    hvsr_band = [self.hvsrBand_min.get(), self.hvsrBand_max.get()] )
                self.hvsr_data = self.params

                if self.trim_dir.get()=='':
                    trimDir=None
                else:
                    trimDir=self.trim_dir.get()
                
                update_progress_bars(prog_percent=2)
                try:
                    self.hvsr_data = sprit_hvsr.fetch_data(params=self.params,
                                            source=self.file_source.get(),
                                            trim_dir=trimDir, 
                                            export_format=self.export_format.get(), 
                                            detrend=self.detrend.get(), 
                                            detrend_options=self.detrend_options.get())
                except:
                    traceback.print_exc()

                update_progress_bars(prog_percent=10)
                update_input_labels(self.hvsr_data)

                # Plot data in data preview tab
                self.fig_pre = sprit_plot._plot_simple_stream_obspy(stream=self.hvsr_data['stream'], params=self.hvsr_data, fig=self.fig_pre, axes=self.ax_pre, return_fig=True)

                # Plot data in noise preview tab
                self.fig_noise = sprit_plot._plot_input_stream_mpl(stream=self.hvsr_data['stream'], hv_data=self.hvsr_data, fig=self.fig_noise, ax=self.ax_noise, fill_gaps=0, component='Z', stack_type='linear', detrend='mean', dbscale=True, return_fig=True, cmap_per=[0.1,0.9])
                select_windows(event=None, initialize=True)
                plot_noise_windows(self.hvsr_data)

            self.data_read = True
            if not self.processingData:
                update_progress_bars(prog_percent=100)
                self.tab_control.select(self.preview_data_tab)
            return self.hvsr_data
        
        def report_results(hvsr_results, azimuth='HV'):
            self.curveTest1ResultText.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['Lw'][:-1])
            self.curveTest1Result.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['Lw'][-1])

            self.curveTest2ResultText.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['Nc'][:-1])
            self.curveTest2Result.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['Nc'][-1])

            self.curveTest3ResultText.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['σ_A(f)'][:-1])
            self.curveTest3Result.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['σ_A(f)'][-1])

            curvePass = (hvsr_results['BestPeak'][azimuth]['PassList']['WindowLengthFreq.'] +
                                hvsr_results['BestPeak'][azimuth]['PassList']['SignificantCycles']+
                                hvsr_results['BestPeak'][azimuth]['PassList']['LowCurveStDevOverTime']) > 2
            if curvePass:
                self.totalCurveResult.configure(text=sprit_utils._check_mark(), font=("TkDefaultFont", 16, "bold"), foreground='green')
            else:
                self.totalCurveResult.configure(text=sprit_utils._x_mark(), font=("TkDefaultFont", 16, "bold"), foreground='red')

            self.peakTest1ResultText.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['A(f-)'][:-1])
            self.peakTest1Result.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['A(f-)'][-1])
            
            self.peakTest2ResultText.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['A(f+)'][:-1])
            self.peakTest2Result.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['A(f+)'][-1])
            
            self.peakTest3ResultText.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['A0'][:-1])
            self.peakTest3Result.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['A0'][-1])

            self.peakTest4ResultText.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['P-'][:5] + ' and ' +hvsr_results['BestPeak'][azimuth]['Report']['P+'][:-1])
            if hvsr_results['BestPeak'][azimuth]['PassList']['FreqStability']:
                self.peakTest4Result.configure(text=sprit_utils._check_mark())
            else:
                self.peakTest4Result.configure(text=sprit_utils._x_mark())

            self.peakTest5ResultText.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['Sf'][:-1])
            self.peakTest5Result.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['Sf'][-1])
            
            self.peakTest6ResultText.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['Sa'][:-1])
            self.peakTest6Result.configure(text=hvsr_results['BestPeak'][azimuth]['Report']['Sa'][-1])

            peakPass = (hvsr_results['BestPeak'][azimuth]['PassList']['PeakProminenceBelow'] +
                    hvsr_results['BestPeak'][azimuth]['PassList']['PeakProminenceAbove']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['PeakAmpClarity']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['FreqStability']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['PeakStability_FreqStD']+
                    hvsr_results['BestPeak'][azimuth]['PassList']['PeakStability_AmpStD']) >= 5
            if peakPass:
                self.totalPeakResult.configure(text=sprit_utils._check_mark(), font=("TkDefaultFont", 16, "bold"), foreground='green')
            else:
                self.totalPeakResult.configure(text=sprit_utils._x_mark(), font=("TkDefaultFont", 16, "bold"), foreground='red')

            if curvePass and peakPass:
                self.totalResult.configure(text=f'Pass {sprit_utils._check_mark()}', font=("TkDefaultFont", 22, "bold"), foreground='green')
            else:
                self.totalResult.configure(text=f'Fail {sprit_utils._x_mark()}', font=("TkDefaultFont", 22, "bold"), foreground='red')

            sprit_hvsr.plot_hvsr(hvsr_results, plot_type=get_kindstr(), fig=self.fig_results, ax=self.ax_results, use_subplots=True, clear_fig=False)

        # FUNCTION TO PROCESS DATA
        @_catch_errors
        def process_data():
            update_progress_bars(prog_percent=0)
            #messagebox.showinfo("Processing Data", 'Processing Data...')
            self.processingData = True #Set to true while data processing algorithm is being run
            
            if not self.data_read:
                self.hvsr_data = read_data()
                update_progress_bars(prog_percent=12)

            self.log_text.insert('end', f"\n\nProcessing Data [{datetime.datetime.now()}]\n\n")
            self.log_text.insert('end', f"{self.generate_ppsd_call['text']}\n\n")

            
            self.hvsr_data = sprit_hvsr.remove_noise(hvsr_data=self.hvsr_data,
                                                     remove_method='auto',
                                                     sat_percent=0.995,
                                                     noise_percent=0.8,
                                                     sta=2,
                                                     lta=30,
                                                     stalta_thresh=[0.5, 5],
                                                     warmup_time=0,
                                                     cooldown_time=0,
                                                     min_win_size=1,
                                                     remove_raw_noise=False)
            update_progress_bars(prog_percent=12)
            self.hvsr_data = plot_noise_windows(self.hvsr_data)

            update_progress_bars(prog_percent=15)
            self.hvsr_data = sprit_hvsr.generate_psds(hvsr_data=self.hvsr_data, 
                                                remove_outliers=self.remove_outliers.get(),
                                                outlier_std=self.outlier_std.get(),
                                                ppsd_length=self.ppsd_length.get(),
                                                overlap=self.overlap.get(),
                                                period_step_octaves=self.perStepOct.get(),
                                                skip_on_gaps=self.skip_on_gaps.get(),
                                                db_bins=self.db_bins,
                                                period_limits=self.period_limits,
                                                period_smoothing_width_octaves=self.perSmoothWidthOct.get(),
                                                special_handling=special_handling#, verbose=True
                                               )
            update_progress_bars(prog_percent=50)

            self.hvsr_data = sprit_hvsr.remove_outlier_curves(hvsr_data=self.hvsr_data,
                                            outlier_threshold=98,
                                            use_percentile=True,
                                            use_hv_curves = False,
                                            show_plot = False)
            update_progress_bars(prog_percent=60)

            self.log_text.insert('end', f"{self.procHVSR_call['text']}\n\n")
            self.hvsr_results = sprit_hvsr.process_hvsr(hvsr_data=self.hvsr_data,
                                                   method=self.method_ind,
                                                   smooth=self.hvsmooth_param,
                                                   freq_smooth=self.freq_smooth.get(),
                                                   f_smooth_width=self.fSmoothWidth.get(),
                                                   resample=self.hvresample_int,
                                                   outlier_curve_rmse_percentile=True)
            update_progress_bars(prog_percent=90)


            self.log_text.insert('end', f"{self.checkPeaks_Call['text']}\n\n")
            self.hvsr_results = sprit_hvsr.check_peaks(hvsr_data=self.hvsr_results, 
                                                  hvsr_band = [self.hvsrBand_min.get(), self.hvsrBand_max.get()],
                                                  peak_freq_range=[self.peakFreqRange_min.get(), self.peakFreqRange_max.get()])
            update_progress_bars(prog_percent=95)


            self.log_text.insert('end', f"{self.checkPeaks_Call['text']}\n\n")
            if isinstance(self.hvsr_results, sprit_hvsr.HVSRData):
                report_results(self.hvsr_results)
                self.results_siteSelectFrame.grid_forget()
            elif isinstance(self.hvsr_results, sprit_hvsr.HVSRBatch):
                self.results_siteSelectFrame.grid(row=0, column=0, columnspan=10, sticky='ew')
                report_results(self.hvsr_results[self.hvsr_results.sites[0]])
            else:
                warnings.warn(f'Data is of type {type(self.hvsr_results)}; should be HVSRData or HVSRBatch type.')

            #Log results
            self.log_text.insert('end', f"Processing completed at [{datetime.datetime.now()}]\n\n")
            self.hvsr_results = sprit_hvsr.get_report(self.hvsr_results, report_format='print', no_output=True)
            if isinstance(self.hvsr_results, sprit_hvsr.HVSRData):
                #format data to be same as HVSRBatch
                hvsrResults = {'sitename_placeholder':self.hvsr_results}
            else:
                hvsrResults = self.hvsr_results

            for sitename in hvsrResults.keys():
                self.log_text.insert('end', f"{hvsrResults[sitename]['Print_Report']}\n\n")
            
            self.processingData = False
            self.tab_control.select(self.results_tab)
            update_progress_bars(prog_percent=100)

        global update_progress_bars
        def update_progress_bars(prog_percent, process_name='Processing'):
            progBarListList = [[self.inputProgBar,(0,0), True], 
                                [self.prevProgBar,(0,0), True], 
                                [self.noiseProgBar,(0,0), True], 
                                [self.settingsProgBar_ppsd, (0, 0), True],
                                [self.settingsProgBar_hvsr, (0,0), True],
                                [self.settingsProgBar_plot,(0,0), True], 
                                [self.logProgBar,(0,11), False], 
                                [self.resultsProgBar,(0,26), False]]
            
            def prog_bar_update(progBarListList, progPercent, processName):
                for bar in progBarListList:
                    progBar = bar[0]
                    barLoc = bar[1]

                    progBar['value'] = progPercent

                    if progPercent==0:
                        progBar.master.columnconfigure(0, weight=1)
                        progBar.grid(row=barLoc[0],column=barLoc[1], sticky='ew')
                    elif progPercent==100:
                        progBar.grid_forget()

                    progBar.update()

            threading.Thread(target=prog_bar_update(progBarListList=progBarListList, progPercent=prog_percent, processName=process_name)).start()
            #self.update_idletasks()

        def update_input_params_call():
            prevCall = self.input_params_call.cget('text')
            self.input_params_call.configure(text="input_params( input_data='{}', metadata={}, site='{}', instrument='{}',\n\tnetwork='{}', station='{}', location='{}', channels=[{}, {}, {}], \n\tacq_date='{}', starttime='{}', endttime='{}', tzone='{}', \n\txcoord={}, ycoord={}, elevation={}, input_crs='{}', output_crs='{}', elev_unit='{}',  \n\thvsr_band=[{}, {}], peak_freq_range=[{}, {}])".format(
                                            self.data_path.get(), self.meta_path.get(), self.site_name.get(), self.instrumentSel.get(),
                                            self.network.get(), self.station.get(), self.location.get(),
                                            self.z_channel.get(), self.e_channel.get(), self.n_channel.get(),
                                            self.acq_date, self.starttime.time(), self.endtime.time(), self.tz,
                                            self.x.get(), self.y.get(), self.z.get(), 
                                            self.input_crs.get(), self.output_crs.get(), self.elev_unit.get(), 
                                            self.hvsrBand_min.get(), self.hvsrBand_max.get(),
                                            self.peakFreqRange_min.get(), self.peakFreqRange_max.get()))
            
            newCall = self.input_params_call.cget('text')
            if prevCall==newCall:
                self.data_read=True
            else:
                self.data_read = False

        #Specify site name        
        siteLabel = ttk.Label(hvsrFrame, text="Site Name")
        siteLabel.grid(row=0, column=0, sticky='e', padx=5)
        self.site_name = tk.StringVar()
        self.site_name.set('HVSR Site')
        self.site_name_entry = ttk.Entry(hvsrFrame, textvariable=self.site_name, validate='focusout', validatecommand=update_input_params_call)
        self.site_name_entry.grid(row=0, column=1, columnspan=1, sticky='ew', padx=5)
        
        def on_source_select():
            self.data_read = False
            try:
                str(self.file_source.get())
                sourceLabel.configure(text="source='{}'".format(self.file_source.get()))
                update_fetch_call()

                if self.file_source.get() == 'raw' or self.file_source.get() == 'dir':
                    self.browse_data_filepath_button.configure(text='Browse Folder')
                    self.batch_options_frame.grid_forget()
                elif self.file_source.get() == 'batch':
                    self.batch_options_frame.grid(row=11, column=0, columnspan=7, sticky='ew')
                    self.browse_data_filepath_button.configure(text='Browse File(s)')
                else:
                    self.browse_data_filepath_button.configure(text='Browse File(s)')
                    self.batch_options_frame.grid_forget()
                return True
            except ValueError:
                return False

        sourceLabel = ttk.Label(master=hvsrFrame, text="source='file'")

        ttk.Label(master=hvsrFrame, text='Data Source Type [str]').grid(row=0, column=3, sticky='e', padx=5)
        sourcFrame= ttk.Frame(hvsrFrame)
        sourcFrame.grid(row=0, column=4, sticky='w', columnspan=3)
        self.file_source = tk.StringVar()
        self.file_source.set('file')
        ttk.Radiobutton(master=sourcFrame, text='File', variable=self.file_source, value='file', command=on_source_select).grid(row=0, column=0, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=sourcFrame, text='Raw', variable=self.file_source, value='raw', command=on_source_select).grid(row=0, column=1, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=sourcFrame, text='Batch', variable=self.file_source, value='batch', command=on_source_select).grid(row=0, column=2, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=sourcFrame, text='Directory', variable=self.file_source, value='dir', command=on_source_select).grid(row=0, column=3, sticky='w', padx=(5, 10))

        #Instrument select
        ttk.Label(hvsrFrame, text="Instrument").grid(row=0, column=6, sticky='e', padx=5)
        inst_options = ["Raspberry Shake", "Tromino", "Other"]

        
        def on_option_select(self, inst):
            update_input_params_call()
            if inst == "Raspberry Shake":
                self.network_entry.configure(state='normal')
                self.station_entry.configure(state='normal')
                self.location_entry.configure(state='normal')
                
                self.z_channel_entry.delete(0, 'end')
                self.e_channel_entry.delete(0, 'end')
                self.n_channel_entry.delete(0, 'end')
                
                self.z_channel_entry.insert(0,"EHZ")
                self.e_channel_entry.insert(0,"EHE")
                self.n_channel_entry.insert(0,"EHN")

                self.network_entry.delete(0, 'end')
                self.network_entry.insert(0,"AM")

                self.station_entry.delete(0, 'end')
                self.station_entry.insert(0,"RAC84")

                self.location_entry.delete(0, 'end')
                self.location_entry.insert(0,"00")
            else:
                self.network_entry.configure(state='disabled')
                self.station_entry.configure(state='disabled')
                self.location_entry.configure(state='disabled')

        self.instrumentSel = tk.StringVar(value=inst_options[0])
        self.instrument_dropdown = ttk.OptionMenu(hvsrFrame, self.instrumentSel, inst_options[0], *inst_options, command=on_option_select)
        self.instrument_dropdown.config(width=20)
        self.instrument_dropdown.grid(row=0, column=7, columnspan=1, sticky='ew')

        # Data Filepath
        dataLabel= ttk.Label(hvsrFrame, text="Data Filepath")
        dataLabel.grid(row=1, column=0, sticky='e', padx=5, pady=(5,2.55))
    
        #Function to set self.data_read False whenever the data_path is updated
        
        def on_data_path_change(data_path, index, trace_mode):
            #If our data path changes, data is registered as not having been read
            #This is primarily so that if just the Run button is pushed, it will know to first read the data
            self.data_read = False
        
        def filepath_update():
            self.data_read = False
            self.fpath = self.data_path.get()
            self.data_read = False
            update_input_params_call()

        self.data_path = tk.StringVar()
        self.data_path.set('sample')
        self.fpath = self.data_path.get()
        self.data_path.trace_add('write', on_data_path_change)
        self.data_filepath_entry = ttk.Entry(hvsrFrame, textvariable=self.data_path, validate='focusout', validatecommand=filepath_update)
        self.data_filepath_entry.grid(row=1, column=1, columnspan=6, sticky='ew', padx=5, pady=(5,2.55))

        
        def browse_data_filepath():
            if self.file_source.get() == 'raw' or self.file_source.get() == 'dir':
                self.fpath = filedialog.askdirectory()
                if self.fpath:
                    self.data_filepath_entry.delete(0, 'end')
                    self.data_filepath_entry.insert(0, self.fpath)
            else:
                self.fpath = filedialog.askopenfilenames()
                
                #fpath will always be tuple
                self.no_data_files = len(self.fpath)
                    
                if self.fpath:
                    self.data_filepath_entry.delete(0, 'end')
                    for f in self.fpath:
                        self.data_filepath_entry.insert('end', self.fpath)
                
            update_input_params_call()

        buttonFrame = ttk.Frame(hvsrFrame)
        buttonFrame.grid(row=1, column=7, sticky='ew')

        self.browse_data_filepath_button = ttk.Button(buttonFrame, text="Browse File(s)", command=browse_data_filepath)

        #self.browse_data_filepath_button.grid(row=1, column=6, sticky='ew')
        self.browse_data_filepath_button.pack(side="left", fill="x", expand=True, padx=(0,2), pady=(5,2.55))

        # Metadata Filepath
        ttk.Label(hvsrFrame, text="Metadata Filepath").grid(row=2, column=0, sticky='e', padx=5, pady=(2.5,5))
        self.meta_path = tk.StringVar()
        self.meta_path.set('')
        self.metadata_filepath_entry = ttk.Entry(hvsrFrame, textvariable=self.meta_path, validate='focusout', validatecommand=update_input_params_call)
        self.metadata_filepath_entry.grid(row=2, column=1, columnspan=6, sticky='ew', padx=5, pady=(2.5,5))
        
        
        def browse_metadata_filepath():
            self.data_read = False #New file will not have been read, set to False
            filepath = filedialog.askopenfilename()
            if filepath:
                self.metadata_filepath_entry.delete(0, 'end')
                self.metadata_filepath_entry.insert(0, filepath)
            update_input_params_call()

        self.browse_metadata_filepath_button = ttk.Button(hvsrFrame, text="Browse", command=browse_metadata_filepath)
        self.browse_metadata_filepath_button.grid(row=2, column=7, sticky='ew', padx=0, pady=(2.5,5))

        
        def update_acq_date():
            aMonth = self.acq_month.get()
            if str(aMonth)[0]=='0':
                aMonth = str(aMonth)[-1]

            aDay = self.acq_day.get()
            if str(aDay)[0]=='0':
                aDay = str(aDay)[-1]

            self.acq_date = datetime.date(year=self.acq_year.get(), month=aMonth, day=aDay)
            self.day_of_year = self.acq_date.timetuple().tm_yday
            self.doy_label.configure(text=str(self.day_of_year))
            update_input_params_call()

        # Date and Time
        dateFrame = ttk.Frame(hvsrFrame)
        dateFrame.grid(row=3, column=1, columnspan=2, sticky='e', padx=5)
        ttk.Label(dateFrame, text="Date").grid(row=1, column=1, sticky='e', padx=5)

        self.acq_year = tk.IntVar()
        self.acq_year.set(int(datetime.datetime.today().year))
        self.acq_year_entry = ttk.Spinbox(dateFrame, from_=0, to=10000, width=7, textvariable=self.acq_year, validate='focusout', validatecommand=update_acq_date) 
        self.acq_year_entry.grid(row=1, column=2, sticky='ew', padx=1)

        self.acq_month = tk.IntVar()
        self.acq_month.set(int(datetime.datetime.today().month))
        self.acq_month_entry = ttk.Spinbox(dateFrame, from_=0, to=12, width=3, textvariable=self.acq_month, validate='focusout', validatecommand=update_acq_date) 
        self.acq_month_entry.grid(row=1, column=3, sticky='ew', padx=1)

        self.acq_day = tk.IntVar()
        self.acq_day.set(int(datetime.datetime.today().day))
        self.acq_day_entry = ttk.Spinbox(dateFrame, from_=0, to=31, width=3, textvariable=self.acq_day, validate='focusout', validatecommand=update_acq_date) 
        self.acq_day_entry.grid(row=1, column=4, sticky='ew', padx=1)

        self.acq_date = datetime.date.today()
        
        sTimeFrame = ttk.Frame(hvsrFrame)
        sTimeFrame.grid(row=3, column=4, sticky='ew')

        def get_times():
            #Format starttime as datetime object (in timezone as originally entered)
            self.acq_date = datetime.date(year=self.acq_year.get(), month=self.acq_month.get(), day=self.acq_day.get())

            sHour = self.start_hour.get()
            if str(sHour)[0] == '0':
                sHour = int(str(sHour)[-1])

            sMin = self.start_minute.get()
            if str(sMin)[0] == '0':
                sMin = int(str(sMin)[-1])

            self.starttime = datetime.datetime(year = int(self.acq_date.year),
                                          month = int(self.acq_date.month),
                                          day = int(self.acq_date.day),
                                          hour = int(sHour),
                                          minute = int(sMin),
                                          tzinfo=self.tz)
            
            #Get duration, as originally entered
            hour_dur = self.end_hour.get() - self.start_hour.get()
            if hour_dur < 0:
                hour_dur = self.end_hour.get() + 24 - self.start_hour.get()
            min_dur = self.end_minute.get() - self.start_minute.get()

            #Convert starttime to utc
            #self.starttime = self.tz.normalize(self.tz.localize(self.starttime)).astimezone(pytz.utc)
            self.starttime  = self.starttime.astimezone(datetime.timezone.utc)

            #Get endttime based on utc starttime and original duration
            self.endtime = self.starttime + datetime.timedelta(hours=hour_dur, minutes=min_dur)

            return self.starttime, self.endtime

        self.tz = datetime.timezone.utc

        
        def any_time_change():
            self.data_read = False #New file will not have been read, set to False            
            self.acq_date = datetime.date(year=self.acq_year.get(), month=self.acq_month.get(), day=self.acq_day.get())
            self.starttime, self.endtime = get_times()
            update_input_params_call()

        ttk.Label(hvsrFrame, text="Start Time").grid(row=3, column=3, sticky='e', padx=5) 
        colonLabel= ttk.Label(sTimeFrame, text=":")#.grid(row=3, column=4, padx=(20,0), sticky='w')
        self.start_hour = tk.IntVar()
        self.start_hour.set(00)
        self.start_time_hour_entry = ttk.Spinbox(sTimeFrame, from_=0, to=23, width=5, textvariable=self.start_hour, validate='focusout', validatecommand=any_time_change) 
        self.start_time_hour_entry#.grid(row=3, column=4, sticky='w') 
        self.start_minute = tk.DoubleVar()
        self.start_minute.set(00)
        self.start_time_min_entry = ttk.Spinbox(sTimeFrame, from_=0, to=59, width=5, textvariable=self.start_minute, validate='focusout', validatecommand=any_time_change)
        self.start_time_min_entry#.grid(row=3, column=4, padx=80, sticky='w') 
        
        #sTLabel.pack(side="left", fill="x", expand=True)
        self.start_time_hour_entry.pack(side='left', expand=True)
        colonLabel.pack(side="left", fill="x")
        self.start_time_min_entry.pack(side='right', expand=True)
        
        eTimeFrame = ttk.Frame(hvsrFrame)
        eTimeFrame.grid(row=3, column=6, sticky='ew')
        ttk.Label(hvsrFrame, text="End Time").grid(row=3, column=5, sticky='e', padx=5) 
        colonLabel = ttk.Label(eTimeFrame, text=":")#.grid(row=3, column=6, padx=(20,0), sticky='w')  
        self.end_hour = tk.IntVar()
        self.end_hour.set(23)
        self.end_time_hour_entry = ttk.Spinbox(eTimeFrame, from_=0, to=23, width=5, textvariable=self.end_hour, validate='focusout', validatecommand=any_time_change) 
        self.end_time_hour_entry#.grid(row=3, column=+, sticky='w') 
        self.end_minute = tk.DoubleVar()
        self.end_minute.set(59)
        self.end_time_min_entry = ttk.Spinbox(eTimeFrame, from_=0, to=59, width=5, textvariable=self.end_minute, validate='focusout', validatecommand=any_time_change)
        self.end_time_min_entry#.grid(row=3, column=+, padx=80, sticky='w') 

        #eTLabel.pack(side="left", fill="x", expand=True)
        self.end_time_hour_entry.pack(side='left', expand=True)
        colonLabel.pack(side="left", fill="x")
        self.end_time_min_entry.pack(side='right', expand=True)

        self.acq_date = datetime.date(year=self.acq_year.get(), month=self.acq_month.get(), day=self.acq_day.get())
        self.starttime, self.endtime = get_times()

        
        def onTimezoneSelect(event):
            #Listbox "loses" selection and triggers an event sometimes, so need to check if that is just what happened
            if self.timezone_listbox.curselection():
                #If it was an actual selection, update timezone
                self.tz = zoneinfo.ZoneInfo(self.timezone_listbox.get(self.timezone_listbox.curselection()))
            else:
                #If it was just the listbox losing the selection, don't change anything
                pass
            update_input_params_call()

        self.timezone_listbox = tk.Listbox(hvsrFrame, selectmode='browse', height=25)

        self.timezone_listbox.insert('end', 'UTC')
        self.timezone_listbox.insert('end', 'US/Central')

        for tz in zoneinfo.available_timezones():# pytz.all_timezones:
            if tz !='UTC':
                self.timezone_listbox.insert('end', tz)
        self.timezone_listbox.selection_set(0)
        self.timezone_listbox.bind('<<ListboxSelect>>', onTimezoneSelect)

        ttk.Label(hvsrFrame,text="Timezone").grid(row=3,column=7, sticky='w', padx=5)
        self.timezone_listbox.grid(row=4,column=7, rowspan=26, sticky='nsew', padx=5)

        # DOY
        self.day_of_year = self.acq_date.timetuple().tm_yday

        ttk.Label(hvsrFrame,text="Day of Year:").grid(row=4, column=1, sticky='e', padx=5, pady=10)
        self.doy_label = ttk.Label(hvsrFrame, text=str(self.day_of_year))
        self.doy_label.grid(row=4, column=2, sticky='w')

        # UTC Time Output
        ttk.Label(hvsrFrame,text="UTC Time:").grid(row=4, column=3, sticky='e', padx=5, pady=10)
        self.utc_time_output_label = ttk.Label(hvsrFrame, text="")
        self.utc_time_output_label.grid(row=4, column=4)

        # Initialize as UTC
        self.tz = datetime.timezone.utc


        self.starttime, self.endtime = get_times()

        # X Y Z CRS Depth
        ttk.Label(hvsrFrame,text="X").grid(row=5,column=1, sticky='e', padx=5, pady=10)
        self.x = tk.DoubleVar()
        self.x.set(0)
        self.x_entry = ttk.Entry(hvsrFrame, textvariable=self.x, validate='focusout', validatecommand=update_input_params_call)
        self.x_entry.grid(row=5,column=2, sticky='w', padx=0)

        ttk.Label(hvsrFrame,text="Y").grid(row=5,column=3, sticky='e', padx=5, pady=10)
        self.y = tk.DoubleVar()
        self.y.set(0)
        self.y_entry = ttk.Entry(hvsrFrame, textvariable=self.y, validate='focusout', validatecommand=update_input_params_call)
        self.y_entry.grid(row=5, column=4, sticky='w', padx=0)

        ttk.Label(hvsrFrame,text="Z").grid(row=5,column=5, sticky='e', padx=5, pady=10)
        self.z = tk.DoubleVar()
        self.z.set(0)
        self.z_entry = ttk.Entry(hvsrFrame, textvariable=self.z, validate='focusout', validatecommand=update_input_params_call)
        self.z_entry.grid(row=5,column=6, sticky='w', padx=0)

        ttk.Label(hvsrFrame,text="Input CRS").grid(row=6,column=1, sticky='e', padx=5, pady=10)
        self.input_crs = tk.StringVar()
        self.input_crs.set('EPSG:4326')
        self.input_crs_entry = ttk.Entry(hvsrFrame, textvariable=self.input_crs, validate='focusout', validatecommand=update_input_params_call)
        self.input_crs_entry.grid(row=6,column=2, sticky='w', padx=0)

        ttk.Label(hvsrFrame,text="Output CRS").grid(row=6,column=3, sticky='e', padx=5, pady=10)
        self.output_crs = tk.StringVar()
        self.output_crs.set('EPSG:4326')
        self.output_crs_entry = ttk.Entry(hvsrFrame, textvariable=self.output_crs, validate='focusout', validatecommand=update_input_params_call)
        self.output_crs_entry.grid(row=6, column=4, sticky='w', padx=0)

        ttk.Label(master=hvsrFrame, text='Elevation Unit').grid(row=6, column=5, sticky='e', padx=5, pady=10)
        elevUnitFrame= ttk.Frame(hvsrFrame)
        elevUnitFrame.grid(row=6, column=6, sticky='w', columnspan=3)
        self.elev_unit = tk.StringVar()
        self.elev_unit.set('meters')
        ttk.Radiobutton(master=elevUnitFrame, text='Meters', variable=self.elev_unit, value='meters', command=update_input_params_call).grid(row=0, column=0, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=elevUnitFrame, text='Feet', variable=self.elev_unit, value='feet', command=update_input_params_call).grid(row=0, column=1, sticky='w', padx=(5, 10))

        # Network Station Location
        ttk.Label(hvsrFrame,text="Network").grid(row=7,column=1, sticky='e', padx=5, pady=10)
        self.network = tk.StringVar()
        self.network.set('AM')
        self.network_entry = ttk.Entry(hvsrFrame, textvariable=self.network, validate='focusout', validatecommand=update_input_params_call)
        self.network_entry.grid(row=7,column=2, sticky='w', padx=0)

        ttk.Label(hvsrFrame,text="Station").grid(row=7,column=3, sticky='e', padx=5, pady=10)
        self.station = tk.StringVar()
        self.station.set('RAC84')
        self.station_entry = ttk.Entry(hvsrFrame, textvariable=self.station, validate='focusout', validatecommand=update_input_params_call)
        self.station_entry.grid(row=7,column=4, sticky='w', padx=0)

        ttk.Label(hvsrFrame,text="Location").grid(row=7,column=5, sticky='e', padx=5, pady=10)
        self.location = tk.StringVar()
        self.location.set('00')
        self.location_entry = ttk.Entry(hvsrFrame, textvariable=self.location, validate='focusout', validatecommand=update_input_params_call)
        self.location_entry.grid(row=7,column=6, sticky='w', padx=0)

        # Z N E Channels
        ttk.Label(hvsrFrame,text="Z Channel").grid(row=8,column=1, sticky='e', padx=5, pady=10)
        self.z_channel = tk.StringVar()
        self.z_channel.set('EHZ')
        self.z_channel_entry = ttk.Entry(hvsrFrame, textvariable=self.z_channel, validate='focusout', validatecommand=update_input_params_call)
        self.z_channel_entry.grid(row=8,column=2, sticky='w', padx=0)

        ttk.Label(hvsrFrame,text="N Channel").grid(row=8,column=3, sticky='e', padx=5, pady=10)
        self.n_channel = tk.StringVar()
        self.n_channel.set('EHN')
        self.n_channel_entry = ttk.Entry(hvsrFrame, textvariable=self.n_channel, validate='focusout', validatecommand=update_input_params_call)
        self.n_channel_entry.grid(row=8,column=4, sticky='w', padx=0)

        ttk.Label(hvsrFrame,text="E Channel").grid(row=8,column=5, sticky='e', padx=5, pady=10)
        self.e_channel = tk.StringVar()
        self.e_channel.set('EHE')
        self.e_channel_entry = ttk.Entry(hvsrFrame, textvariable=self.e_channel, validate='focusout', validatecommand=update_input_params_call)
        self.e_channel_entry.grid(row=8,column=6, sticky='w', padx=0)

        # HVSR Band
        def on_hvsrband_update():
            try:
                float(self.hvsrBand_min.get())
                float(self.hvsrBand_max.get())

                hvsrBandLabel.configure(text='hvsr_band=[{}, {}]'.format(self.hvsrBand_min.get(), self.hvsrBand_max.get()))                
                update_check_peaks_call(self.checkPeaks_Call)
                update_input_params_call()
                return True
            except ValueError:
                return False      
        
        ttk.Label(hvsrFrame,text="HVSR Band").grid(row=9,column=1, sticky='e', padx=10, pady=10)
        hvsrbandframe= ttk.Frame(hvsrFrame)
        hvsrbandframe.grid(row=9, column=2,sticky='w')
        self.hvsrBand_min = tk.DoubleVar()
        self.hvsrBand_min.set(0.4)
        hvsr_band_min_entry = ttk.Entry(hvsrbandframe, width=9, textvariable=self.hvsrBand_min, validate='focusout', validatecommand=on_hvsrband_update)
        hvsr_band_min_entry.grid(row=0, column=0, sticky='ew', padx=(0,2))

        self.hvsrBand_max = tk.DoubleVar()
        self.hvsrBand_max.set(40)
        hvsr_band_max_entry = ttk.Entry(hvsrbandframe, width=9,textvariable=self.hvsrBand_max, validate='focusout', validatecommand=on_hvsrband_update)
        hvsr_band_max_entry.grid(row=0,column=1, sticky='ew', padx=(2,0))

        # Peak Freq Range Band
        def on_peakFreqRange_update():
            try:
                float(self.peakFreqRange_min.get())
                float(self.peakFreqRange_max.get())

                peakFreqRangeLabel.configure(text='peak_freq_range=[{}, {}]'.format(self.peakFreqRange_min.get(), self.peakFreqRange_max.get()))                
                update_check_peaks_call(self.checkPeaks_Call)
                update_input_params_call()
                return True
            except ValueError:
                return False      
        
        ttk.Label(hvsrFrame,text="Peak Freq. Range").grid(row=9,column=3, sticky='e', padx=10, pady=10)
        peakFreqRangeframe= ttk.Frame(hvsrFrame)
        peakFreqRangeframe.grid(row=9, column=4,sticky='w')
        self.peakFreqRange_min = tk.DoubleVar()
        self.peakFreqRange_min.set(0.4)
        peakFreqRange_min_entry = ttk.Entry(peakFreqRangeframe, width=9, textvariable=self.peakFreqRange_min, validate='focusout', validatecommand=on_peakFreqRange_update)
        peakFreqRange_min_entry.grid(row=0, column=0, sticky='ew', padx=(0,2))

        self.peakFreqRange_max = tk.DoubleVar()
        self.peakFreqRange_max.set(40)
        peakFreqRange_max_entry = ttk.Entry(peakFreqRangeframe, width=9,textvariable=self.peakFreqRange_max, validate='focusout', validatecommand=on_peakFreqRange_update)
        peakFreqRange_max_entry.grid(row=0,column=1, sticky='ew', padx=(2,0))

        #BATCH Section
        def update_batch_data_read_call():
            self.batch_read_data_call.configure(text="batch_data_read(input_data, batch_type='{}', param_col={}, batch_params={})".format(
                                                                                        self.batch_type.get(), self.param_col.get(), self.batch_params.get()))
            return
        
        def on_batch_type_select():
            update_batch_data_read_call()
            return

        self.batch_options_frame = ttk.LabelFrame(hvsrFrame, text='Batch Options')
        ttk.Label(self.batch_options_frame, text="Batch Type").grid(row=0,column=0, sticky='e', padx=10, pady=10)
        batchTypeFrame= ttk.Frame(self.batch_options_frame)
        batchTypeFrame.grid(row=0, column=1, sticky='w', columnspan=3)
        self.batch_type = tk.StringVar()
        self.batch_type.set('table')
        ttk.Radiobutton(master=batchTypeFrame, text='Table', variable=self.batch_type, value='table', command=on_batch_type_select).grid(row=0, column=0, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=batchTypeFrame, text='File list', variable=self.batch_type, value='filelist', command=on_batch_type_select).grid(row=0, column=1, sticky='w', padx=(5, 10))

        ttk.Label(self.batch_options_frame,text="Parameter column name").grid(row=0,column=4, sticky='e', padx=5)
        self.param_col = tk.StringVar()
        self.param_col.set(None)
        self.param_col_entry = ttk.Entry(self.batch_options_frame, textvariable=self.param_col, validate='focusout', validatecommand=update_batch_data_read_call)
        self.param_col_entry.grid(row=0, column=5, sticky='w', padx=0)
        ttk.Label(self.batch_options_frame,text="For batch_type='table' with single parameter column only").grid(row=1,column=4, columnspan=2, sticky='w', padx=5)

        ttk.Label(self.batch_options_frame,text="Batch parameters").grid(row=0,column=6, sticky='e', padx=5)
        self.batch_params = tk.StringVar()
        self.batch_params.set(None)
        self.batch_params_entry = ttk.Entry(self.batch_options_frame, textvariable=self.batch_params, validate='focusout', validatecommand=update_batch_data_read_call, width=75)
        self.batch_params_entry.grid(row=0, column=7, columnspan=3, sticky='ew', padx=0)
        ttk.Label(self.batch_options_frame,text="To specify parameters used for reading in data").grid(row=1,column=6, columnspan=2, sticky='w', padx=5)

        self.batch_read_data_call = ttk.Label(self.batch_options_frame, text="batch_data_read(input_data, batch_type={}, param_col={}, batch_params={})".format(
                                                                                        self.batch_type.get(), self.param_col.get(), self.batch_params.get() ))
        self.batch_read_data_call.grid(row=2,column=0, columnspan=10, sticky='w', padx=10, pady=10)

        self.batch_options_frame.grid(row=11, column=0, columnspan=7, sticky='ew')
        self.batch_options_frame.grid_forget()
        
        separator = ttk.Separator(hvsrFrame, orient='horizontal')
        separator.grid(row=12, column=0, columnspan=7, sticky='ew', padx=10)

        
        def update_fetch_call():
            prevCall = self.input_params_call.cget('text')
            if self.trim_dir.get()=='':
                trim_dir = None
            else:
                trim_dir = self.trim_dir.get()
            self.data_read = False #New file will not have been read, set to False
            self.fetch_data_call.configure(text="fetch_data(params, source='{}', trim_dir={}, export_format='{}', detrend='{}', detrend_options={})"
                                            .format(self.file_source.get(), trim_dir, self.export_format.get(), self.detrend.get(), self.detrend_options.get()))
            
            newCall = self.input_params_call.cget('text')
            if prevCall==newCall:
                self.data_read=True
            else:
                self.data_read = False
        #export_format='.mseed'
        
        def on_obspyFormatSelect(self):
            update_fetch_call()
        ttk.Label(hvsrFrame, text="Data Format").grid(row=13, column=1, sticky='e', padx=5)
        obspyformats =  ['AH', 'ALSEP_PSE', 'ALSEP_WTH', 'ALSEP_WTN', 'CSS', 'DMX', 'GCF', 'GSE1', 'GSE2', 'KINEMETRICS_EVT', 'KNET', 'MSEED', 'NNSA_KB_CORE', 'PDAS', 'PICKLE', 'Q', 'REFTEK130', 'RG16', 'SAC', 'SACXY', 'SEG2', 'SEGY', 'SEISAN', 'SH_ASC', 'SLIST', 'SU', 'TSPAIR', 'WAV', 'WIN', 'Y']

        self.export_format = tk.StringVar(value=obspyformats[11])
        self.data_format_dropdown = ttk.OptionMenu(hvsrFrame, self.export_format, obspyformats[11], *obspyformats, command=on_obspyFormatSelect)
        self.data_format_dropdown.grid(row=13, column=2, columnspan=3, sticky='ew')

        #detrend='spline'
        
        def on_detrend_select():
            try:
                str(self.detrend.get())
                update_fetch_call()
                return True
            except ValueError:
                return False

        sourceLabel = ttk.Label(master=hvsrFrame, text="source='raw'")

        ttk.Label(master=hvsrFrame, text='Detrend type [str]').grid(row=14, column=1, sticky='e', padx=5)
        detrendFrame= ttk.Frame(hvsrFrame)
        detrendFrame.grid(row=14, column=2, sticky='w', columnspan=3)
        self.detrend = tk.StringVar()
        self.detrend.set('spline')
        ttk.Radiobutton(master=detrendFrame, text='Spline', variable=self.detrend, value='spline', command=on_detrend_select).grid(row=0, column=0, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=detrendFrame, text='Polynomial', variable=self.detrend, value='polynomial', command=on_detrend_select).grid(row=0, column=1, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=detrendFrame, text='None', variable=self.detrend, value='none', command=on_detrend_select).grid(row=0, column=2, sticky='w', padx=(5, 10))

        #detrend_options=2
        
        def on_detrend_order():
            try:
                int(self.detrend_options.get())
                update_fetch_call()
                return True
            except ValueError:
                return False
                     
        ttk.Label(hvsrFrame,text="Detrend Order [int]").grid(row=14,column=5, sticky='e', padx=5, pady=10)
        self.detrend_options = tk.IntVar()
        self.detrend_options.set(2)
        self.detrend_order_entry = ttk.Entry(hvsrFrame, textvariable=self.detrend_options, validate='focusout', validatecommand=on_detrend_order)
        self.detrend_order_entry.grid(row=14,column=6, sticky='w', padx=0)
        
        #trim_dir=False
        def on_trim_dir():
            try:
                str(self.trim_dir.get())
                update_fetch_call()
                return True
            except ValueError:
                return False
            
        ttk.Label(hvsrFrame, text="Output Directory (trimmed data)").grid(row=15, column=0, sticky='e', padx=5, pady=(2.5,5))
        self.trim_dir = tk.StringVar()
        self.trim_dir_entry = ttk.Entry(hvsrFrame, textvariable=self.trim_dir, validate='focusout', validatecommand=on_trim_dir)
        self.trim_dir_entry.grid(row=15, column=1, columnspan=5, sticky='ew', padx=5, pady=(2.5,5))
        
        
        def browse_trim_dir_filepath():
            filepath = filedialog.askdirectory()
            if filepath:
                self.trim_dir_entry.delete(0, 'end')
                self.trim_dir_entry.insert(0, filepath)
        
        self.trim_dir_filepath_button = ttk.Button(hvsrFrame, text="Browse", command=browse_trim_dir_filepath)
        self.trim_dir_filepath_button.grid(row=15, column=6, sticky='ew', padx=0, pady=(2.5,5))

        #self.starttime, self.endtime = get_times()
        input_params_LF = ttk.LabelFrame(master=self.input_tab, text='input_params() call')
        self.input_params_call = ttk.Label(master=input_params_LF, text="input_params( input_data='{}', metadata={}, site='{}', instrument='{}',\n\tnetwork='{}', station='{}', location='{}', channels=[{}, {}, {}], \n\tacq_date='{}', starttime='{}', endttime='{}', tzone='{}', \n\txcoord={}, ycoord={}, elevation={}, input_crs='{}', output_crs='{}', elev_unit='{}',   \n\thvsr_band=[{}, {}], peak_freq_range=[{}, {}])".format(
                                            self.data_path.get(), self.meta_path.get(), self.site_name.get(), self.instrumentSel.get(),
                                            self.network.get(), self.station.get(), self.location.get(),
                                            self.z_channel.get(), self.e_channel.get(), self.n_channel.get(),
                                            self.acq_date, self.starttime.time(), self.endtime.time(), self.tz,
                                            self.x.get(), self.y.get(), self.z.get(), 
                                            self.input_crs.get(), self.output_crs.get(), self.elev_unit.get(), 
                                            self.hvsrBand_min.get(), self.hvsrBand_max.get(),
                                            self.peakFreqRange_min.get(), self.peakFreqRange_max.get()))
        self.input_params_call.pack(anchor='w', expand=True, padx=20)

        #fetch_data() call
        fetch_data_LF = ttk.LabelFrame(master=self.input_tab, text='fetch_data() call')
        self.fetch_data_call = ttk.Label(master=fetch_data_LF, text="fetch_data(params, source={}, trim_dir={}, export_format={}, detrend={}, detrend_options={})"
                                                                .format(self.file_source.get(), None, self.export_format.get(), self.detrend.get(), self.detrend_options.get()))
        self.fetch_data_call.pack(anchor='w', expand=True, padx=20)

        #Set up frame for reading and running
        runFrame_hvsr = ttk.Frame(self.input_tab)
        runFrame_hvsr.columnconfigure(0, weight=1)

        self.inputProgBar = ttk.Progressbar(runFrame_hvsr, orient='horizontal')
        self.inputProgBar.grid(row=0, column=0, sticky='ew')#.pack(fill='both',expand=True, side='left', anchor='sw')

        self.style.configure(style='Custom.TButton', background='#d49949')
        self.read_button = ttk.Button(runFrame_hvsr, text="Read Data", command=read_data, width=30, style='Custom.TButton')

        self.style.configure('Run.TButton', background='#8b9685', width=10, height=3)
        self.run_button = ttk.Button(runFrame_hvsr, text="Run", style='Run.TButton', command=process_data)        
        self.run_button.grid(row=0, column=2, sticky='nsew', padx=2.5)#.pack(side='right', anchor='se', padx=(10,0))
        self.read_button.grid(row=0, column=1, sticky='nsew', padx=2.5)#.pack(side='right', anchor='se')

        hvsrFrame.pack(fill='both', expand=True, side='top')#.grid(row=0, sticky="nsew")
        runFrame_hvsr.pack(fill='both', side='bottom')
        fetch_data_LF.pack(fill='x', side='bottom')
        input_params_LF.pack(fill='x', side='bottom')
        self.input_tab.pack(fill='both', expand=True)
        self.tab_control.add(self.input_tab, text="Input")

        #Data Preview Tab
        self.preview_data_tab = ttk.Frame(self.tab_control)

        # Configure the row and column of the input_tab to have a non-zero weight
        self.preview_data_tab.pack(expand=1)

        self.inputdataFrame = ttk.LabelFrame(self.preview_data_tab, text="Input Data Viewer")
        self.inputdataFrame.pack(expand=True, fill='both')
            
        self.inputInfoFrame = ttk.LabelFrame(self.inputdataFrame, text="Input Data Info")
        self.input_data_label = ttk.Label(self.inputInfoFrame, text=self.data_filepath_entry.get())
        self.input_data_label.pack(anchor='w', fill='both', expand=True, padx=15)                
        self.inputInfoFrame.pack(expand=True, fill='both', side='top')
        
        self.inputDataViewFrame = ttk.LabelFrame(self.inputdataFrame, text="Input Data Plot")
                    
        ttk.Label(master=self.inputInfoFrame, text=self.data_filepath_entry.get()).pack()#.grid(row=0, column=0)

        #Set up plot
        #Reset axes, figure, and canvas widget
        self.fig_pre = plt.figure()

        prev_mosaic = [['Z'],['N'],['E']]
        self.ax_pre = self.fig_pre.subplot_mosaic(prev_mosaic, sharex=True)  

        self.canvas_pre = FigureCanvasTkAgg(self.fig_pre, master=self.inputDataViewFrame)  # A tk.DrawingArea.
        self.canvas_pre.draw()
        self.canvasPreWidget = self.canvas_pre.get_tk_widget()#.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.preview_toolbar = NavigationToolbar2Tk(self.canvas_pre, self.inputDataViewFrame, pack_toolbar=False)
        self.preview_toolbar.update()
    
        #self.canvas_pre.mpl_connect("button_release_event", select_windows)

        #Save preview figure
        savePrevFigFrame = ttk.Frame(master=self.inputDataViewFrame)
        
        ttk.Label(savePrevFigFrame, text="Export Figure").grid(row=0, column=0, sticky='ew', padx=5)
        self.previewFig_dir = tk.StringVar()
        self.previewFig_dir_entry = ttk.Entry(savePrevFigFrame, textvariable=self.previewFig_dir)
        self.previewFig_dir_entry.grid(row=0, column=1, columnspan=5, sticky='ew')
        
        
        def filepath_preview_fig():
            filepath = filedialog.asksaveasfilename(defaultextension='.png', initialdir=pathlib.Path(self.data_path.get()).parent)
            if filepath:
                self.previewFig_dir_entry.delete(0, 'end')
                self.previewFig_dir_entry.insert(0, filepath)
        
        
        def save_preview_fig():
            self.fig_pre.savefig(self.previewFig_dir.get())
        
        self.browsePreviewFig = ttk.Button(savePrevFigFrame, text="Browse",command=filepath_preview_fig)
        self.browsePreviewFig.grid(row=0, column=7, sticky='ew', padx=2.5)
        
        self.savePreviewFig = ttk.Button(savePrevFigFrame, text="Save",command=save_preview_fig)
        self.savePreviewFig.grid(row=0, column=8, columnspan=2, sticky='ew', padx=2.5)

        savePrevFigFrame.columnconfigure(1, weight=1)

        savePrevFigFrame.pack(side='bottom', fill='both', expand=False)
        self.preview_toolbar.pack(side=tk.BOTTOM, fill=tk.X)            
        self.canvasPreWidget.pack(fill='both', expand=True)#.grid(row=0, column=0, sticky='nsew')

        self.inputDataViewFrame.pack(expand=True, fill='both', side='bottom')
        
        #preview-Run button
        runFrame_dataPrev = ttk.Frame(self.preview_data_tab)
        runFrame_dataPrev.columnconfigure(0, weight=1)

        self.prevProgBar = ttk.Progressbar(runFrame_dataPrev, orient='horizontal')
        self.prevProgBar.grid(row=0, column=0, sticky='ew')#.pack(fill='both',expand=True, side='left', anchor='sw')

        self.run_button = ttk.Button(runFrame_dataPrev, text="Run", style='Run.TButton', command=process_data)
        self.run_button.grid(row=0, column=1, sticky='nsew', padx=2.5)#.pack(side='bottom', anchor='e')#.grid(row=2, column=9, columnspan=20, sticky='e')
        runFrame_dataPrev.pack(side='bottom', anchor='e', fill='both')#grid(row=1, sticky='e')

        self.tab_control.add(self.preview_data_tab, text="Data Preview")

        # NOISE TAB
        self.noise_tab = ttk.Frame(self.tab_control)
        self.canvasFrame_noise = ttk.LabelFrame(self.noise_tab, text='Noise Viewer')

        #Helper function for updating the canvas and drawing/deleted the boxes
        
        def __draw_windows(event, pathlist, ax_key, windowDrawn, winArtist, xWindows, fig, ax):
            """Helper function for updating the canvas and drawing/deleted the boxes"""
            for i, pa in enumerate(pathlist):
                for j, p in enumerate(pa): 
                    if windowDrawn[i][j]:
                        pass
                    else:
                        patch = matplotlib.patches.PathPatch(p, facecolor='k', alpha=0.75)                            
                        winArt = ax[ax_key].add_patch(patch)
                        windowDrawn[i][j] = True
                        winArtist[i][j] = winArt

            if event.button is MouseButton.RIGHT:
                fig.canvas.draw()

        #Helper function for manual window selection 
        
        def __draw_boxes(event, clickNo, xWindows, pathList, windowDrawn, winArtist, lineArtist, x0, fig, ax):
            """Helper function for manual window selection to draw boxes to show where windows have been selected for removal"""
            #Create an axis dictionary if it does not already exist so all functions are the same

            if isinstance(ax, np.ndarray) or isinstance(ax, dict):
                ax = ax
            else:
                ax = {'a':ax}

            
            if len(ax) > 1:
                if type(ax) is not dict:
                    axDict = {}
                    for i, a in enumerate(ax):
                        axDict[str(i)] = a
                    ax = axDict
            #else:
            #    ax = {'a':ax}
            
            #if event.inaxes!=ax: return
            #y0, y1 = ax.get_ylim()
            y0 = []
            y1 = []
            kList = []
            for k in ax.keys():
                kList.append(k)
                y0.append(ax[k].get_ylim()[0])
                y1.append(ax[k].get_ylim()[1])
            #else:
            #    y0 = [ax.get_ylim()[0]]
            #    y1 = [ax.get_ylim()[1]]

            if self.clickNo == 0:
                #y = np.linspace(ax.get_ylim()[0], ax.get_ylim()[1], 2)
                self.x0 = event.xdata
                self.clickNo = 1   
                self.lineArtist.append([])
                winNums = len(self.xWindows)
                for i, k in enumerate(ax.keys()):
                    linArt = ax[k].axvline(self.x0, 0, 1, color='k', linewidth=1, zorder=100)
                    self.lineArtist[winNums].append([linArt, linArt])
                #else:
                #    linArt = plt.axvline(self.x0, y0[i], y1[i], color='k', linewidth=1, zorder=100)
                #    self.lineArtist.append([linArt, linArt])
            else:
                x1 = event.xdata
                self.clickNo = 0

                windowDrawn.append([])
                winArtist.append([])  
                pathList.append([])
                winNums = len(self.xWindows)
                for i, key in enumerate(kList):
                    path_data = [
                        (matplotlib.path.Path.MOVETO, (self.x0, y0[i])),
                        (matplotlib.path.Path.LINETO, (x1, y0[i])),
                        (matplotlib.path.Path.LINETO, (x1, y1[i])),
                        (matplotlib.path.Path.LINETO, (self.x0, y1[i])),
                        (matplotlib.path.Path.LINETO, (self.x0, y0[i])),
                        (matplotlib.path.Path.CLOSEPOLY, (self.x0, y0[i])),
                    ]
                    codes, verts = zip(*path_data)
                    path = matplotlib.path.Path(verts, codes)

                    windowDrawn[winNums].append(False)
                    winArtist[winNums].append(None)

                    pathList[winNums].append(path)
                    __draw_windows(event=event, pathlist=pathList, ax_key=key, windowDrawn=windowDrawn, winArtist=winArtist, xWindows=self.xWindows, fig=fig, ax=ax)
                    linArt = ax[key].axvline(x1, 0, 1, color='k', linewidth=0.5, zorder=100)

                    [self.lineArtist[winNums][i].pop(-1)]
                    self.lineArtist[winNums][i].append(linArt)
                x_win = [self.x0, x1]
                x_win.sort() #Make sure they are in the right order
                self.xWindows.append(x_win)
            fig.canvas.draw()
            return self.clickNo, self.x0

        #Helper function for manual window selection to draw boxes to deslect windows for removal
        
        def __remove_on_right(event, xWindows, pathList, windowDrawn, winArtist,  lineArtist, fig, ax):
            """Helper function for manual window selection to draw boxes to deslect windows for removal"""

            if self.xWindows is not None:
                for i, xWins in enumerate(self.xWindows):
                    if event.xdata > xWins[0] and event.xdata < xWins[1]:
                        linArtists = self.lineArtist[i]
                        pathList.pop(i)
                        for j, a in enumerate(linArtists):
                            winArtist[i][j].remove()#.pop(i)
                            self.lineArtist[i][j][0].remove()#.pop(i)#[i].pop(j)
                            self.lineArtist[i][j][1].remove()
                        windowDrawn.pop(i)
                        self.lineArtist.pop(i)#[i].pop(j)
                        winArtist.pop(i)#[i].pop(j)
                        self.xWindows.pop(i)
            fig.canvas.draw() 
               
        
        def select_windows(event, input=None, initialize=False):
            """Function to manually select windows for exclusion from data.

            Parameters
            ----------
            input : dict
                Dictionary containing all the hvsr information.

            Returns
            -------
            self.xWindows : list
                List of two-item lists containing start and end times of windows to be removed.
            """
            from matplotlib.backend_bases import MouseButton
            import matplotlib.pyplot as plt
            
            #self.fig_noise, self.ax_noise = sprit_hvsr._plot_simple_stream_obspy(stream=input['stream'], params=input, fig=self.fig_noise, ax=self.ax_noise, component='Z', stack_type='linear', detrend='mean', fill_gaps=0, dbscale=True, return_fig=True, cmap_per=[0.1,0.9])
            #self.fig_noise.canvas.draw()
            
            #if 'stream' in input.keys():
            #    self.fig_noise, self.ax_noise = sprit_hvsr._plot_simple_stream_obspy(stream=self.params['stream'], params=self.params, fig=self.fig_noise, ax=self.ax_noise, component='Z', stack_type='linear', detrend='mean', fill_gaps=0, dbscale=True, return_fig=True, cmap_per=[0.1,0.9])
            #else:
            #    params = input.copy()
            #    input = input['stream']
            
            #if isinstance(input, obspy.core.stream.Stream):
            #    fig, ax = sprit_hvsr._plot_simple_stream_obspy(input, component=['Z'])
            #elif isinstance(input, obspy.core.trace.Trace):
            #    fig, ax = sprit_hvsr._plot_simple_stream_obspy(input)
            if initialize:
                self.lineArtist = []
                self.winArtist = []
                self.windowDrawn = []
                self.pathList = []
                self.xWindows = []
                self.x0 = 0
                self.clickNo = 0
            
            if not initialize:
                __on_click(event)
                self.hvsr_data['xwindows_out'] = self.xWindows


                #self.fig_closed
                #fig_closed = False
                #while fig_closed is False:
                #    #fig.canvas.mpl_connect('button_press_event', __on_click)#(self.clickNo, self.xWindows, pathList, windowDrawn, winArtist, lineArtist, self.x0, fig, ax))
                #    fig.canvas.mpl_connect('close_event', _on_fig_close)#(self.clickNo, self.xWindows, pathList, windowDrawn, winArtist, lineArtist, self.x0, fig, ax))
                #    plt.pause(0.5)
                
                #output['xwindows_out'] = self.xWindows
                #output['fig'] = fig
                #output['ax'] = ax
                noEvent = True
            return self.hvsr_data

        #Support function to help select_windows run properly
        
        def _on_fig_close(event):
            #self.fig_closed
            fig_closed = True
            return

        
        def __on_click(event):

            if event.button is MouseButton.RIGHT:
                __remove_on_right(event, self.xWindows, self.pathList, self.windowDrawn, self.winArtist, self.lineArtist, self.fig_noise, self.ax_noise)

            if event.button is MouseButton.LEFT:            
                self.clickNo, self.x0 = __draw_boxes(event, self.clickNo, self.xWindows, self.pathList, self.windowDrawn, self.winArtist, self.lineArtist, self.x0, self.fig_noise, self.ax_noise)    
        
        #if 'hvsr_data' not in dir(self):
        #    self.hvsr_data = {'placeholder':None}
            
        def plot_noise_windows(hvsr_data={'placeholder':None}, initial_setup=False):
            if 'hvsr_data' in dir(self):
                hvsr_data = self.hvsr_data
                
            if isinstance(hvsr_data, sprit_hvsr.HVSRBatch):
                batch_data = hvsr_data.copy()
                hvsr_data = hvsr_data[list(hvsr_data.keys())[0]]
            else:
                batch_data = None

            if initial_setup:
                self.xWindows=[]
            else:
                #Clear everything
                for key in self.ax_noise:
                    self.ax_noise[key].clear()
                self.fig_noise.clear()

                #Really make sure it's out of memory
                self.fig_noise = []
                self.ax_noise = []
                try:
                    self.fig_noise.get_children()
                except:
                    pass
                try:
                    self.ax_noise.get_children()
                except:
                    pass

            #Reset axes, figure, and canvas widget
            self.fig_noise = plt.figure()
    
            noise_mosaic = [['spec'],['spec'],['spec'],
                    ['spec'],['spec'],['spec'],
                    ['signalz'],['signalz'], ['signaln'], ['signale']]
            self.ax_noise = self.fig_noise.subplot_mosaic(noise_mosaic, sharex=True)  


            if not initial_setup:
                self.noise_canvasWidget.destroy()
                self.noise_toolbar.destroy()
                self.fig_noise = sprit_plot._plot_simple_stream_obspy(stream=hvsr_data['stream'], hv_data=hvsr_data, fig=self.fig_noise, ax=self.ax_noise, component='Z', stack_type='linear', detrend='mean', fill_gaps=0, dbscale=True, return_fig=True, cmap_per=[0.1,0.9])

            self.noise_canvas = FigureCanvasTkAgg(self.fig_noise, master=self.canvasFrame_noise)  # A tk.DrawingArea.
            self.noise_canvas.draw()
            #self.noise_canvasWidget = self.noise_canvas.get_tk_widget()#.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            # pack_toolbar=False will make it easier to use a layout manager later on.
            self.noise_toolbar = NavigationToolbar2Tk(self.noise_canvas, self.canvasFrame_noise, pack_toolbar=False)
            self.noise_toolbar.update()
        
            self.noise_canvasWidget = self.noise_canvas.get_tk_widget()#.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            self.noise_canvas.mpl_connect("button_release_event", select_windows)

            self.noise_toolbar.pack(side=tk.BOTTOM, fill=tk.X)            
            self.noise_canvasWidget.pack(fill='both')#.grid(row=0, column=0, sticky='nsew')

            if not initial_setup:
                if batch_data is None:
                    hvsr_data = {'SITENAME':hvsr_data}
                else:
                    hvsr_data = batch_data

                for i, (k, hv_data) in enumerate(hvsr_data.items()):
                    #Reset edited data every time plot_noise_windows is run
                    #v_data['stream'] = hv_data['input_stream'].copy()                    
                    #Set initial input
                    #input = hv_data#['input_stream']

                    if self.do_stalta.get():
                        hv_data = sprit_hvsr.remove_noise(hvsr_data=hv_data, remove_method='stalta', sta=self.sta.get(), lta=self.lta.get(), stalta_thresh=[self.stalta_thresh_low.get(), self.stalta_thresh_hi.get()])

                    if self.do_pctThresh.get():
                        hv_data = sprit_hvsr.remove_noise(hvsr_data=hv_data, remove_method='saturation',  sat_percent=self.pct.get())

                    if self.do_noiseWin.get():
                        hv_data = sprit_hvsr.remove_noise(hvsr_data=hv_data, remove_method='noise', noise_percent=self.noise_amp_pct.get(), lta=self.lta_noise.get(), min_win_size=self.win_size_thresh.get())
                
                    if self.do_warmup.get():
                        hv_data = sprit_hvsr.remove_noise(hvsr_data=hv_data, remove_method='warmup', warmup_time=self.warmup_time.get(), cooldown_time=self.cooldown_time.get())

                    if i==0:
                        self.fig_noise, self.ax_noise, self.noise_windows_line_artists, self.noise_windows_window_artists = sprit_hvsr._get_removed_windows(input=hv_data, fig=self.fig_noise, ax=self.ax_noise, existing_xWindows=self.xWindows, time_type='matplotlib')
                        self.fig_noise.canvas.draw()

                if batch_data is None:
                    hvsr_data = hvsr_data['SITENAME']

                return hvsr_data
            
            self.fig_noise.canvas.draw()
            return

        plot_noise_windows({'placeholder':None}, initial_setup=True)
        self.canvasFrame_noise.pack(fill='both')#.grid(row=0, column=0, sticky="nsew")

        #noise_mosaic = [['spec'],['spec'],['spec'],
        #        ['spec'],['spec'],['spec'],
        #        ['signalz'],['signalz'], ['signaln'], ['signale']]
        #self.fig_noise, self.ax_noise = plt.subplot_mosaic(noise_mosaic, sharex=True)  
        #self.canvasFrame_noise = ttk.LabelFrame(self.noise_tab, text='Noise Viewer')
        #self.canvasFrame_noise.pack(fill='both')#.grid(row=0, column=0, sticky="nsew")

        #self.noise_canvas = FigureCanvasTkAgg(self.fig_noise, master=self.canvasFrame_noise)
        #self.noise_canvas.draw()
        #self.noise_canvasWidget = self.noise_canvas.get_tk_widget()#.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        #self.noise_canvasWidget.pack(fill='both')#.grid(row=0, column=0, sticky='nsew')

        #Run button frame
        runFrame_noise = ttk.Frame(self.noise_tab)
        runFrame_noise.columnconfigure(0, weight=1)

        #Run area
        #Progress Bar
        self.noiseProgBar = ttk.Progressbar(runFrame_noise, orient='horizontal')
        self.noiseProgBar.grid(row=0, column=0, sticky='ew')#.pack(fill='both',expand=True, side='left', anchor='sw')

        #Update Noise Windows button
        self.style.configure(style='Noise.TButton', background='#86a5ba')
        self.noise_button = ttk.Button(runFrame_noise, text="Update Noise Windows", command=plot_noise_windows, width=30, style='Noise.TButton')
        
        self.noise_windows_line_artists = []
        self.noise_windows_window_artists = []

        self.style.configure('Run.TButton', background='#8b9685', width=10, height=3)
        self.run_button = ttk.Button(runFrame_noise, text="Run", style='Run.TButton', command=process_data)        
        self.noise_button.grid(row=0, column=1, sticky='nsew', padx=2.5)#.pack(side='right', anchor='se')
        self.run_button.grid(row=0, column=2, sticky='nsew', padx=2.5)#.pack(side='right', anchor='se', padx=(10,0))

        runFrame_noise.pack(fill='both',side='bottom', anchor='e')    


        def update_remove_noise_call():
            if 'prevAutoState' not in dir(self):
                self.prevAutoState=self.do_auto.get()

            if self.prevAutoState and not self.do_auto.get():
                self.do_stalta.set(False)
                self.do_pctThresh.set(False)
                self.do_noiseWin.set(False)
                self.do_warmup.set(False)
            #Get method
            remMethDict = {'auto':self.do_auto.get(),
                           'stalta':self.do_stalta.get(),
                           'sat_per':self.do_pctThresh.get(),
                           'noise_per':self.do_noiseWin.get(),
                           'warmcool':self.do_warmup.get(),
                           }

            remMethList = []
            for k, v in remMethDict.items():
                if v:
                    if k=='auto':
                        remMethList = ['auto']
                        break
                    remMethList.append(k)

            if len(remMethList)==1:
                remMethList = remMethList[0]
            
            if remMethList=='auto':
                remMethList = 'auto'
                self.do_auto.set(True)
                set_auto()

            if len(remMethList)==0:
                remMethList=None

            self.remove_noise_call.configure(text="remove_noise(hvsr_data, remove_method={}, sat_percent={}, noise_percent={}, sta={}, lta={}, stalta_thresh=[{},{}], warmup_time={}, cooldown_time={}, min_win_size={}, remove_raw_noise={})".format(
                                                                remMethList, self.pct.get(), self.noise_amp_pct.get(), self.sta.get(), self.lta.get(), self.stalta_thresh_low.get(), self.stalta_thresh_hi.get(), 
                                                                self.warmup_time.get(), self.cooldown_time.get(), self.win_size_thresh.get(),self.use_raw_data.get() ))

            self.prevAutoState = self.do_auto.get()


        #remove_noise Frame
        removeNoiseFrame = ttk.LabelFrame(self.noise_tab, text='remove_noise() call')

        self.remove_noise_call = ttk.Label(master=removeNoiseFrame, text="remove_noise(hvsr_data, remove_method='auto',sat_percent=0.995, noise_percent=0.80, sta=2, lta=30, stalta_thresh=[0.5,5], warmup_time=0, cooldown_time=0, min_win_size=1, remove_raw_noise=False)")
        self.remove_noise_call.grid(row=0, column=0, padx=5, pady=(0,5))
        removeNoiseFrame.pack(fill='both', side='bottom')#.grid(row=0, column=1, sticky='nsew')

        noiseFrame = ttk.LabelFrame(self.noise_tab, text='Noise Removal')
        noiseFrame.pack(fill='both')#.grid(row=1, columnspan=2, sticky='nsew')

        #Options for doing stalta antitrigger for noise removal
        stltaremoveFrame = ttk.LabelFrame(noiseFrame, text='STA/LTA Antitrigger')
        stltaremoveFrame.grid(row=0, column=0, columnspan=1, sticky='nsew')
        
        self.do_stalta = tk.BooleanVar()
        staltaBool = ttk.Checkbutton(master=stltaremoveFrame, text="", variable=self.do_stalta, command=update_remove_noise_call) # create the Checkbutton widget
        staltaBool.grid(row=0, column=0, sticky='ew')
        
        ttk.Label(master=stltaremoveFrame, text="STA [s]").grid(row=0, column=1)
        self.sta = tk.DoubleVar()
        self.sta.set(5)
        staEntry = ttk.Entry(master=stltaremoveFrame, textvariable=self.sta, width=5, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        staEntry.grid(row=0, column=2, sticky='ew', padx=(5,10))

        ttk.Label(master=stltaremoveFrame, text="LTA [s]").grid(row=0, column=3)
        self.lta = tk.DoubleVar()
        self.lta.set(30)
        ltaEntry = ttk.Entry(master=stltaremoveFrame, textvariable=self.lta, width=5, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        ltaEntry.grid(row=0, column=4, sticky='ew', padx=(5,10))

        ttk.Label(master=stltaremoveFrame, text="STA/LTA Thresholds (Low, High)").grid(row=0, column=5)
        self.stalta_thresh_low = tk.DoubleVar()
        self.stalta_thresh_low.set(0.5)
        staltaLowEntry = ttk.Entry(master=stltaremoveFrame, textvariable=self.stalta_thresh_low, width=5, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        staltaLowEntry.grid(row=0, column=6, sticky='ew', padx=(5,0))
        
        self.stalta_thresh_hi = tk.DoubleVar()
        self.stalta_thresh_hi.set(5)
        staltaHiEntry = ttk.Entry(master=stltaremoveFrame, textvariable=self.stalta_thresh_hi, width=5, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        staltaHiEntry.grid(row=0, column=7, sticky='ew')
        
        #Options for Percentage threshold removal
        pctThresFrame = ttk.LabelFrame(noiseFrame, text='Percentage Threshold')
        pctThresFrame.grid(row=1, column=0, sticky='nsew')

        self.do_pctThresh= tk.BooleanVar()
        pctBool = ttk.Checkbutton(master=pctThresFrame, text="", variable=self.do_pctThresh, command=update_remove_noise_call) # create the Checkbutton widget
        pctBool.grid(row=0, column=0, sticky='ew')
 
        ttk.Label(master=pctThresFrame, text="Max Saturation %").grid(row=0, column=1)
        self.pct = tk.DoubleVar()
        self.pct.set(0.995)
        pctEntry = ttk.Entry(master=pctThresFrame, textvariable=self.pct, width=10, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        pctEntry.grid(row=0, column=2, sticky='ew', padx=(5,10))

        ttk.Label(master=pctThresFrame, text="", width=27).grid(row=0, column=3, columnspan=2)

        #Options for noisy window
        noisyWindowFrame = ttk.LabelFrame(noiseFrame, text='Noisy Windows')
        noisyWindowFrame.grid(row=2, column=0, sticky='nsew')

        self.do_noiseWin = tk.BooleanVar()
        winNoiseBool = ttk.Checkbutton(master=noisyWindowFrame, text="", variable=self.do_noiseWin, command=update_remove_noise_call) # create the Checkbutton widget
        winNoiseBool.grid(row=0, column=0, sticky='ew')
 
        ttk.Label(master=noisyWindowFrame, text="Max Window %").grid(row=0, column=1)
        self.noise_amp_pct = tk.DoubleVar()
        self.noise_amp_pct.set(0.80)
        winamppctEntry = ttk.Entry(master=noisyWindowFrame, textvariable=self.noise_amp_pct, width=10, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        winamppctEntry.grid(row=0, column=2, sticky='ew', padx=(5,10))

        ttk.Label(master=noisyWindowFrame, text="Window Length [sec]").grid(row=0, column=3)
        self.lta_noise = tk.DoubleVar()
        self.lta_noise.set(30)
        winamppctEntry = ttk.Entry(master=noisyWindowFrame, textvariable=self.lta_noise, width=10, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        winamppctEntry.grid(row=0, column=4, sticky='ew', padx=(5,10))

        ttk.Label(master=noisyWindowFrame, text="Min. Window Size [sec]").grid(row=0, column=5)
        self.win_size_thresh = tk.DoubleVar()
        self.win_size_thresh.set(0)
        win_size_Entry = ttk.Entry(master=noisyWindowFrame, textvariable=self.win_size_thresh, width=10, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        win_size_Entry.grid(row=0, column=6, sticky='e', padx=(5,10))

        #Options for warmup
        warmupFrame = ttk.LabelFrame(noiseFrame, text='Warmup & Cooldown Time')
        warmupFrame.grid(row=0, column=1, sticky='nsew')

        self.do_warmup= tk.BooleanVar()
        warmupBool = ttk.Checkbutton(master=warmupFrame, text="", variable=self.do_warmup, command=update_remove_noise_call) # create the Checkbutton widget
        warmupBool.grid(row=0, column=0, sticky='ew')
 
        ttk.Label(master=warmupFrame, text="Warmup time [s]").grid(row=0, column=1)
        self.warmup_time = tk.DoubleVar()
        warmupEntry = ttk.Entry(master=warmupFrame, textvariable=self.warmup_time, width=10, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        warmupEntry.grid(row=0, column=2, sticky='ew', padx=(5,10))
        warmupEntry.delete(0, 'end')
        warmupEntry.insert(0, '0')
 
        ttk.Label(master=warmupFrame, text="Cooldown Time [s]").grid(row=0, column=3)
        self.cooldown_time = tk.DoubleVar()
        cooldownEntry = ttk.Entry(master=warmupFrame, textvariable=self.cooldown_time, width=10, validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        cooldownEntry.grid(row=0, column=5, sticky='ew', padx=(5,10))
        cooldownEntry.delete(0, 'end')
        cooldownEntry.insert(0, '0')

        #Options for doing stdev noise removal
        stdremoveFrame = ttk.LabelFrame(noiseFrame, text='Standard Deviation Antitrigger (not yet implemented)')
        stdremoveFrame.grid(row=1, column=1, columnspan=1, sticky='nsew')
        
        self.do_stdev = tk.BooleanVar()
        stdBool = ttk.Checkbutton(master=stdremoveFrame, text="", variable=self.do_stdev, state='disabled', command=update_remove_noise_call) # create the Checkbutton widget
        stdBool.grid(row=0, column=0, sticky='ew')
        
        ttk.Label(master=stdremoveFrame, text="Std Deviation Ratio (moving stdev/total stdev)").grid(row=0, column=1)
        self.stdRatio = tk.DoubleVar()
        stdRatEntry = ttk.Entry(master=stdremoveFrame, textvariable=self.stdRatio, width=5, state='disabled', validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        stdRatEntry.grid(row=0, column=2, sticky='ew', padx=(5,10))
        stdRatEntry.delete(0, 'end')
        stdRatEntry.insert(0, '1')
        
        ttk.Label(master=stdremoveFrame, text="Window Length [s]").grid(row=0, column=3)
        self.stdWinLen = tk.DoubleVar()
        stdWinLenEntry = ttk.Entry(master=stdremoveFrame, textvariable=self.stdWinLen, width=5, state='disabled',validate='focusout', validatecommand=update_remove_noise_call) # create the Entry widget
        stdWinLenEntry.grid(row=0, column=4, sticky='ew', padx=(5,10))
        stdWinLenEntry.delete(0, 'end')
        stdWinLenEntry.insert(0, '5')

        #Quick set the auto 
        #autoFrame = ttk.LabelFrame(noiseFrame, text='Auto Run')
        #autoFrame.grid(row=2, column=1, columnspan=1, sticky='nsew')

        
        def set_auto():
            if self.do_auto.get():
                self.do_stalta.set(True)
                self.do_stdev.set(True)
                self.do_warmup.set(True)
                self.do_noiseWin.set(True)
                self.do_pctThresh.set(True)
            else:
                self.do_stalta.set(False)
                self.do_stdev.set(False)
                self.do_warmup.set(False)
                self.do_noiseWin.set(False)
                self.do_pctThresh.set(False)                
                pass
            

        #Additional options
        addOptionsFrame = ttk.LabelFrame(noiseFrame, text='')
        addOptionsFrame.grid(row=2, column=1, columnspan=1, sticky='nsew')


        self.do_auto= tk.BooleanVar()
        autoBool = ttk.Checkbutton(master=addOptionsFrame, text="Set Auto Run", variable=self.do_auto, command=update_remove_noise_call) # create the Checkbutton widget
        autoBool.grid(row=0, column=0, sticky='nsew', padx=5)

        self.use_raw_data= tk.BooleanVar()
        rawDataRemoveBool = ttk.Checkbutton(master=addOptionsFrame, text="Remove from raw data", variable=self.use_raw_data, command=update_remove_noise_call) # create the Checkbutton widget
        rawDataRemoveBool.grid(row=0, column=1, sticky='nsew', padx=5)

        #Export noise windows
        ttk.Label(noiseFrame, text="Export Figure").grid(row=4, column=0, sticky='ew', padx=5)
        self.results_noise_dir = tk.StringVar()
        self.results_noise_dir_entry = ttk.Entry(noiseFrame, textvariable=self.results_noise_dir)
        self.results_noise_dir_entry.grid(row=4, column=0, columnspan=5, sticky='ew', padx=(100,5))
        
        
        def filepath_noise_fig():
            filepath = filedialog.asksaveasfilename(defaultextension='png', initialdir=pathlib.Path(self.data_path.get()).parent, initialfile=self.params['site']+'_noisewindows.png')
            if filepath:
                self.results_noise_dir_entry.delete(4, 'end')
                self.results_noise_dir_entry.insert(4, filepath)
        
        
        def save_noise_fig():
            self.fig_noise.savefig(self.results_noise_dir.get())
        
        self.browse_noise_fig = ttk.Button(noiseFrame, text="Browse",command=filepath_noise_fig)
        self.browse_noise_fig.grid(row=4, column=7, sticky='ew', padx=2.5)
        
        self.save_noise_fig = ttk.Button(noiseFrame, text="Save",command=save_noise_fig)
        self.save_noise_fig.grid(row=4, column=8, columnspan=2, sticky='ew', padx=2.5)

        self.noise_tab.pack(expand=1)
        self.tab_control.add(self.noise_tab, text="Noise")

        # SETTINGS TAB
        self.settings_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.settings_tab, text="Settings")
        
        # Create a new Notebook widget within the Settings tab
        settings_notebook = ttk.Notebook(self.settings_tab)

        # Create the tabs within the Settings tab
        #PPSD SETTINGS SUBTAB
        ppsd_settings_tab = ttk.Frame(settings_notebook)
        ppsdSettingsFrame = ttk.LabelFrame(ppsd_settings_tab, text='Input Settings')#.pack(fill='both')
        ppsdParamsFrame = ttk.LabelFrame(ppsd_settings_tab, text='PPSD Parameters')#.pack(fill='both')

        # ppsd_length=30.0
        
        def on_ppsd_length():
            try:
                float(self.ppsd_length.get())
                ppsdLenLabel.configure(text='ppsd_length={}'.format(self.ppsd_length.get()))
                update_ppsd_call(self.ppsd_call)
                return True
            except ValueError:
                return False
        ppsdLenLabel = ttk.Label(master=ppsdParamsFrame, text='ppsd_length=30.0 ')#.grid(row=0, column=0)
        ppsdLenLabel.grid(row=0, column=0, sticky='w', pady=(6,6), padx=5)
        
        ttk.Label(master=ppsdSettingsFrame, text='PPSD Length (in seconds) [float]').grid(row=0, column=0, sticky='w', padx=5)
        self.ppsd_length = tk.DoubleVar()
        self.ppsd_length.set(30)
        ppsdLenEntry = ttk.Entry(master=ppsdSettingsFrame, textvariable=self.ppsd_length, width=10, validate='focusout', validatecommand=on_ppsd_length)
        ppsdLenEntry.grid(row=0, column=1, sticky='w', padx=(5, 10))

        # overlap=0.5, 
        
        def on_overlap():
            try:
                overlap = float(self.overlap.get())
                if overlap > 1:
                    self.overlap.set(overlap/100)
                overlapLabel.configure(text='overlap={}'.format(self.overlap.get()))
                update_ppsd_call(self.ppsd_call)
                return True
            except ValueError:
                return False
        overlapLabel = ttk.Label(master=ppsdParamsFrame, text='overlap=0.5 ')#.grid(row=0, column=0)
        overlapLabel.grid(row=1, column=0, sticky='ew', pady=(6,6), padx=5)
        
        ttk.Label(master=ppsdSettingsFrame, text='Overlap % (0-1) [float]').grid(row=1, column=0, sticky='w', padx=5)
        self.overlap = tk.DoubleVar()
        self.overlap.set(0.5)
        overlapEntry = ttk.Entry(master=ppsdSettingsFrame, textvariable=self.overlap, width=10, validate='focusout', validatecommand=on_overlap)
        overlapEntry.grid(row=1, column=1, sticky='w', padx=(5, 10))

        # period_step_octaves=0.0625, 
        
        def on_per_step_oct():
            try:
                float(self.perStepOct.get())
                
                pStepOctLabel.configure(text='period_step_octaves={}'.format(self.perStepOct.get()))
                update_ppsd_call(self.ppsd_call)            
                return True
            except ValueError:
                return False
        pStepOctLabel = ttk.Label(master=ppsdParamsFrame, text='period_step_octaves=0.0625')#.grid(row=0, column=0)
        pStepOctLabel.grid(row=2, column=0, sticky='ew', pady=(6,6), padx=5)
        
        ttk.Label(master=ppsdSettingsFrame, text='Period Step Octave [float]').grid(row=2, column=0, sticky='w', padx=5)
        self.perStepOct = tk.DoubleVar()
        self.perStepOct.set(0.0625)
        pStepOctEntry = ttk.Entry(master=ppsdSettingsFrame, textvariable=self.perStepOct, width=10, validate='focusout', validatecommand=on_per_step_oct)
        pStepOctEntry.grid(row=2, column=1, sticky='w', padx=(5, 10))

        #skip_on_gaps
        
        def show_sog():
            if self.skip_on_gaps.get():
                sogLabel.configure(text ='skip_on_gaps=True')
            else:
                sogLabel.configure(text ='skip_on_gaps=False')
            update_ppsd_call(self.ppsd_call)
            
        self.skip_on_gaps = tk.BooleanVar()
        ttk.Label(master=ppsdSettingsFrame, text='Skip on Gaps [bool]: ', justify='left').grid(row=3, column=0, sticky='w', padx=5)
        sogCheckButton = ttk.Checkbutton(master=ppsdSettingsFrame, text='', variable=self.skip_on_gaps, command=show_sog) # create the Entry widget
        sogCheckButton.grid(row=3, column=1, sticky='ew', padx=(5,10))
        sogLabel = ttk.Label(master=ppsdParamsFrame, text='skip_on_gaps=False')
        sogLabel.grid(row=3, column=0, sticky='ew', pady=(6,6), padx=5)

        # db_bins=(-200, -50, 1.0), 
        
        def show_dbbins():
            try:
                float(minDB.get())
                float(maxDB.get())
                float(dB_step.get())
                dbbinsLabel.configure(text='db_bins=({}, {}, {})'.format(
                    minDB.get(), maxDB.get(), dB_step.get()))
                self.db_bins = (minDB.get(), maxDB.get(), dB_step.get())
                update_ppsd_call(self.ppsd_call)
                return True
            except ValueError:
                return False

        dbbinsLabel = ttk.Label(master=ppsdParamsFrame,
                                text='db_bins=(-200, -50, 1.0)')
        dbbinsLabel.grid(row=4, column=0, sticky='ew', pady=(6,6), padx=5)
        ttk.Label(master=ppsdSettingsFrame, text='dB Bins (Y Axis) [tuple]', justify='left').grid(row=4, column=0, sticky='w', padx=5)
        
        ttk.Label(master=ppsdSettingsFrame, text='Min. dB').grid(row=4, column=1, sticky='e', padx=5)
        minDB = tk.DoubleVar()
        minDB.set(-200)
        minDBEntry = ttk.Entry(master=ppsdSettingsFrame, textvariable=minDB,
                            validate="focusout", validatecommand=show_dbbins, width=10)
        minDBEntry.grid(row=4, column=2, sticky='w', padx=(5, 10))
        
        ttk.Label(master=ppsdSettingsFrame, text='Max. dB').grid(row=4, column=3, sticky='e', padx=5)
        maxDB = tk.DoubleVar()
        maxDB.set(-50)
        maxDBEntry = ttk.Entry(master=ppsdSettingsFrame, textvariable=maxDB,
                            validate="focusout", validatecommand=show_dbbins, width=10)
        maxDBEntry.grid(row=4, column=4, sticky='w', padx=(5, 10))

        ttk.Label(master=ppsdSettingsFrame, text='dB Step').grid(row=4, column=5, sticky='e', padx=5)
        dB_step = tk.DoubleVar()
        dB_step.set(1.0)
        stepEntry = ttk.Entry(master=ppsdSettingsFrame, textvariable=dB_step,
                            validate="focusout", validatecommand=(show_dbbins), width=10)
        stepEntry.grid(row=4, column=6, sticky='w', padx=(5, 10))
        self.db_bins = (minDB.get(), maxDB.get(), dB_step.get())

        # period_limits=None,
        
        def show_per_lims():
            try:
                if minPerLim.get() == 'None':
                    pass
                else:
                    float(minPerLim.get())
                    
                if maxPerLim.get() == 'None':
                    pass
                else:
                    float(maxPerLim.get())
                    
                if minPerLim.get() == 'None' or maxPerLim.get() == 'None':
                    perLimsLabel.configure(text='period_limits=None')
                else:
                    perLimsLabel.configure(text='period_limits=[{}, {}]'.format(minPerLim.get(), maxPerLim.get()))
                    self.period_limits = [float(minPerLim.get()), float(maxPerLim.get())]
                update_ppsd_call(self.ppsd_call)
                return True
            except ValueError:
                return False

        perLimsLabel = ttk.Label(master=ppsdParamsFrame,
                                text='period_limits=None')
        perLimsLabel.grid(row=5, column=0, sticky='ew', pady=(6,6), padx=5)
        ttk.Label(master=ppsdSettingsFrame, text='Period Limits [list of floats or None]', justify='left').grid(row=5, column=0, sticky='w', padx=5)
        
        ttk.Label(master=ppsdSettingsFrame, text='Min. Period Limit').grid(row=5, column=1, sticky='e', padx=5)
        minPerLim = tk.StringVar()
        minPerLim.set(None)
        minPerLimEntry = ttk.Entry(master=ppsdSettingsFrame, textvariable=minPerLim,
                            validate="focusout", validatecommand=(show_per_lims), width=10)
        minPerLimEntry.grid(row=5, column=2, sticky='w', padx=(5, 10))
        
        ttk.Label(master=ppsdSettingsFrame, text='Max. Period Limit').grid(row=5, column=3, sticky='e', padx=5)
        maxPerLim = tk.StringVar()
        maxPerLim.set(None)
        maxPerLimEntry = ttk.Entry(master=ppsdSettingsFrame, textvariable=maxPerLim,
                            validate="focusout", validatecommand=(show_per_lims), width=10)
        maxPerLimEntry.grid(row=5, column=4, sticky='w', padx=(5, 10))

        if minPerLim.get() == 'None' or maxPerLim.get() == 'None':
            self.period_limits = None
        else:
            self.period_limits = [float(minPerLim.get()), float(maxPerLim.get())]

        # period_smoothing_width_octaves=1.0,
        
        def on_per_smoothwidth_oct():
            try:
                float(self.perSmoothWidthOct.get())
                
                pSmoothWidthLabel.configure(text='period_smoothing_width_octaves={}'.format(self.perSmoothWidthOct.get()))
                update_ppsd_call(self.ppsd_call)
                return True
            except ValueError:
                return False
        pSmoothWidthLabel = ttk.Label(master=ppsdParamsFrame, text='period_smoothing_width_octaves=1.0')#.grid(row=0, column=0)
        pSmoothWidthLabel.grid(row=6, column=0, sticky='ew', pady=(6,6), padx=5)
        
        ttk.Label(master=ppsdSettingsFrame, text='Period Smoothing Width (octaves) [float]').grid(row=6, column=0, sticky='w', padx=5)
        self.perSmoothWidthOct = tk.DoubleVar()
        self.perSmoothWidthOct.set(1.0)
        pSmoothWidthEntry = ttk.Entry(master=ppsdSettingsFrame, textvariable=self.perSmoothWidthOct, width=10, validate='focusout', validatecommand=on_per_smoothwidth_oct)
        pSmoothWidthEntry.grid(row=6, column=1, sticky='w', padx=(5, 10))
        
        # special_handling=None, 
        
        def on_special_handling():
            try:
                str(self.special_handling.get())
                if self.special_handling.get() == 'None':
                    specialHandlingLabel.configure(text="special_handling={}".format(self.special_handling.get()))
                    special_handling = None
                else:
                    specialHandlingLabel.configure(text="special_handling='{}'".format(self.special_handling.get()))
                    special_handling = self.special_handling.get()
                update_ppsd_call(self.ppsd_call)
                return True
            except ValueError:
                return False

        specialHandlingLabel = ttk.Label(master=ppsdParamsFrame, text="special_handling=None")
        specialHandlingLabel.grid(row=7, column=0, sticky='ew', pady=(6,6), padx=5)

        ttk.Label(master=ppsdSettingsFrame, text='Special Handling [str]').grid(row=7, column=0, sticky='w', padx=5)

        self.special_handling = tk.StringVar()
        self.special_handling.set('None')
        ttk.Radiobutton(master=ppsdSettingsFrame, text='None', variable=self.special_handling, value='None', command=on_special_handling).grid(row=7, column=1, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=ppsdSettingsFrame, text='Ringlaser', variable=self.special_handling, value='ringlaser', command=on_special_handling).grid(row=7, column=2, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=ppsdSettingsFrame, text='Hydrophone', variable=self.special_handling, value='hydrophone', command=on_special_handling).grid(row=7, column=3, sticky='w', padx=(5, 10))

        if self.special_handling.get()=='None':
            special_handling = None
        else:
            special_handling = self.special_handling.get()

        separator = ttk.Separator(ppsdSettingsFrame, orient='horizontal')
        separator.grid(row=8, columnspan=8, sticky='ew', pady=10, padx=5)

        separator = ttk.Separator(ppsdParamsFrame, orient='horizontal')
        separator.grid(row=8, sticky='ew', pady=10, padx=5)

        #remove_outliers
        
        def show_rem_outliers():
            if self.remove_outliers.get():
                rem_outliers_Label.configure(text ='remove_outliers=True')
            else:
                rem_outliers_Label.configure(text ='remove_outliers=False')
            update_ppsd_call(self.ppsd_call)
            
        self.remove_outliers = tk.BooleanVar()
        self.remove_outliers.set(True)
        ttk.Label(master=ppsdSettingsFrame, text='Remove outlier curves [bool]: ', justify='left').grid(row=9, column=0, sticky='w', padx=5)
        rem_outliers_CheckButton = ttk.Checkbutton(master=ppsdSettingsFrame, text='', variable=self.remove_outliers, command=show_rem_outliers) # create the Entry widget
        rem_outliers_CheckButton.grid(row=9, column=1, sticky='ew', padx=(5,10))
        rem_outliers_Label = ttk.Label(master=ppsdParamsFrame, text='remove_outliers=True')
        rem_outliers_Label.grid(row=9, column=0, sticky='ew', pady=(6,6), padx=5)

        # outlier_std=1.5, 
        
        def on_outlier_std():
            try:
                float(self.outlier_std.get())
                outlier_std_Label.configure(text='outlier_std={}'.format(self.outlier_std.get()))
                update_ppsd_call(self.ppsd_call)            
                return True
            except ValueError:
                return False
        outlier_std_Label = ttk.Label(master=ppsdParamsFrame, text='outlier_std=1.5')#.grid(row=0, column=0)
        outlier_std_Label.grid(row=10, column=0, sticky='ew', pady=(6,6), padx=5)
        
        ttk.Label(master=ppsdSettingsFrame, text='St. Dev. for Outliers [float]').grid(row=10, column=0, sticky='w', padx=5)
        self.outlier_std = tk.DoubleVar()
        self.outlier_std.set(1.5)
        outlier_std_Entry = ttk.Entry(master=ppsdSettingsFrame, textvariable=self.outlier_std, width=10, validate='focusout', validatecommand=on_outlier_std)
        outlier_std_Entry.grid(row=10, column=1, sticky='w', padx=(5, 10))


        #PPSD Function Call
        ppsdCallFrame = ttk.LabelFrame(ppsd_settings_tab, text='sprit_hvsr.generate_psds() and obspy PPSD() call')#.pack(fill='both') 
       
        self.ppsd_call = ttk.Label(master=ppsdCallFrame, text='obspy...PPSD({}, {}, {}, {}, {}, {}, \n\t{}, {}, {}, {})'
                  .format('stats', 'metadata', ppsdLenLabel.cget('text'), overlapLabel.cget('text'), pStepOctLabel.cget('text'), sogLabel.cget('text'), 
                          dbbinsLabel.cget('text'), perLimsLabel.cget('text'), pSmoothWidthLabel.cget('text'), specialHandlingLabel.cget('text')))
        self.ppsd_call.pack(side='bottom', anchor='w', padx=(25,0), pady=(10,10))

        self.generate_ppsd_call = ttk.Label(master=ppsdCallFrame, text='generate_psds({}, remove_outliers={}, outlier_std={},...\n\t{}, {}, {}, {}, {}, \n\t{}, {}, {})'
                  .format('hvsr_data', self.remove_outliers.get(), self.outlier_std.get(), 
                          ppsdLenLabel.cget('text'), overlapLabel.cget('text'), pStepOctLabel.cget('text'), sogLabel.cget('text'), 
                          dbbinsLabel.cget('text'), perLimsLabel.cget('text'), pSmoothWidthLabel.cget('text'), specialHandlingLabel.cget('text')))
        self.generate_ppsd_call.pack(side='bottom', anchor='w', padx=(25,0), pady=(10,10))
        
        
        def update_ppsd_call(ppsd_call):
            ppsd_call.configure(text='obspy...PPSD({}, {}, {}, {}, {}, {}, \n\t{}, {}, {}, {})'.format('stats', 'metadata', ppsdLenLabel.cget('text'), 
                                                                                                    overlapLabel.cget('text'), pStepOctLabel.cget('text'), sogLabel.cget('text'), 
                          dbbinsLabel.cget('text'), perLimsLabel.cget('text'), pSmoothWidthLabel.cget('text'), specialHandlingLabel.cget('text')))

            self.generate_ppsd_call.configure(text='generate_psds({}, remove_outliers={}, outlier_std={},...\n\t{}, {}, {}, {}, {}, \n\t{}, {}, {})'
                            .format('hvsr_data', self.remove_outliers.get(), self.outlier_std.get(), 
                                    ppsdLenLabel.cget('text'), overlapLabel.cget('text'), pStepOctLabel.cget('text'), sogLabel.cget('text'), 
                                    dbbinsLabel.cget('text'), perLimsLabel.cget('text'), pSmoothWidthLabel.cget('text'), specialHandlingLabel.cget('text')))
                    

        #Stats from trace(s)
        obspyStatsFrame = ttk.LabelFrame(ppsd_settings_tab, text='Data Trace Stats')#.pack(fill='both')
        self.obspySreamLabel_settings = ttk.Label(obspyStatsFrame, text='Stats')
        self.obspySreamLabel_settings.pack(anchor='nw', padx=5)

        #Metadata (PAZ)
        obspyMetadataFrame = ttk.LabelFrame(ppsd_settings_tab, text='Metadata Poles and Zeros')#.pack(fill='both')

        self.metadataZ_settings = ttk.Label(obspyMetadataFrame, text='Z: ')
        self.metadataZ_settings.grid(row=1, column=0, padx=5)
        self.metadataZ_settings.configure(font=("TkDefaultFont", 10, 'underline', 'bold'))
        self.sensitivityLabelZ_settings = ttk.Label(obspyMetadataFrame, text='Sensitivity_Z')
        self.sensitivityLabelZ_settings.grid(row=1, column=1, padx=5)
        self.gainLabelZ_settings = ttk.Label(obspyMetadataFrame, text='Gain_Z')
        self.gainLabelZ_settings.grid(row=1, column=2, padx=5)
        self.polesLabelZ_settings = ttk.Label(obspyMetadataFrame, text='Poles_Z')
        self.polesLabelZ_settings.grid(row=1, column=3, padx=5)
        self.zerosLabelZ_settings = ttk.Label(obspyMetadataFrame, text='Zeros_Z')
        self.zerosLabelZ_settings.grid(row=1, column=4, padx=5)
 
        self.metadataN_settings = ttk.Label(obspyMetadataFrame, text='N: ')
        self.metadataN_settings.grid(row=2, column=0, padx=5)
        self.metadataN_settings.configure(font=("TkDefaultFont", 10, 'underline', 'bold'))
        self.sensitivityLabelN_settings = ttk.Label(obspyMetadataFrame, text='Sensitivity_N')
        self.sensitivityLabelN_settings.grid(row=2, column=1, padx=5)
        self.gainLabelN_settings = ttk.Label(obspyMetadataFrame, text='Gain_N')
        self.gainLabelN_settings.grid(row=2, column=2, padx=5)
        self.polesLabelN_settings = ttk.Label(obspyMetadataFrame, text='Poles_N')
        self.polesLabelN_settings.grid(row=2, column=3, padx=5)
        self.zerosLabelN_settings = ttk.Label(obspyMetadataFrame, text='Zeros_N')
        self.zerosLabelN_settings.grid(row=2, column=4, padx=5)
 
        self.metadataE_settings = ttk.Label(obspyMetadataFrame, text='E: ')
        self.metadataE_settings.grid(row=3, column=0, padx=5)
        self.metadataE_settings.configure(font=("TkDefaultFont", 10, 'underline', 'bold'))
        self.sensitivityLabelE_settings = ttk.Label(obspyMetadataFrame, text='Sensitivity_E')
        self.sensitivityLabelE_settings.grid(row=3, column=1)
        self.gainLabelE_settings = ttk.Label(obspyMetadataFrame, text='Gain_E')
        self.gainLabelE_settings.grid(row=3, column=2, padx=5)
        self.polesLabelE_settings = ttk.Label(obspyMetadataFrame, text='Poles_E')
        self.polesLabelE_settings.grid(row=3, column=3, padx=5)
        self.zerosLabelE_settings = ttk.Label(obspyMetadataFrame, text='Zeros_E')
        self.zerosLabelE_settings.grid(row=3, column=4, padx=5)

        self.metadata_sensitivity = ttk.Label(obspyMetadataFrame, text='Sensitivity')
        self.metadata_sensitivity.grid(row=0, column=1, padx=5)
        self.metadata_sensitivity.configure(font=("TkDefaultFont", 10, 'underline', 'bold'))

        self.metadata_gain = ttk.Label(obspyMetadataFrame, text='Gain')
        self.metadata_gain.grid(row=0, column=2, padx=5)
        self.metadata_gain.configure(font=("TkDefaultFont", 10, 'underline', 'bold'))

        self.metadata_poles = ttk.Label(obspyMetadataFrame, text='Poles')
        self.metadata_poles.grid(row=0, column=3, padx=5)
        self.metadata_poles.configure(font=("TkDefaultFont", 10, 'underline', 'bold'))

        self.metadata_zeros = ttk.Label(obspyMetadataFrame, text='Zeros')
        self.metadata_zeros.grid(row=0, column=4, padx=5)
        self.metadata_zeros.configure(font=("TkDefaultFont", 10, 'underline', 'bold'))

        #Run button frame
        runFrame_set_ppsd = ttk.Frame(ppsd_settings_tab)
        self.run_button = ttk.Button(runFrame_set_ppsd, text="Run", style='Run.TButton', command=process_data)
        self.run_button.grid(row=0, column=11, sticky='ew', padx=2.5)

        self.settingsProgBar_ppsd = ttk.Progressbar(runFrame_set_ppsd, orient='horizontal')
        self.settingsProgBar_ppsd.grid(row=0, column=0, columnspan=10, sticky='ew')
        runFrame_set_ppsd.columnconfigure(0, weight=1)

        runFrame_set_ppsd.pack(fill='both', side='bottom', anchor='e')            
        obspyMetadataFrame.pack(fill='both', side='bottom',expand=True)#.grid(row=7, column=0, columnspan=6, sticky='nsew')#.pack(side='bottom', fill='both', anchor='n', expand=True)
        obspyStatsFrame.pack(fill='both', side='bottom',expand=True)#.grid(row=6, column=0, columnspan=6, sticky='nsew')#.pack(side='bottom', fill='both', anchor='n', expand=True)
        ppsdCallFrame.pack(fill='both', side='bottom',expand=True)#row=5, column=0, columnspan=6, sticky='nsew')#.pack(side='bottom', fill='both', anchor='n', expand=True)
        ppsdParamsFrame.pack(fill='both', side='right')#.grid(row=0, column=5, rowspan=4, sticky='nsew')#.pack(side='right',fill='both', anchor='n', expand=True)
        ppsdSettingsFrame.pack(fill='both', expand=True, side='top', anchor='w')#.grid(row=0, column=0, columnspan=4, rowspan=4, sticky='nsew')#.pack(side='left', fill='both', anchor='n', expand=True)
    
        ppsd_settings_tab.pack(fill='both', expand=True)
        settings_notebook.add(ppsd_settings_tab, text="PPSD")

        #HVSR SETTINGS SUBTAB
        hvsr_settings_tab = ttk.Frame(settings_notebook)
        
        hvsrSettingsFrame = ttk.LabelFrame(hvsr_settings_tab, text='H/V Processing Settings')#.pack(fill='both')
        
        hvsrParamsFrame = ttk.LabelFrame(hvsr_settings_tab, text='Process HVSR Parameters')#.pack(fill='both')
        
        #Method selection, method=4
        ttk.Label(hvsrSettingsFrame, text="Horizontal Combine Method [int]").grid(row=0, column=0, padx=(5,0), sticky='w')
        method_options = ['', #Empty to make intuitive and match sprit_hvsr.py
                          "1.Diffuse Field Assumption (not currently implemented)", 
                          "2. Arithmetic Mean H ≡ (N + E)/2",
                          "3. Geometric Mean: H ≡ √(N · E) (recommended by SESEAME Project (2004))",
                          "4. Vector Summation: H ≡ √(N^2 + E^2)",
                          "5. Quadratic Mean: H ≡ √(N^2 + E^2)/2",
                          "6. Maximum Horizontal Value: H ≡ max(N, E)"
                          ]

        
        def on_method_select(meth, meth_opts=method_options):
            self.method_ind = meth_opts.index(meth)

            try:
                int(self.method_ind)
                hCombMethodLabel.configure(text="method={}".format(self.method_ind))
                update_procHVSR_call(self.procHVSR_call)
                return True
            except ValueError:
                return False

        defaultMeth=3
        hCombMethodLabel = ttk.Label(master=hvsrParamsFrame, text="method={}".format(defaultMeth), width=30)
        hCombMethodLabel.grid(row=0, column=0, sticky='ew', pady=(6,6), padx=5)

        self.method_sel = tk.StringVar(value=method_options[defaultMeth])
        self.method_ind = method_options.index(self.method_sel.get())       
        self.method_dropdown = ttk.OptionMenu(hvsrSettingsFrame, self.method_sel, method_options[defaultMeth], *method_options, command=on_method_select)
        self.method_dropdown.config(width=50)
        self.method_dropdown.grid(row=0, column=1, columnspan=8, sticky='ew')
        
        #smooth=True, 
        
        def curve_smooth():
            try:
                int(self.hvsmooth.get())
                bool(self.hvsmoothbool.get())
                if not self.hvsmoothbool.get():
                    hvSmoothLabel.configure(text='smooth={}'.format(self.hvsmoothbool.get()))
                    self.hvsmooth_param = False
                else:
                    hvSmoothLabel.configure(text='smooth={}'.format(self.hvsmooth.get()))
                    self.hvsmooth_param = self.hvsmooth.get()              
                update_procHVSR_call(self.procHVSR_call)
                return True
            except ValueError:
                return False
            
        hvSmoothLabel = ttk.Label(master=hvsrParamsFrame, text="smooth=True", width=30)
        hvSmoothLabel.grid(row=1, column=0, sticky='ew', pady=(6,6), padx=5)

        ttk.Label(master=hvsrSettingsFrame, text='Smooth H/V Curve [bool]').grid(row=1, column=0, padx=(5,0), sticky='w')

        self.hvsmoothbool = tk.BooleanVar()
        self.hvsmoothbool.set(True)
        self.hvsmooth_param=True
        smoothCurveBool = ttk.Checkbutton(master=hvsrSettingsFrame, text="", compound='left', variable=self.hvsmoothbool, command=curve_smooth) # create the Checkbutton widget
        smoothCurveBool.grid(row=1, column=1, sticky='w')

        self.hvsmooth = tk.IntVar()
        self.hvsmooth.set(51)
        smoothCurveSamples = ttk.Entry(master=hvsrSettingsFrame, textvariable=self.hvsmooth, width=10, validate='focusout', validatecommand=curve_smooth)
        smoothCurveSamples.grid(row=1, column=2, sticky='w', padx=(5, 10))
        ttk.Label(master=hvsrSettingsFrame, text='[int] # pts in smoothing window (default=51)').grid(row=1, column=3, padx=(0,0))
        
        #freq_smooth='konno ohmachi', 
        freqSmoothLabel = ttk.Label(master=hvsrParamsFrame, text="freq_smooth='konno ohmachi'", width=30)
        freqSmoothLabel.grid(row=2, column=0, sticky='w', pady=(16,16), padx=5)

        
        def on_freq_smooth():
            try:
                str(self.freq_smooth.get())
                freqSmoothLabel.configure(text="freq_smooth={}".format(self.freq_smooth.get()))
                update_procHVSR_call(self.procHVSR_call)
                return True
            except ValueError:
                return False

        self.freq_smooth = tk.StringVar()
        self.freq_smooth.set('konno ohmachi')
        ttk.Label(master=hvsrSettingsFrame, text='Frequency Smoothing [str]').grid(row=2, column=0, padx=(5,0), sticky='w')
        fsmoothOptFrame = ttk.LabelFrame(master=hvsrSettingsFrame, text='Frequency Smoothing Operations')
        fsmoothOptFrame.grid(row=2, column=1, columnspan=7, padx=5, sticky='nsew')
        ttk.Radiobutton(master=fsmoothOptFrame, text='Konno-Ohmachi', variable=self.freq_smooth, value='konno ohmachi', command=on_freq_smooth).grid(row=0, column=0, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=fsmoothOptFrame, text='Constant', variable=self.freq_smooth, value='constant', command=on_freq_smooth).grid(row=0, column=1, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=fsmoothOptFrame, text='Proportional', variable=self.freq_smooth, value='proportional', command=on_freq_smooth).grid(row=0, column=2, sticky='w', padx=(5, 10))
        ttk.Radiobutton(master=fsmoothOptFrame, text='None', variable=self.freq_smooth, value='None', command=on_freq_smooth).grid(row=0, column=3, sticky='w', padx=(5, 10))

        #f_smooth_width=40, 
        fSmoothWidthlabel = ttk.Label(master=hvsrParamsFrame, text="f_smooth_width=40", width=30)
        fSmoothWidthlabel.grid(row=3, column=0, sticky='ew', pady=(6,6), padx=5)

        
        def on_smooth_width():
            try:
                int(self.fSmoothWidth.get())
                fSmoothWidthlabel.configure(text='f_smooth_width={}'.format(self.fSmoothWidth.get()))                
                update_procHVSR_call(self.procHVSR_call)
                return True
            except ValueError:
                return False
            
        ttk.Label(master=hvsrSettingsFrame, text='Bandwidth of freq. smoothing [int]').grid(row=3, column=0, padx=(5,0), sticky='w')
        self.fSmoothWidth = tk.IntVar()
        self.fSmoothWidth.set(40)
        fSmoothWidthEntry = ttk.Entry(master=hvsrSettingsFrame, justify='left', textvariable=self.fSmoothWidth, validate='focusout', validatecommand=on_smooth_width, width=10)
        fSmoothWidthEntry.grid(row=3, column=1, sticky='w', padx=(5, 10))
        
        #resample=True, 
        resampleLabel = ttk.Label(master=hvsrParamsFrame, text="resample=True", width=30)
        resampleLabel.grid(row=4, column=0, sticky='ew', pady=(6,6), padx=5)
        
        def on_curve_resample():
            try:
                if not self.resamplebool.get():
                    resampleLabel.configure(text='resample={}'.format(self.resamplebool.get()))
                    self.hvresample_int=self.hvresample.get()
                else:
                    resampleLabel.configure(text='resample={}'.format(self.hvresample.get()))
                    self.hvresample_int=self.hvresample.get()    
                update_procHVSR_call(self.procHVSR_call)
                return True
            except ValueError:
                return False
            
        self.resamplebool = tk.BooleanVar()
        self.resamplebool.set(True)
        ttk.Label(master=hvsrSettingsFrame, text='Resample H/V Curve [bool]').grid(row=4, column=0, padx=(5,0), sticky='w')
        resampleCurveBool = ttk.Checkbutton(master=hvsrSettingsFrame, text="", compound='left', variable=self.resamplebool, command=on_curve_resample) # create the Checkbutton widget
        resampleCurveBool.grid(row=4, column=1, sticky='w')

        self.hvresample = tk.IntVar()
        self.hvresample.set(1000)
        self.hvresample_int = self.hvresample.get()
        resampleCurveSamples = ttk.Entry(master=hvsrSettingsFrame, textvariable=self.hvresample, width=10, validate='focusout', validatecommand=on_curve_resample)
        resampleCurveSamples.grid(row=4, column=2, sticky='w', padx=(5, 10))
        ttk.Label(master=hvsrSettingsFrame, text='[int] # pts in resampled curve (default=1000)').grid(row=4, column=3, padx=(0,0), sticky='w')

        #outlier_curve_std=1.75
        outlierValLabel = ttk.Label(master=hvsrParamsFrame, text="outlier_curve_std=1.75", width=30)
        outlierValLabel.grid(row=5, column=0, sticky='ew', pady=(6,6), padx=5)        

        ttk.Label(master=hvsrSettingsFrame, text='Outlier St. Dev. [float]').grid(row=6, column=0, columnspan=2, padx=(5,0), sticky='w')
        self.outlierRemStDev = tk.DoubleVar()
        self.outlierRemStDev.set(1.75)
        outlierRemStDev = ttk.Entry(master=hvsrSettingsFrame, textvariable=self.outlierRemStDev, width=10, validate='focusout', validatecommand=on_outlier_std)
        outlierRemStDev.grid(row=6, column=1, sticky='w', padx=(5, 10))

        separator = ttk.Separator(hvsrSettingsFrame, orient='horizontal')
        separator.grid(row=7, columnspan=7, sticky='ew', pady=10)

        #hvsr_band=[0.4, 40]
        hvsrBandLabel = ttk.Label(master=hvsrParamsFrame, text="hvsr_band=[0.4,40]", width=30)
        hvsrBandLabel.grid(row=7, column=0, sticky='w', pady=(20,6), padx=5)

        ttk.Label(hvsrSettingsFrame,text="HVSR Band [Hz]").grid(row=8,column=0, sticky='w', padx=(5,0))

        hvsr_band_min_settingsEntry = ttk.Entry(hvsrSettingsFrame, width=10, textvariable=self.hvsrBand_min, validate='focusout', validatecommand=on_hvsrband_update)
        hvsr_band_min_settingsEntry.grid(row=8,column=1, sticky='ew')

        hvsr_band_max_settingsEntry = ttk.Entry(hvsrSettingsFrame, width=10, textvariable=self.hvsrBand_max, validate='focusout', validatecommand=on_hvsrband_update)
        hvsr_band_max_settingsEntry.grid(row=8,column=2, sticky='ew')
   
        #peak_freq_range=[0.4, 40]
        peakFreqRangeLabel = ttk.Label(master=hvsrParamsFrame, text="peak_freq_range=[0.4,40]", width=30)
        peakFreqRangeLabel.grid(row=8, column=0, sticky='w', pady=(20,6), padx=5)

        ttk.Label(hvsrSettingsFrame,text="Peak Frequency Range [Hz]").grid(row=9,column=0, sticky='w', padx=(5,0))

        hvsr_band_min_settingsEntry = ttk.Entry(hvsrSettingsFrame, width=10, textvariable=self.peakFreqRange_min, validate='focusout', validatecommand=on_peakFreqRange_update)
        hvsr_band_min_settingsEntry.grid(row=9,column=1, sticky='ew')

        hvsr_band_max_settingsEntry = ttk.Entry(hvsrSettingsFrame, width=10, textvariable=self.peakFreqRange_max, validate='focusout', validatecommand=on_peakFreqRange_update)
        hvsr_band_max_settingsEntry.grid(row=9,column=2, sticky='ew')
       
        #Process HVSR Function Call
        hvsrCallFrame = ttk.LabelFrame(hvsr_settings_tab, text='sprit_hvsr.process_hvsr() Call')#.pack(fill='both')
        
        self.procHVSR_call = ttk.Label(master=hvsrCallFrame, text='process_hvsr({}, {}, {}, {}, {}, \n\t{}, {}, {})'
                  .format('hvsr_data', hCombMethodLabel.cget('text'), hvSmoothLabel.cget('text'), freqSmoothLabel.cget('text'), fSmoothWidthlabel.cget('text'), resampleLabel.cget('text'), 
                           outlierValLabel.cget('text'), hvsrBandLabel.cget('text')))
        self.procHVSR_call.pack(anchor='w', padx=(25,0), pady=(10,10))

        
        def update_procHVSR_call(procHVSR_call):
            procHVSR_call.configure(text='process_hvsr({}, {}, {}, {}, {}, \n\t{}, {}, {})'
                  .format('hvsr_data', hCombMethodLabel.cget('text'), hvSmoothLabel.cget('text'), freqSmoothLabel.cget('text'), fSmoothWidthlabel.cget('text'), resampleLabel.cget('text'), 
                          outlierValLabel.cget('text'), hvsrBandLabel.cget('text')))
        
        #Check Peaks Function Call
        checkPeaksCallFrame = ttk.LabelFrame(hvsr_settings_tab, text='sprit_hvsr.check_peaks() Call')#.pack(fill='both')

        self.checkPeaks_Call = ttk.Label(master=checkPeaksCallFrame, text='check_peaks({}, {}, {})'
                  .format('hvsr_data', hvsrBandLabel.cget('text'), peakFreqRangeLabel.cget('text')))
        self.checkPeaks_Call.pack(anchor='w', padx=(25,0), pady=(10,10))

        #check_peaks(hvsr_dict, hvsr_band=[0.4, 40], peak_water_level=1.8)
        
        def update_check_peaks_call(checkPeaks_Call):
            checkPeaks_Call.configure(text='check_peaks({}, {}, {})'
                  .format('hvsr_data', hvsrBandLabel.cget('text'), peakFreqRangeLabel.cget('text')))


        #Run button frame
        runFrame_set_hvsr = ttk.Frame(hvsr_settings_tab)
        runFrame_set_hvsr.columnconfigure(0, weight=1)

        self.settingsProgBar_hvsr = ttk.Progressbar(runFrame_set_hvsr, orient='horizontal')
        self.settingsProgBar_hvsr.grid(row=0, column=0, sticky='nsew')#.pack(fill='both',expand=True, side='left', anchor='sw')

        self.run_button = ttk.Button(runFrame_set_hvsr, text="Run", style='Run.TButton', command=process_data)
        self.run_button.grid(row=0, column=1, sticky='nsew', padx=2.5)#.pack(side='bottom', anchor='e')

        #Pack tab
        runFrame_set_hvsr.pack(fill='both', side='bottom', anchor='e')    
        checkPeaksCallFrame.pack(fill='both', expand=True, side='bottom')#.grid(row=10, column=0, columnspan=6, sticky='nsew')#.pack(side='bottom', fill='both', anchor='n', expand=True)
        hvsrCallFrame.pack(fill='both', expand=True, side='bottom')#.grid(row=9, column=0, columnspan=6, sticky='nsew')#.pack(side='bottom', fill='both', anchor='n', expand=True)
        hvsrParamsFrame.pack(fill='both', side='right')#.grid(row=0, column=6, rowspan=4, sticky='nsew')#.pack(side='right',fill='both', anchor='n', expand=True)
        hvsrSettingsFrame.pack(fill='both', expand=True, side='top')#.grid(row=0, column=0, columnspan=6, rowspan=4, sticky='nsew')#.pack(fill='both', expand=True)
        
        hvsr_settings_tab.pack(fill='both', expand=True)           
        settings_notebook.add(hvsr_settings_tab, text="HVSR Settings")

        #PLOT SETTINGS TAB
        plot_settings_tab = ttk.Frame(settings_notebook)

        # Create the Plot Options LabelFrame
        plot_options_frame = ttk.LabelFrame(plot_settings_tab, text="Plot Options")

        
        def update_hvplot_call():
            kindstr = get_kindstr()
            hvplot_label.configure(text="plot_hvsr({}, plot_type={}, xtype='{}', show_legend={}, {}, {})".format('hvsr_data', kindstr, self.x_type.get(), self.show_legend.get(), '[...]', 'kwargs'))

        # Create the Checkbuttons for the plot options
        ttk.Label(plot_options_frame, text='HVSR Plot', justify='center').grid(row=0, column=1, sticky='ew', padx=(5, 5))
        ttk.Label(plot_options_frame, text='Components H/V Plot', justify='center').grid(row=0, column=2, sticky='ew', padx=(5, 5))
        ttk.Label(plot_options_frame, text='Spectrogram Plot', justify='center').grid(row=0, column=3, sticky='ew', padx=(5, 5))

        self.hvsr_chart_bool = tk.BooleanVar()
        self.hvsr_chart_bool.set(True)
        ttk.Checkbutton(plot_options_frame, text='', variable=self.hvsr_chart_bool, command=update_hvplot_call).grid(row=1, column=1, sticky='nsew', padx=15, pady=(5, 20))
        self.ind_comp_chart_bool = tk.BooleanVar()
        self.ind_comp_chart_bool.set(True)
        ttk.Checkbutton(plot_options_frame, text='', variable=self.ind_comp_chart_bool, command=update_hvplot_call).grid(row=1, column=2, sticky='nsew', padx=50, pady=(5, 20))
        self.spec_chart_bool = tk.BooleanVar()
        self.spec_chart_bool.set(True)
        ttk.Checkbutton(plot_options_frame, text='', variable=self.spec_chart_bool, command=update_hvplot_call).grid(row=1, column=3, sticky='nsew', padx=25, pady=(5, 20))
        
        ttk.Separator(plot_options_frame, orient='horizontal').grid(row=2, columnspan=5, sticky='ew', pady=5)
        
        #Separate component chart: c+
        ttk.Label(plot_options_frame, text='Show Components on same chart as H/V Curve:').grid(row=3, column=0, sticky='w', padx=5)
        
        
        def disable_comp_buttons():
            if self.show_comp_with_hv.get():
                self.annotate_best_peak_comp.set(False)
                self.show_best_peak_comp.set(False)
                bestPeakCompButton.config(state="disabled") 
                bestPeakCompAnnButton.config(state='disabled')
            else:
                bestPeakCompButton.config(state="normal") 
                bestPeakCompAnnButton.config(state='normal')
            update_hvplot_call()

        self.show_comp_with_hv = tk.BooleanVar()
        self.show_comp_with_hv.set(False)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.show_comp_with_hv, 
                        command=disable_comp_buttons).grid(row=3, column=2, sticky="ew", padx=50)

        ttk.Separator(plot_options_frame, orient='horizontal').grid(row=4, columnspan=5, sticky='ew', pady=5)

        #Show Best Peak: p
        ttk.Label(plot_options_frame, text='Show Best Peak:').grid(row=5, column=0, sticky='w', padx=5)

        self.show_best_peak_hv = tk.BooleanVar()
        self.show_best_peak_hv.set(True)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.show_best_peak_hv, command=update_hvplot_call).grid(row=5, column=1, sticky="ew", padx=15)

        self.show_best_peak_comp = tk.BooleanVar()
        self.show_best_peak_comp.set(True)
        bestPeakCompButton=ttk.Checkbutton(plot_options_frame, text="", variable=self.show_best_peak_comp, command=update_hvplot_call)
        bestPeakCompButton.grid(row=5, column=2, sticky="ew", padx=50)

        self.show_best_peak_spec = tk.BooleanVar()
        self.show_best_peak_spec.set(False)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.show_best_peak_spec, command=update_hvplot_call).grid(row=5, column=3, sticky="ew", padx=25)

        ttk.Separator(plot_options_frame, orient='horizontal').grid(row=6, columnspan=5, sticky='ew')

        #Annotate Best Peak: ann
        ttk.Label(plot_options_frame, text='Annotate Best Peak:').grid(row=7, column=0, sticky='w', padx=5)

        self.annotate_best_peak_hv = tk.BooleanVar()
        self.annotate_best_peak_hv.set(True)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.annotate_best_peak_hv, command=update_hvplot_call).grid(row=7, column=1, sticky="ew", padx=15)

        self.annotate_best_peak_comp = tk.BooleanVar()
        self.annotate_best_peak_comp.set(True)
        bestPeakCompAnnButton=ttk.Checkbutton(plot_options_frame, text="", variable=self.annotate_best_peak_comp, command=update_hvplot_call)
        bestPeakCompAnnButton.grid(row=7, column=2, sticky="ew", padx=50)

        self.annotate_best_peak_spec = tk.BooleanVar()
        self.annotate_best_peak_spec.set(True)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.annotate_best_peak_spec, command=update_hvplot_call).grid(row=7, column=3, sticky="ew", padx=25)

        ttk.Separator(plot_options_frame, orient='horizontal').grid(row=8, columnspan=5, sticky='ew')


        #Show all peaks (main H/V curve): all
        ttk.Label(plot_options_frame, text='Show All Peaks (H/V Curve):').grid(row=9, column=0, sticky='w', padx=5)

        self.show_all_peaks_hv = tk.BooleanVar()
        self.show_all_peaks_hv.set(False)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.show_all_peaks_hv, command=update_hvplot_call).grid(row=9, column=1, sticky="ew", padx=15)

        ttk.Separator(plot_options_frame, orient='horizontal').grid(row=10, columnspan=5, sticky='ew')

        #Show all curves: t
        ttk.Label(plot_options_frame, text='Show All H/V Curves:').grid(row=11, column=0, sticky='w', padx=5)

        self.show_ind_curves = tk.BooleanVar()
        self.show_ind_curves.set(False)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.show_ind_curves, command=update_hvplot_call).grid(row=11, column=1, sticky="ew", padx=15)

        ttk.Separator(plot_options_frame, orient='horizontal').grid(row=12, columnspan=5, sticky='ew')

        #Show individual peaks (tp): tp
        ttk.Label(plot_options_frame, text='Show Individual Peaks:').grid(row=13, column=0, sticky='w', padx=5)

        self.show_ind_peaks = tk.BooleanVar()
        self.show_ind_peaks.set(False)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.show_ind_peaks, command=update_hvplot_call).grid(row=13, column=1, sticky="ew", padx=15)

        ttk.Separator(plot_options_frame, orient='horizontal').grid(row=14, columnspan=5, sticky='ew')

        #Show individual peaks (tp): tp
        ttk.Label(plot_options_frame, text='Show Standard Deviation:').grid(row=15, column=0, sticky='w', padx=5)

        self.show_stDev_hv = tk.BooleanVar()
        self.show_stDev_hv.set(True)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.show_stDev_hv, command=update_hvplot_call).grid(row=15, column=1, sticky="ew", padx=15)

        self.show_stDev_comp = tk.BooleanVar()
        self.show_stDev_comp.set(True)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.show_stDev_comp, command=update_hvplot_call).grid(row=15, column=2, sticky="ew", padx=50)

        ttk.Separator(plot_options_frame, orient='horizontal').grid(row=16, columnspan=5, sticky='ew')

        ttk.Label(plot_options_frame, text='Show Legend:').grid(row=17, column=0, sticky='w', padx=5)

        self.show_legend = tk.BooleanVar()
        self.show_legend.set(False)
        ttk.Checkbutton(plot_options_frame, text="", variable=self.show_legend, command=update_hvplot_call).grid(row=17, column=2, sticky="ew", padx=50)


        #Specify X-Type
        ttk.Label(plot_options_frame, text='X Type:').grid(row=18, column=0, sticky='w', padx=5, pady=10)

        self.x_type = tk.StringVar()
        self.x_type.set('freq')
        ttk.Radiobutton(master=plot_options_frame, text='Frequency', variable=self.x_type, value='freq', command=update_hvplot_call).grid(row=18, column=1, sticky='w', padx=(5, 10), pady=10)
        ttk.Radiobutton(master=plot_options_frame, text='Period', variable=self.x_type, value='period', command=update_hvplot_call).grid(row=18, column=2, sticky='w', padx=(5, 10), pady=10)

        #kwargs
        ttk.Label(plot_options_frame, text='Matplotlib Keyword Arguments (not implemented):').grid(row=19, column=0, sticky='w', padx=5, pady=10)

        self.plot_kwargs = tk.StringVar()
        self.plot_kwargs.set("cmap='turbo'")
        ttk.Entry(plot_options_frame, textvariable=self.plot_kwargs).grid(row=19, column=1, columnspan=3, sticky="ew", pady=10)

        plot_options_frame.pack(fill='both', expand=True)#.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Create the plot_hvsr Call LabelFrame
        hvplot_call_frame = ttk.LabelFrame(plot_settings_tab, text="plot_hvsr() Call")

        #HVSR
        
        def get_kindstr():
            if self.hvsr_chart_bool.get():
                kindstr_hv = 'HVSR'
                if self.show_best_peak_hv.get():
                    kindstr_hv = kindstr_hv + ' p'
                if self.annotate_best_peak_hv.get():
                    kindstr_hv = kindstr_hv + ' ann'
                if self.show_all_peaks_hv.get():
                    kindstr_hv = kindstr_hv + ' all'
                if self.show_ind_curves.get():
                    kindstr_hv = kindstr_hv + ' t'
                if self.show_ind_peaks.get():
                    kindstr_hv = kindstr_hv.replace('t', 'tp')
                    if 'tp' not in kindstr_hv:
                        kindstr_hv = kindstr_hv+ ' tp'
                if not self.show_stDev_hv.get():
                    kindstr_hv = kindstr_hv + ' -s'
            else:
                kindstr_hv = ''

            #Comp
            if self.ind_comp_chart_bool.get():
                kindstr_c = 'c'

                if not self.show_comp_with_hv.get():
                    kindstr_c = kindstr_c + '+'

                    if self.show_best_peak_comp.get():
                        kindstr_c = kindstr_c + ' p'
                    if self.annotate_best_peak_comp.get():
                        kindstr_c = kindstr_c + ' ann'
                if not self.show_stDev_comp.get():
                    kindstr_c = kindstr_c + ' -s'
            else:
                kindstr_c = ''

            #Specgram
            if self.spec_chart_bool.get():
                kindstr_spec = 'Spec'

                if self.show_best_peak_spec.get():
                    kindstr_spec = kindstr_spec + ' p'
                if self.annotate_best_peak_spec.get():
                    kindstr_spec = kindstr_spec + ' ann'
            else:
                kindstr_spec = ''
            kindstr = kindstr_hv + ' ' +  kindstr_c + ' ' + kindstr_spec
            return kindstr
        

        # Add a Label widget to the plot_hvsr Call Label section
        hvplot_label = ttk.Label(hvplot_call_frame, text="plot_hvsr({}, remove_method='{}', xtype='{}', show_legend={}, {}, {})".format('hvsr_data', get_kindstr(), self.x_type.get(), self.show_legend.get(), '[...]', 'kwargs'))

        #Run button frame
        runFrame_set_plot = ttk.Frame(plot_settings_tab)
        runFrame_set_plot.columnconfigure(0, weight=1)

        self.settingsProgBar_plot = ttk.Progressbar(runFrame_set_plot, orient='horizontal')
        self.settingsProgBar_plot.grid(row=0, column=0, columnspan=10, sticky='ew')#.pack(fill='both',expand=True, side='left', anchor='sw')
        self.run_button = ttk.Button(runFrame_set_plot, text="Run", style='Run.TButton', command=process_data)

        
        def update_results_plot():
            self.tab_control.select(self.results_tab)
            sprit_hvsr.plot_hvsr(self.hvsr_results, plot_type=get_kindstr(), fig=self.fig_results, ax=self.ax_results, show_legend=self.show_legend.get(), use_subplots=True, clear_fig=False)

        self.update_results_plot_button = ttk.Button(runFrame_set_plot, text="Update Plot", style='Noise.TButton', command=update_results_plot, width=30)
        
        self.update_results_plot_button.grid(row=0, column=11, padx=2.5)#pack(side='right', anchor='se')
        self.run_button.grid(row=0, column=12, padx=2.5)#(side='right', anchor='se', padx=(10,0))

        runFrame_set_plot.pack(fill='both', side='bottom', anchor='e')
        hvplot_label.pack(fill='both', expand=True, padx=(10,0))#.grid(column=0, row=0, padx=10, pady=10, sticky="w")
        hvplot_call_frame.pack(fill='both', expand=True)#.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

        plot_settings_tab.pack(fill='both', expand=True)
        settings_notebook.add(plot_settings_tab, text="Plot Settings")

        # Pack the settings Notebook widget
        settings_notebook.pack(expand=True, fill='both')
        self.tab_control.add(self.settings_tab, text="Settings")

        # RESULTS TAB
        self.results_tab = ttk.Frame(self.tab_control)
        self.hvsr_results = {'site':''}#Just initialize for now

        # Create the Batch Site selection LabelFrame
        self.results_siteSelectFrame = ttk.LabelFrame(self.results_tab, text="HVSR Results")
        self.results_siteSelectLabel = ttk.Label(self.results_siteSelectFrame, text='Select Site ')

        def on_site_select():
            sitename =self.selectedSite.get()
            try: 
                report_results(self.hvsr_results[sitename])
            except:
                if sitename=='':
                    pass
                else:
                    messagebox.showwarning(title='WARNING', message=f"Site {sitename} does not exist")
                                                   
        if isinstance(self.hvsr_results, sprit_hvsr.HVSRBatch):
            sites = self.hvsr_results.sites
        else:
            sites = [self.hvsr_results['site']]
        self.site_options = sites
        self.selectedSite = tk.StringVar(value=sites[0])
        self.site_dropdown = ttk.Combobox(self.results_siteSelectFrame, textvariable=self.selectedSite, values=self.site_options, validate='focusout', validatecommand=on_site_select)
        self.site_dropdown.config(width=30)
        self.results_siteSelectLabel.grid(row=0, column=0, columnspan=1, sticky='ew')
        self.site_dropdown.grid(row=0, column=1, columnspan=4, sticky='ew')

        self.browse_results_fig = ttk.Button(self.results_siteSelectFrame, text="Update site",command=on_site_select)
        self.browse_results_fig.grid(row=0, column=8, sticky='ew', padx=5)

        self.results_siteSelectFrame.columnconfigure(9, weight=1)


        def update_site_dropdown():
            self.site_dropdown['values'] = self.site_options


        #lambda value=string: self.om_variable.set(value)
        # Create the plot_hvsr Call LabelFrame
        self.results_chartFrame = ttk.LabelFrame(self.results_tab, text="Data Plots")

        #Set up plot     
        self.fig_results = plt.figure()
        results_mosaic = [['hvsr'],['comp'],['spec']]
        self.ax_results = self.fig_results.subplot_mosaic(results_mosaic)

        self.results_canvas = FigureCanvasTkAgg(self.fig_results, master=self.results_chartFrame)  # A tk.DrawingArea.
        self.results_canvas.draw()
        self.results_canvasWidget = self.results_canvas.get_tk_widget()
        self.results_toolbar = NavigationToolbar2Tk(self.results_canvas, self.results_chartFrame, pack_toolbar=False)
        self.results_toolbar.update()
        self.results_toolbar.pack(fill=tk.X, side=tk.BOTTOM, expand=False)
        self.results_canvasWidget.pack(fill='both', expand=True)

        #Peak report
        self.results_peakInfoFrame = ttk.LabelFrame(self.results_tab, text="Peak Report")
        self.curveTitleLabel = ttk.Label(self.results_peakInfoFrame, text='Criteria for Reliable H/V Curve (all 3 must pass)')
        self.curveTest1Label = ttk.Label(self.results_peakInfoFrame, text='Window Length for Frequency')
        self.curveTest1ResultFrame = ttk.Frame(self.results_peakInfoFrame)
        self.curveTest1ResultText = ttk.Label(self.curveTest1ResultFrame, text='')
        self.curveTest1Result = ttk.Label(self.curveTest1ResultFrame, text='')

        self.curveTest2Label = ttk.Label(self.results_peakInfoFrame, text='Number of Significant Cycles')
        self.curveTest2ResultFrame = ttk.Frame(self.results_peakInfoFrame)
        self.curveTest2ResultText = ttk.Label(self.curveTest2ResultFrame, text='')
        self.curveTest2Result = ttk.Label(self.curveTest2ResultFrame, text='')

        self.curveTest3Label = ttk.Label(self.results_peakInfoFrame, text='Low Curve Standard Deviation for Frequencies Near Peak Over Time')
        self.curveTest3ResultFrame = ttk.Frame(self.results_peakInfoFrame)
        self.curveTest3ResultText = ttk.Label(self.curveTest3ResultFrame, text='')
        self.curveTest3Result = ttk.Label(self.curveTest3ResultFrame, text='')

        self.totalCurveResult = ttk.Label(self.results_peakInfoFrame, text='')

        self.peakTitleLabel = ttk.Label(self.results_peakInfoFrame, text='Criteria for a Clear H/V Peak (5/6 must pass)')
        self.peakTest1Label = ttk.Label(self.results_peakInfoFrame, text='H/V Amplitude is low Below Peak Frequency')
        self.peakTest1ResultFrame = ttk.Frame(self.results_peakInfoFrame)
        self.peakTest1ResultText = ttk.Label(self.peakTest1ResultFrame, text='')
        self.peakTest1Result = ttk.Label(self.peakTest1ResultFrame, text='')
        
        self.peakTest2Label = ttk.Label(self.results_peakInfoFrame, text='H/V Amplitude is low Above Peak Frequency')
        self.peakTest2ResultFrame = ttk.Frame(self.results_peakInfoFrame)
        self.peakTest2ResultText = ttk.Label(self.peakTest2ResultFrame, text='')
        self.peakTest2Result = ttk.Label(self.peakTest2ResultFrame, text='')
        
        self.peakTest3Label = ttk.Label(self.results_peakInfoFrame, text='Peak is Prominent')
        self.peakTest3ResultFrame = ttk.Frame(self.results_peakInfoFrame)
        self.peakTest3ResultText = ttk.Label(self.peakTest3ResultFrame, text='')
        self.peakTest3Result = ttk.Label(self.peakTest3ResultFrame, text='')
        
        self.peakTest4Label = ttk.Label(self.results_peakInfoFrame, text='Frequency of Peak is Stationary Over Time')
        self.peakTest4ResultFrame = ttk.Frame(self.results_peakInfoFrame)
        self.peakTest4ResultText = ttk.Label(self.peakTest4ResultFrame, text='')
        self.peakTest4Result = ttk.Label(self.peakTest4ResultFrame, text='')
        
        self.peakTest5Label = ttk.Label(self.results_peakInfoFrame, text='Standard Deviation of Peak Frequency is low ')
        self.peakTest5ResultFrame = ttk.Frame(self.results_peakInfoFrame)
        self.peakTest5ResultText = ttk.Label(self.peakTest5ResultFrame, text='')
        self.peakTest5Result = ttk.Label(self.peakTest5ResultFrame, text='')
        
        self.peakTest6Label = ttk.Label(self.results_peakInfoFrame, text='Standard Deviation of Peak Amplitude is low')
        self.peakTest6ResultFrame = ttk.Frame(self.results_peakInfoFrame)
        self.peakTest6ResultText = ttk.Label(self.peakTest6ResultFrame, text='')
        self.peakTest6Result = ttk.Label(self.peakTest6ResultFrame, text='')

        self.totalPeakResult = ttk.Label(self.results_peakInfoFrame, text='')

        self.totalResult = ttk.Label(self.results_peakInfoFrame, text='')

        self.curveTitleLabel.grid(row=0, sticky='w', padx=5, pady=2.5)
        self.curveTitleLabel.configure(font=("TkDefaultFont", 12, 'underline', 'bold'))
        self.curveTest1Label.grid(row=1, sticky='w', padx=5, pady=2.5)
        self.curveTest1ResultFrame.grid(row=2, sticky='ew', padx=5, pady=2.5)
        self.curveTest1ResultFrame.columnconfigure(0, weight=1)
        self.curveTest1ResultFrame.columnconfigure(1, weight=6)
        self.curveTest1ResultText.grid(row=0, column=0, sticky='e', padx=5, pady=2.5)
        self.curveTest1Result.grid(row=0, column=1, sticky='e', padx=5, pady=2.5)

        self.curveTest2Label.grid(row=3, sticky='w', padx=5, pady=2.5)
        self.curveTest2ResultFrame.grid(row=4, sticky='ew', padx=5, pady=2.5)
        self.curveTest2ResultFrame.columnconfigure(0, weight=1)
        self.curveTest2ResultFrame.columnconfigure(1, weight=6)
        self.curveTest2ResultText.grid(row=0, column=0, sticky='e', padx=5, pady=2.5)
        self.curveTest2Result.grid(row=0, column=1, sticky='e', padx=5, pady=2.5)

        self.curveTest3Label.grid(row=5, sticky='w', padx=5, pady=2.5)
        self.curveTest3ResultFrame.grid(row=6, sticky='ew', padx=5, pady=2.5)
        self.curveTest3ResultFrame.columnconfigure(0, weight=1)
        self.curveTest3ResultFrame.columnconfigure(1, weight=6)
        self.curveTest3ResultText.grid(row=0, column=0, sticky='e', padx=5, pady=2.5)
        self.curveTest3Result.grid(row=0, column=1, sticky='e', padx=5, pady=2.5)

        self.totalCurveResult.grid(row=7, sticky='e', padx=5, pady=10 )

        ttk.Separator(self.results_peakInfoFrame).grid(row=8, sticky='ew', pady=5)
        
        self.peakTitleLabel.grid(row=9, sticky='w', padx=5, pady=2.5)
        self.peakTitleLabel.configure(font=("TkDefaultFont", 12, 'underline', 'bold'))
        
        self.peakTest1Label.grid(row=11, sticky='w', padx=5, pady=2.5)
        self.peakTest1ResultFrame.grid(row=12, sticky='ew', padx=5, pady=2.5)
        self.peakTest1ResultFrame.columnconfigure(0, weight=1)
        self.peakTest1ResultFrame.columnconfigure(1, weight=6)
        self.peakTest1ResultText.grid(row=0, column=0, sticky='e', padx=5, pady=2.5)
        self.peakTest1Result.grid(row=0, column=1, sticky='e', padx=5, pady=2.5)

        self.peakTest2Label.grid(row=13, sticky='w', padx=5, pady=2.5)
        self.peakTest2ResultFrame.grid(row=14, sticky='ew', padx=5, pady=2.5)
        self.peakTest2ResultFrame.columnconfigure(0, weight=1)
        self.peakTest2ResultFrame.columnconfigure(1, weight=6)
        self.peakTest2ResultText.grid(row=0, column=0, sticky='e', padx=5, pady=2.5)
        self.peakTest2Result.grid(row=0, column=1, sticky='e', padx=5, pady=2.5)

        self.peakTest3Label.grid(row=15, sticky='w', padx=5, pady=2.5)
        self.peakTest3ResultFrame.grid(row=16, sticky='ew', padx=5, pady=2.5)
        self.peakTest3ResultFrame.columnconfigure(0, weight=1)
        self.peakTest3ResultFrame.columnconfigure(1, weight=6)
        self.peakTest3ResultText.grid(row=0, column=0, sticky='e', padx=5, pady=2.5)
        self.peakTest3Result.grid(row=0, column=1, sticky='e', padx=5, pady=2.5)

        self.peakTest4Label.grid(row=17, sticky='w', padx=5, pady=2.5)
        self.peakTest4ResultFrame.grid(row=18, sticky='ew', padx=5, pady=2.5)
        self.peakTest4ResultFrame.columnconfigure(0, weight=1)
        self.peakTest4ResultFrame.columnconfigure(1, weight=6)
        self.peakTest4ResultText.grid(row=0, column=0, sticky='e', padx=5, pady=2.5)
        self.peakTest4Result.grid(row=0, column=1, sticky='e', padx=5, pady=2.5)

        self.peakTest5Label.grid(row=19, sticky='w', padx=5, pady=2.5)
        self.peakTest5ResultFrame.grid(row=20, sticky='ew', padx=5, pady=2.5)
        self.peakTest5ResultFrame.columnconfigure(0, weight=1)
        self.peakTest5ResultFrame.columnconfigure(1, weight=6)
        self.peakTest5ResultText.grid(row=0, column=0, sticky='e', padx=5, pady=2.5)
        self.peakTest5Result.grid(row=0, column=1, sticky='e', padx=5, pady=2.5)

        self.peakTest6Label.grid(row=21, sticky='w', padx=5, pady=2.5)
        self.peakTest6ResultFrame.grid(row=22, sticky='ew', padx=5, pady=2.5)
        self.peakTest6ResultFrame.columnconfigure(0, weight=1)
        self.peakTest6ResultFrame.columnconfigure(1, weight=6)
        self.peakTest6ResultText.grid(row=0, column=0, sticky='e', padx=5, pady=2.5)
        self.peakTest6Result.grid(row=0, column=1, sticky='e', padx=5, pady=2.5)

        self.totalPeakResult.grid(row=23, sticky='e', padx=5, pady=10 )

        ttk.Separator(self.results_peakInfoFrame).grid(row=24, sticky='ew', pady=5)

        self.totalResult.grid(row=25, sticky='e', padx=5, pady=10 )

        self.resultsProgBar = ttk.Progressbar(self.results_peakInfoFrame, orient='horizontal')
        self.resultsProgBar.grid(row=26, column=0, sticky='ew')

        #Export results
        self.results_export_Frame = ttk.LabelFrame(self.results_tab, text="Export Results")
        
        ttk.Label(self.results_export_Frame, text="Export Figure").grid(row=0, column=0, sticky='ew', padx=5)
        self.results_fig_dir = tk.StringVar()
        self.results_fig_dir_entry = ttk.Entry(self.results_export_Frame, textvariable=self.results_fig_dir)
        self.results_fig_dir_entry.grid(row=0, column=1, columnspan=5, sticky='ew')
        
        def filepath_results_fig():
            filepath = filedialog.asksaveasfilename(defaultextension='png', initialdir=pathlib.Path(self.data_path.get()).parent, initialfile=self.params['site']+'_results.png')
            if filepath:
                self.results_fig_dir_entry.delete(0, 'end')
                self.results_fig_dir_entry.insert(0, filepath)
           
        def save_results_fig():
            if not self.save_ind_subplots.get():
                self.fig_results.savefig(self.results_fig_dir.get())
            else:
                for key in self.ax_results.keys():
                    extent = self.ax_results[key].get_tightbbox(self.fig_results.canvas.renderer).transformed(self.fig_results.dpi_scale_trans.inverted())
                    self.fig_results.savefig(pathlib.Path(self.results_fig_dir.get()).parent.as_posix()+'/Subplot'+key+'.png',  bbox_inches=extent)
        

        self.browse_results_fig = ttk.Button(self.results_export_Frame, text="Browse",command=filepath_results_fig)
        self.browse_results_fig.grid(row=0, column=7, sticky='ew', padx=2.5)
        
        self.save_results_fig = ttk.Button(self.results_export_Frame, text="Save",command=save_results_fig)
        self.save_results_fig.grid(row=0, column=8, columnspan=2, sticky='ew', padx=2.5)

        #Save subplots individually
        self.save_ind_subplots = tk.BooleanVar()
        self.save_ind_subplots.set(False)
        ttk.Checkbutton(self.results_export_Frame, text="Save ind. subplots", variable=self.save_ind_subplots).grid(row=0, column=10, sticky="ew", padx=5)

        #Export Peak Report        
        ttk.Label(self.results_export_Frame, text="Export Peak Report").grid(row=1, column=0, sticky='ew', padx=5)
        self.results_report_dir = tk.StringVar()
        self.results_report_dir_entry = ttk.Entry(self.results_export_Frame, textvariable=self.results_report_dir)
        self.results_report_dir_entry.grid(row=1, column=1, columnspan=5, sticky='ew')
        
        def filepath_report_fig():
            filepath = filedialog.asksaveasfilename(defaultextension='csv', initialdir=pathlib.Path(self.data_path.get()).parent, initialfile=self.params['site']+'_peakReport.csv')
            if filepath:
                self.results_report_dir_entry.delete(0, 'end')
                self.results_report_dir_entry.insert(0, filepath)
        
        def save_report_fig():
            sprit_hvsr.get_report(self.hvsr_results, format='plot',  export=self.results_report_dir.get())

        self.browse_results_fig = ttk.Button(self.results_export_Frame, text="Browse",command=filepath_report_fig)
        self.browse_results_fig.grid(row=1, column=7, sticky='ew', padx=2.5)
        
        self.save_results_fig = ttk.Button(self.results_export_Frame, text="Save",command=save_report_fig)
        self.save_results_fig.grid(row=1, column=8, columnspan=2, sticky='ew', padx=2.5)
        self.results_export_Frame.columnconfigure(1, weight=1)
        
        self.results_siteSelectFrame.grid(row=0,column=0, columnspan=8, rowspan=2, sticky='ew')
        self.results_peakInfoFrame.grid(row=0,  column=9, columnspan=2, rowspan=8, sticky='nsew')#.pack(side='right', fill='both')
        self.results_chartFrame.grid(row=2,     column=0, columnspan=8, rowspan=6, sticky='nsew')#.pack(side='top', expand=True, fill='both')
        self.results_export_Frame.grid(row=9,   column=0, columnspan=11,rowspan=2,sticky='nsew')#.pack(side='bottom', fill='x')
        self.results_tab.columnconfigure(0, weight=1)
        self.results_tab.rowconfigure(2, weight=1)
        

        # LOG TAB
        self.log_tab = ttk.Frame(self.tab_control)
        
        from tkinter import scrolledtext
        self.logFrame = ttk.LabelFrame(self.log_tab, text='Log')
        self.logFrame.columnconfigure(0, weight=1)
        self.logFrame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(self.logFrame, wrap = tk.WORD)#, width=200, height=50)
        self.log_text.configure(font=("Courier", 11))
        #text_area.grid(row=0, column=0, sticky='nsew')
        self.log_text.grid(row=0, rowspan=10, column=0, sticky='nsew')#.pack(fill='both', expand=True)

        self.logProgBar = ttk.Progressbar(self.logFrame, orient='horizontal')
        self.logProgBar.grid(row=11, column=0, sticky='nsew')

        introLogText = "Log of active session:\n"
        self.log_text.insert('end', introLogText)
        #log_text.configure(bg='black', fg='white')


        self.logFrame.pack(fill='both', expand=True)#.pack(fill='both', expand=True, side='top', anchor='nw')
        self.log_tab.pack(fill='both', expand=True, side='left', anchor='nw')
        
        # Add log tab to tab control
        self.tab_control.add(self.log_tab, text="Log")
        # Add result tab to tab control
        self.tab_control.add(self.results_tab, text="Results".center(11, ' ').center(13,'|'))

        # Pack tab control
        self.tab_control.pack(expand=True, fill="both")


#Decorator that catches errors and warnings (to be modified later for gui)
def _catch_errors(func):
    global spritApp

    #Define a local function to get a list of warnings that we'll use in the output
    def get_warning_msg_list(w):
        messageList = []
        #Collect warnings that happened before we got to the error
        if w:
            hasWarnings = True
            for wi in w:
                warning_category = type(wi.message).__name__.title().replace('warning','Warning')
                #if w.line is None:
                #    w.line = linecache.getline(wi.filename, wi.lineno)
                warning_lineNo = wi.lineno
                warning_message = str(wi.message)
                # append the warning category and message to messageList so we get all warnings
                messageList.append(f'{warning_category} ({warning_lineNo}): {warning_message}')
        return messageList
    
    # use functools.wraps to preserve the original function's metadata
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        result = None
        # use the global keyword to access the error_message and error_category variables
        global error_message
        global error_category
        global spritApp

        messageList = []
        hasWarnings = False
        # use a try-except block to catch any exceptions
        #result = func(*args, **kwargs)
        try:
            # use a context manager to catch any warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter('always')
                # call the original function with the given arguments
                result = func(*args, **kwargs)
                
                #Get message list, [] if no messages, doesn't run at all if Error/exception in func
                messageList = get_warning_msg_list(w)
                if messageList == []:
                    return result
                else:
                    warningMessage = "WARNING:"
                    for msg in messageList:
                        warningMessage = "\n {}".format(msg)

                    messagebox.showwarning(title='WARNINGS', message=warningMessage)
                    
        except Exception as e:
            messageList = get_warning_msg_list(w)
            errorObj = sys.exc_info()[2]

            mainErrText = sys.exc_info()[1]

            mainErrTb = traceback.extract_tb(sys.exc_info()[2])[-1]
            mainErrFilePath = pathlib.Path(mainErrTb[0])
            
            mainErrFileName = mainErrFilePath.stem
            mainErrLineNo = mainErrTb[1]
            mainErrFunc = mainErrTb[2]
            mainErrCodeLine = mainErrTb[3]

            errLineNo1 = str(traceback.extract_tb(sys.exc_info()[2])[-1].lineno)
            error_category = type(e).__name__.title().replace('error', 'Error')
            error_message = f"{e} ({errLineNo1})"
            
            #Get message list, [] if no messages, doesn't run at all if Error/exception in func
            warningMessageList = get_warning_msg_list(w)

            #Build error messages
            tbTuple0 = sys.exc_info()[0]
            tbTuple1 = sys.exc_info()[1]
            tbTuple2 = traceback.extract_tb(sys.exc_info()[2])
            
            logMsg = f"**ERROR**\n{tbTuple0.__name__}: {tbTuple1}"
            dialogErrMsg = logMsg.split(':')[1]
            for tb in tbTuple2:
                logMsg = logMsg + '\n\t'
                logMsg = logMsg + f"{pathlib.Path(tb[0]).stem}.{tb[2]}(): {tb[3]} (Line {tb[1]})"
                dialogErrMsg = dialogErrMsg + f"\n{pathlib.Path(tb[0]).stem}.{tb[2]}(), Line {tb[1]}"
            logMsg = logMsg + '\n\n'

            #fullErrorMessage = f'ERROR {mainErrFileName}.{mainErrFunc} ({mainErrLineNo}): {mainErrText} \n\n {mainErrFileName} Line {mainErrLineNo}: {mainErrCodeLine}.'
            if messageList == []:
                pass
            else:
                dialogErrMsg = dialogErrMsg+"\n\n  Additional Warnings along the way. See Log for more information."
                logMsg = logMsg + "\n\n\t  *WARNING(S)*\n\tAdditional Warnings along the way:"
                for addMsg in warningMessageList:
                    logMsg = logMsg+"\n\t\t{}".format(addMsg)


            SPRIT_App.log_errorMsg(spritApp, logMsg)

            messagebox.showerror(title=f'ERROR ({error_category})',
                                    message=dialogErrMsg)
            update_progress_bars(100)

        # return the result of the function or the error/warning messages and categories
        return result
    # return the wrapper function
    return wrapper

def on_closing():
    plt.close('all')
    root.destroy()
    sys.exit()

def reboot_app():
    """Restarts the current program.
    Note: this function does not return. Any cleanup action (like
    saving data) must be done before calling this function."""
    python = sys.executable
    os.execl(python, python, * sys.argv)

if __name__ == "__main__":
    can_gui = sprit_utils._check_gui_requirements()  

    if can_gui:
        global root
        root = tk.Tk()
        try:
            try:
                icon_path = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources').joinpath('icon').joinpath('sprit_icon_alpha.ico')
                root.iconbitmap(icon_path)
            except:
                icon_path = pathlib.Path(str(importlib.resources.files('sprit'))).joinpath('resources').joinpath('icon').joinpath('sprit_icon.png')
                root.iconphoto(False, tk.PhotoImage(file=icon_path.as_posix()))
        except Exception as e:
            print("ICON NOT LOADED, still opening GUI")

        root.resizable(True, True)
        spritApp = SPRIT_App(root)
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    else:
        print("GUI cannot be created")
