import datetime
import inspect
import os
import pathlib
import webbrowser

from zoneinfo import available_timezones

import ipywidgets as widgets
from IPython.display import display, clear_output
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import plotly.subplots as subplots
from scipy import signal

try:
    import sprit_hvsr
except:
    import sprit.sprit_hvsr as sprit_hvsr

def read_data(button):
    progress_bar.value = 0
    log_textArea.value += f"\n\nREADING DATA [{datetime.datetime.now()}]"

    ip_kwargs = get_input_params()
    hvsr_data = sprit_hvsr.input_params(**ip_kwargs, verbose=verbose_check.value)
    log_textArea.value += f"\n\n{datetime.datetime.now()}\ninput_params():\n'{ip_kwargs}"
    if button.description=='Read Data':
        progress_bar.value=0.333
    else:
        progress_bar.value=0.1
    fd_kwargs = get_fetch_data_params()
    hvsr_data = sprit_hvsr.fetch_data(hvsr_data, **fd_kwargs, verbose=verbose_check.value)
    log_textArea.value += '\n\n'+str(datetime.datetime.now())+'\nfetch_data():\n\t'+str(fd_kwargs)
    if button.description=='Read Data':
        progress_bar.value=0.666
    else:
        progress_bar.value=0.2
    
    use_hv_curve_rmse.value=False
    use_hv_curve_rmse.disabled=True

    update_preview_fig(hvsr_data, preview_fig)

    if button.description=='Read Data':
        sprit_tabs.selected_index = 1
        progress_bar.value=0
    return hvsr_data

def get_remove_noise_kwargs():
    def get_remove_method():
        remove_method_list=[]
        do_stalta = stalta_check.value
        do_sat_pct = max_saturation_check.value
        do_noiseWin=noisy_windows_check.value
        do_warmcool=warmcool_check.value
        
        if auto_remove_check.value:
            remove_method_list=['stalta', 'saturation', 'noise', 'warmcool']
        else:
            if do_stalta:
                remove_method_list.append('stalta')
            if do_sat_pct:
                remove_method_list.append('saturation')
            if do_noiseWin:
                remove_method_list.append('noise')
            if do_warmcool:
                remove_method_list.append('warmcool')
        
        if not remove_method_list:
            remove_method_list = None
        return remove_method_list
    
    remove_noise_kwargs = {'remove_method':get_remove_method(),
                            'sat_percent':max_saturation_pct.value, 
                            'noise_percent':max_window_pct.value,
                            'sta':sta.value,
                            'lta':lta.value, 
                            'stalta_thresh':[stalta_thresh_low.value, stalta_thresh_hi.value], 
                            'warmup_time':warmup_time.value,
                            'cooldown_time':cooldown_time.value,
                            'min_win_size':noisy_window_length.value,
                            'remove_raw_noise':raw_data_remove_check.value,
                            'verbose':verbose_check.value}
    return remove_noise_kwargs

def get_generate_ppsd_kwargs():
    ppsd_kwargs = {
        'skip_on_gaps':skip_on_gaps.value,
        'db_bins':[db_bins_min.value, db_bins_max.value, db_bins_step.value],
        'ppsd_length':ppsd_length.value,
        'overlap':overlap_pct.value,
        'special_handling':special_handling_dropdown.value,
        'period_smoothing_width_octaves':period_smoothing_width.value,
        'period_step_octaves':period_step_octave.value,
        'period_limits':[period_limits_min.value, period_limits_max.value],
        'verbose':verbose_check.value
        }

    if str(ppsd_kwargs['special_handling']).lower() == 'none':
        ppsd_kwargs['special_handling'] = None        
    return ppsd_kwargs

def get_remove_outlier_curve_kwargs():
    roc_kwargs = {
            'use_percentile':rmse_pctile_check.value,
            'rmse_thresh':rmse_thresh.value,
            'use_hv_curve':False,
            'verbose':verbose_check.value
        }
    return roc_kwargs

def get_process_hvsr_kwargs():
    if smooth_hv_curve_bool.value:
        smooth_value = smooth_hv_curve.value
    else:
        smooth_value = smooth_hv_curve_bool.value

    if resample_hv_curve_bool.value:
        resample_value = resample_hv_curve.value
    else:
        resample_value = resample_hv_curve_bool.value

    ph_kwargs={'method':h_combine_meth.value,
                'smooth':smooth_value,
                'freq_smooth':freq_smoothing.value,
                'f_smooth_width':freq_smooth_width.value,
                'resample':resample_value,
                'outlier_curve_rmse_percentile':use_hv_curve_rmse.value,
                'verbose':verbose_check.value}
    return ph_kwargs

def get_check_peaks_kwargs():
    cp_kwargs = {'hvsr_band':[hvsr_band_min_box.value, hvsr_band_max_box.value],
                'peak_freq_range':[peak_freq_range_min_box.value, peak_freq_range_max_box.value],
                'peak_selection':peak_selection_type.value,
                'verbose':verbose_check.value}
    return cp_kwargs

def get_get_report_kwargs():
    def get_formatted_plot_str():
        # Initialize plot string
        hvsr_plot_str = ''
        comp_plot_str = ''
        spec_plot_str = ''

        # Whether to use each plot
        if use_plot_hv.value:
            hvsr_plot_str=hvsr_plot_str + "HVSR"
        if use_plot_comp.value:
            comp_plot_str=comp_plot_str + "C"
        if use_plot_spec.value:
            spec_plot_str=spec_plot_str + "SPEC"

        # Whether components be on the same plot as HV curve?
        if not combine_hv_comp.value:
            comp_plot_str=comp_plot_str + "+"
        else:
            comp_plot_str=comp_plot_str.replace('+','')

        # Whether to show (log) standard deviations
        if not show_std_hv.value:
            hvsr_plot_str=hvsr_plot_str + " -s"
        if not show_std_comp.value:
            comp_plot_str=comp_plot_str + " -s"                

        # Whether to show all peaks
        if show_all_peaks_hv.value:
            hvsr_plot_str=hvsr_plot_str + " all"

        # Whether curves from each time window are shown
        if show_all_curves_hv.value:
            hvsr_plot_str=hvsr_plot_str + " t"
        if show_all_curves_comp.value:
            comp_plot_str=comp_plot_str + " t"

        # Whether the best peak is displayed
        if show_best_peak_hv.value:
            hvsr_plot_str=hvsr_plot_str + " p"
        if show_best_peak_comp.value:
            comp_plot_str=comp_plot_str + " p"
        if show_best_peak_spec.value:
            spec_plot_str=spec_plot_str + " p"

        # Whether best peak value is annotated
        if ann_best_peak_hv.value:
            hvsr_plot_str=hvsr_plot_str + " ann"
        if ann_best_peak_comp.value:
            comp_plot_str=comp_plot_str + " ann"
        if ann_best_peak_spec.value:
            spec_plot_str=spec_plot_str + " ann"

        # Whether peaks from individual time windows are shown
        if show_ind_peaks_hv.value:
            hvsr_plot_str=hvsr_plot_str + " tp"
        if show_ind_peaks_spec.value:
            spec_plot_str=spec_plot_str + ' tp'
        
        # Whether to show legend
        if show_legend_hv.value:
            hvsr_plot_str=hvsr_plot_str + " leg"
        if ann_best_peak_comp.value:
            comp_plot_str=comp_plot_str + " leg"
        if show_legend_spec.value:
            spec_plot_str=spec_plot_str + " leg"            

        # Combine string into one
        plot_str = hvsr_plot_str + ' ' + comp_plot_str+ ' ' + spec_plot_str
        return plot_str

    gr_kwargs = {'report_format':['print','csv'],
                    'plot_type':get_formatted_plot_str(),
                    'export_path':None,
                    'csv_overwrite_opt':'overwrite',
                    'no_output':False,
                'verbose':verbose_check.value
                    }
    return gr_kwargs

def process_data(button):
    startProc=datetime.datetime.now()
    progress_bar.value = 0
    log_textArea.value += f"\n\nPROCESSING DATA [{startProc}]"
    global hvsr_data
    # Read data again only if internal hvsr_data input_data variable is different from what is in the gui
    if not 'hvsr_data' in globals() or not hasattr(hvsr_data, 'input_data') or \
            (pathlib.Path(hvsr_data.input_data).as_posix() != pathlib.Path(data_filepath.value).as_posix()):
        hvsr_data = read_data(button)

    remove_noise_kwargs = get_remove_noise_kwargs()
    hvsr_data = sprit_hvsr.remove_noise(hvsr_data, **remove_noise_kwargs)
    log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_noise()\n\t{remove_noise_kwargs}"
    progress_bar.value = 0.3

    generate_ppsd_kwargs = get_generate_ppsd_kwargs()
    hvsr_data = sprit_hvsr.generate_ppsds(hvsr_data, **generate_ppsd_kwargs)
    progress_bar.value = 0.5
    log_textArea.value += f"\n\n{datetime.datetime.now()}\ngenerate_ppsds()\n\t{generate_ppsd_kwargs}"
    
    
    # If this was started by clicking "Generate PPSDs", stop here
    if button.description == 'Generate PPSDs':
        return

    ph_kwargs = get_process_hvsr_kwargs()
    hvsr_data = sprit_hvsr.process_hvsr(hvsr_data, **ph_kwargs)
    log_textArea.value += f"\n\n{datetime.datetime.now()}\nprocess_hvsr()\n\t{ph_kwargs}"
    progress_bar.value = 0.75
    update_outlier_fig()

    roc_kwargs = get_remove_outlier_curve_kwargs()
    hvsr_data = sprit_hvsr.remove_outlier_curves(hvsr_data, **roc_kwargs)
    log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_outlier_curves()\n\t{roc_kwargs}"
    progress_bar.value = 0.85
    outlier_fig, hvsr_data = update_outlier_fig()

    use_hv_curve_rmse.value=False
    use_hv_curve_rmse.disabled=False

    def get_rmse_range():
        minRMSE = 10000
        maxRMSE = -1
        if roc_kwargs['use_hv_curve']:
            colnames = ['HV_Curves']
        else:
            colnames = ['psd_values_Z',
                        'psd_values_E',
                        'psd_values_N']
        dataList = []
        for col in colnames:
            dataArr = np.stack(hvsr_data.hvsr_windows_df[col])
            medCurveArr = np.nanmedian(dataArr, axis=0)
            rmse = np.sqrt(((np.subtract(dataArr, medCurveArr)**2).sum(axis=1))/dataArr.shape[1])
            if rmse.min() < minRMSE:
                minRMSE = rmse.min()
            if rmse.max() > maxRMSE:
                maxRMSE = rmse.max()
        rmse_thresh_slider.min = minRMSE
        rmse_thresh_slider.max = maxRMSE
        rmse_thresh_slider.step = round((maxRMSE-minRMSE)/100, 2)
        rmse_thresh_slider.value = maxRMSE
    get_rmse_range()

    cp_kwargs = get_check_peaks_kwargs()
    hvsr_data = sprit_hvsr.check_peaks(hvsr_data, **cp_kwargs)
    log_textArea.value += f"\n\n{datetime.datetime.now()}\ncheck_peaks()\n\t{cp_kwargs}"
    progress_bar.value = 0.9

    gr_kwargs = get_get_report_kwargs()
    hvsr_data = sprit_hvsr.get_report(hvsr_data, **gr_kwargs)
    log_textArea.value += f"\n\n{datetime.datetime.now()}\nget_report()\n\t{gr_kwargs}\n\n"
    hvsr_data.get_report(report_format='print') # Just in case print wasn't included
    log_textArea.value += hvsr_data['Print_Report']
    printed_results_textArea.value = hvsr_data['Print_Report']
    hvsr_data.get_report(report_format='csv') 
    results_table.value = hvsr_data['CSV_Report'].to_html()
    
    log_textArea.value += f'Processing time: {datetime.datetime.now() - startProc}'
    progress_bar.value = 0.95

    update_results_fig(hvsr_data, gr_kwargs['plot_type'])
    
    progress_bar.value = 1
    global hvsr_results
    hvsr_results = hvsr_data
    return hvsr_results
    
def parse_plot_string(plot_string):
    plot_list = plot_string.split()

    hvsrList = ['hvsr', 'hv', 'h']
    compList = ['component', 'comp', 'c']
    compPlus = [item + '+' for item in compList]
    specList = ['spectrogram', 'specgram', 'spec','sg', 's']

    hvInd = np.nan
    compInd = np.nan
    specInd = np.nan

    hvIndFound = False
    compIndFound = False
    specIndFound = False

    for i, item in enumerate(plot_list):
        if item.lower() in hvsrList and not hvIndFound:
            # assign the index
            hvInd = i
            hvIndFound = True
        if (item.lower() in compList or item.lower() in compPlus) and not compIndFound:
            # assign the index
            compInd = i
            compIndFound = True
        if item.lower() in specList and not specIndFound:
            # assign the index
            specInd = i
            specIndFound = True

    # Get individual plot lists (should already be correctly ordered)
    if hvInd is np.nan:
        hvsr_plot_list = ['HVSR']

    if compInd is np.nan:
        comp_plot_list = []
        if specInd is np.nan:
            if hvInd is not np.nan:
                hvsr_plot_list = plot_list
            spec_plot_list = []
        else:
            if hvInd is not np.nan:
                hvsr_plot_list = plot_list[hvInd:specInd]
            spec_plot_list = plot_list[specInd:]
    else:
        if hvInd is not np.nan:
            hvsr_plot_list = plot_list[hvInd:compInd]
        
        if specInd is np.nan:
            comp_plot_list = plot_list[compInd:]
            spec_plot_list = []
        else:
            comp_plot_list = plot_list[compInd:specInd]
            spec_plot_list = plot_list[specInd:]

    # Figure out how many subplots there will be
    plot_list_list = [hvsr_plot_list, comp_plot_list, spec_plot_list]

    return plot_list_list

def parse_hv_plot_list(hv_data, hvsr_plot_list, results_fig=None, azimuth='HV'):
    hvsr_data = hv_data
    hv_plot_list = hvsr_plot_list[0]
    x_data = hvsr_data.x_freqs['Z']
    hvsrDF = hvsr_data.hvsr_windows_df

    plotymax = max(hvsr_data.hvsrp2['HV']) + (max(hvsr_data.hvsrp2['HV']) - max(hvsr_data.hvsr_curve))
    ylim = [0, plotymax]


    if results_fig is None:
        results_fig = go.Figure()

    if azimuth == 'HV':
        HVCol = 'HV_Curves'
    else:
        HVCol = 'HV_Curves_'+azimuth

    if 'tp' in hv_plot_list:
        allpeaks = []
        for row in hvsrDF[hvsrDF['Use']]['CurvesPeakFreqs_'+azimuth].values:
            for peak in row:
                allpeaks.append(peak)
        allInd = []
        for row, peakList in enumerate(hvsrDF[hvsrDF['Use']]['CurvesPeakIndices_'+azimuth].values):
            for ind in peakList:
                allInd.append((row, ind))
        x_vals = []
        y_vals = []
        y_max = np.nanmax(hvsr_data.hvsrp[azimuth])
        hvCurveInd = list(hvsrDF.columns).index(HVCol)

        for i, tp in enumerate(allpeaks):
            x_vals.extend([tp, tp, None]) # add two x values and a None
            y_vals.extend([0, hvsrDF.iloc[allInd[i][0], hvCurveInd][allInd[i][1]], None]) # add the first and last y values and a None            

        results_fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode='lines',
                                        line=dict(width=4, dash="solid", 
                                        color="rgba(128,0,0,0.1)"), 
                                        name='Best Peaks Over Time'),
                                        row=1, col=1)

    if 't' in hv_plot_list:
        alltimecurves = np.stack(hvsrDF[hvsrDF['Use']][HVCol])
        for i, row in enumerate(alltimecurves):
            if i==0:
                showLeg = True
            else:
                showLeg= False
            results_fig.add_trace(go.Scatter(x=x_data[:-1], y=row, mode='lines',
                                        line=dict(width=0.5, dash="solid", 
                                        color="rgba(100, 110, 100, 0.8)"), 
                                        showlegend=showLeg,
                                        name='Ind. time win. curve', 
                                        hoverinfo='none'),
                                        row=1, col=1)

    if 'all' in hv_plot_list:
        for i, p in enumerate(hvsr_data['hvsr_peak_freqs'][azimuth]):
            if i==0:
                showLeg = True
            else:
                showLeg= False

            results_fig.add_trace(go.Scatter(
                x=[p, p, None], # set x to None
                y=[0, np.nanmax(np.stack(hvsrDF[HVCol])),None], # set y to None
                mode="lines", # set mode to lines
                line=dict(width=1, dash="dot", color="gray"), # set line properties
                name="All checked peaks", # set legend name
                showlegend=showLeg),
                row=1, col=1)

    if 'fr' in hv_plot_list:
        lowX = [hvsr_data.hvsr_band[0], hvsr_data.hvsr_band[0]]
        lowWinX = [hvsr_data.peak_freq_range[0], hvsr_data.peak_freq_range[0]]
        hiWinX = [hvsr_data.peak_freq_range[1], hvsr_data.peak_freq_range[1]]
        hiX =  [hvsr_data.hvsr_band[1], hvsr_data.hvsr_band[1]]
        
        yPts = ylim
        
        # Show windows where peak_freq_range is
        results_fig.add_trace(go.Scatter(x=lowWinX, y=yPts,
                                line={'color':'black', 'width':0.1}, marker=None,
                                fill='tozerox', fillcolor="rgba(128, 100, 100, 0.6)",
                                showlegend=False, name='Peak Frequency exclusion range',
                                hoverinfo='none'),
                                row=1, col=1)
        
        results_fig.add_trace(go.Scatter(x=hiWinX, y=yPts,
                                line={'color':'black', 'width':0.1},marker=None, 
                                showlegend=False,
                                hoverinfo='none'),
                                row=1, col=1)
        
        results_fig.add_trace(go.Scatter(x=hiX, y=yPts,
                                line=None, marker=None,
                                fill='tonextx', fillcolor="rgba(128, 100, 100, 0.6)",
                                name='Peak frequency exclusion range', hoverinfo='none'),
                                row=1, col=1)        

    if '-s' not in hv_plot_list:
        # Show standard deviation
        results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.hvsrp2[azimuth],
                                line={'color':'black', 'width':0.1},marker=None, 
                                showlegend=False, name='Log. St.Dev. Upper',
                                hoverinfo='none'),
                                row=1, col=1)
        
        results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.hvsrm2[azimuth],
                                line={'color':'black', 'width':0.1},marker=None,
                                fill='tonexty', fillcolor="rgba(128, 128, 128, 0.6)",
                                name='Log. St.Dev.', hoverinfo='none'),
                                row=1, col=1)
            
    if 'p' in hv_plot_list:
        results_fig.add_trace(go.Scatter(
            x=[hvsr_data['BestPeak'][azimuth]['f0'], hvsr_data['BestPeak'][azimuth]['f0'], None], # set x to None
            y=[0,np.nanmax(np.stack(hvsrDF['HV_Curves'])),None], # set y to None
            mode="lines", # set mode to lines
            line=dict(width=1, dash="dash", color="black"), # set line properties
            name="Best Peak"),
            row=1, col=1)

    if 'ann' in hv_plot_list:
        # Annotate best peak
        results_fig.add_annotation(x=np.log10(hvsr_data['BestPeak'][azimuth]['f0']),
                                y=0, yanchor='bottom', xanchor='center',
                                text=f"{hvsr_data['BestPeak'][azimuth]['f0']:.3f} Hz",
                                bgcolor='rgba(255, 255, 255, 0.7)',
                                showarrow=False,
                                row=1, col=1)
    return results_fig

def parse_comp_plot_list(hv_data, comp_plot_list, plot_with_hv=False, results_fig=None, azimuth='HV'):
    
    hvsr_data = hv_data
    if results_fig is None:
        results_fig=go.Figure()

    # Initial setup
    x_data = hvsr_data.x_freqs['Z']
    hvsrDF = hvsr_data.hvsr_windows_df
    
    same_plot = False
    if plot_with_hv:
        same_plot = True
    else:
        same_plot = ((comp_plot_list != []) and ('+' not in comp_plot_list[0]))

    if same_plot:
        yaxis_to_use = 'y2'
        use_secondary = True
        transparency_modifier = 0.5
    else:
        yaxis_to_use = 'y'
        use_secondary=False
        transparency_modifier = 1

    # Keep components if azimuth is used, but make them lighter
    if len(hvsr_data.hvsr_az.keys()) > 0:
        h_transparency_modifier = transparency_modifier * 0.5
    else:
        h_transparency_modifier = transparency_modifier
        
    v_transparency_modifier = transparency_modifier
    az_transparency_modifier = transparency_modifier

        
    h_alpha = 0.4 * h_transparency_modifier
    v_alpha = 0.4 * v_transparency_modifier
    az_alpha = 0.4 * az_transparency_modifier
    components = ['Z', 'E', 'N']

    compColor_semi_light = {'Z':f'rgba(128,128,128,{v_alpha})',
                'E':f'rgba(0,0,128,{h_alpha})',
                'N':f'rgba(128,0,0,{h_alpha})'}

    h_alpha = 0.7 * h_transparency_modifier
    v_alpha = 0.7 * v_transparency_modifier
    az_alpha = 0.7 * az_transparency_modifier    
    compColor_semi = {'Z':f'rgba(128,128,128,{v_alpha})',
                    'E':f'rgba(100,100,128,{h_alpha})', 
                    'N':f'rgba(128,100,100,{h_alpha})'}

    compColor = {'Z':f'rgba(128,128,128,{v_alpha})', 
                'E':f'rgba(100,100,250,{h_alpha})', 
                'N':f'rgba(250,100,100,{h_alpha})'}

    for az in hvsr_data.hvsr_az.keys():
        components.append(az)
        compColor_semi_light[az] = f'rgba(0,128,0,{az_alpha})'
        compColor_semi[az] = f'rgba(100,128,100,{az_alpha})'
        compColor[az] = f'rgba(100,250,100,{az_alpha})'

    # Whether to plot in new subplot or not
    if same_plot:
        compRow=1
    else:
        compRow=2

    # Whether to plot individual time curves
    if 't' in comp_plot_list:
        for comp in components:
            alltimecurves = np.stack(hvsrDF[hvsrDF['Use']]['psd_values_'+comp])
            for i, row in enumerate(alltimecurves):
                if i==0:
                    showLeg = True
                else:
                    showLeg= False
                
                results_fig.add_trace(go.Scatter(x=x_data[:-1], y=row, mode='lines',
                                line=dict(width=0.5, dash="solid", 
                                color=compColor_semi[comp]),
                                name='Ind. time win. curve',
                                showlegend=False,
                                hoverinfo='none',
                                yaxis=yaxis_to_use),
                                secondary_y=use_secondary,
                                row=compRow, col=1)

    # Code to plot standard deviation windows, if not removed
    if '-s' not in comp_plot_list:
        for comp in components:
            # Show standard deviation
            results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.ppsd_std_vals_p[comp],
                                    line={'color':compColor_semi_light[comp], 'width':0.1},marker=None, 
                                    showlegend=False, name='Log. St.Dev. Upper',
                                    hoverinfo='none',    
                                    yaxis=yaxis_to_use),
                                    secondary_y=use_secondary,
                                    row=compRow, col=1)
            
            results_fig.add_trace(go.Scatter(x=x_data, y=hvsr_data.ppsd_std_vals_m[comp],
                                    line={'color':compColor_semi_light[comp], 'width':0.1},marker=None,
                                    fill='tonexty', fillcolor=compColor_semi_light[comp],
                                    name=f'St.Dev. [{comp}]', hoverinfo='none', showlegend=False, 
                                    yaxis=yaxis_to_use),
                                    secondary_y=use_secondary,
                                    row=compRow, col=1)
            
    # Code to plot location of best peak
    if 'p' in comp_plot_list:
        minVal = 10000
        maxVal = -10000
        for comp in components:
            currPPSDCurve = hvsr_data['psd_values_tavg'][comp]
            if np.nanmin(currPPSDCurve) < minVal:
                minVal = np.nanmin(currPPSDCurve)
            if np.nanmax(currPPSDCurve) > maxVal:
                maxVal = np.nanmax(currPPSDCurve)

        results_fig.add_trace(go.Scatter(
            x=[hvsr_data['BestPeak'][azimuth]['f0'], hvsr_data['BestPeak'][azimuth]['f0'], None], # set x to None
            y=[minVal,maxVal,None], # set y to None
            mode="lines", # set mode to lines
            line=dict(width=1, dash="dash", color="black"), # set line properties
            name="Best Peak",
            yaxis=yaxis_to_use),
            secondary_y=use_secondary,
            row=compRow, col=1)
        
    # Code to annotate value of best peak
    if 'ann' in comp_plot_list:
        minVal = 1e6 # A high number to compare against (comparer should always be lower)
        for comp in components:
            currPPSDCurve = hvsr_data['ppsd_std_vals_m'][comp]
            if np.nanmin(currPPSDCurve) < minVal:
                minVal = np.nanmin(currPPSDCurve)
        results_fig.add_annotation(x=np.log10(hvsr_data['BestPeak'][azimuth]['f0']),
                        y=minVal,
                        text=f"{hvsr_data['BestPeak'][azimuth]['f0']:.3f} Hz",
                        bgcolor='rgba(255, 255, 255, 0.7)',
                        showarrow=False,
                        yref=yaxis_to_use,
                        secondary_y=use_secondary,
                        row=compRow, col=1)

    # Plot the main averaged component PPSDs
    for comp in components:
        results_fig.add_trace(go.Scatter(x=hvsr_data.x_freqs[comp],
                                        y=hvsr_data['psd_values_tavg'][comp],
                                        line=dict(width=2, dash="solid", 
                                        color=compColor[comp]),marker=None, 
                                        name='PPSD Curve '+comp,    
                                        yaxis=yaxis_to_use), 
                                        secondary_y=use_secondary,
                                        row=compRow, col='all')

    # If new subplot, update accordingly
    if compRow==2:
        results_fig.update_xaxes(type='log',
                        range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                        row=compRow, col=1)
    return results_fig

def parse_spec_plot_list(hv_data, spec_plot_list, subplot_num, results_fig=None, azimuth='HV'):
    hvsr_data = hv_data

    if results_fig is None:
        results_fig=go.Figure()

    if azimuth == 'HV':
        HVCol = 'HV_Curves'
    else:
        HVCol = 'HV_Curves_'+azimuth

    # Initial setup
    hvsrDF = hvsr_data.hvsr_windows_df
    specAxisTimes = np.array([dt.isoformat() for dt in hvsrDF.index.to_pydatetime()])
    y_data = hvsr_data.x_freqs['Z'][1:]
    image_data = np.stack(hvsrDF[HVCol]).T

    maxZ = np.percentile(image_data, 100)
    minZ = np.percentile(image_data, 0)

    use_mask = hvsr_data.hvsr_windows_df.Use.values
    use_mask = np.tile(use_mask, (image_data.shape[0],1))
    use_mask = np.where(use_mask is False, np.nan, use_mask)

    hmap = go.Heatmap(z=image_data,
                x=specAxisTimes,
                y=y_data,
                colorscale='Turbo',
                showlegend=False,
                #opacity=0.7,
                hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>H/V Amplitude: %{z:.2f}<extra></extra>',
                zmin=minZ,zmax=maxZ, showscale=False, name='HV Curve Amp. over Time')
    results_fig.add_trace(hmap, row=subplot_num, col=1)

    data_used = go.Heatmap(
        x=specAxisTimes,
        y=y_data,
        z=use_mask.astype(bool),
        showlegend=False,
        colorscale=[[0, 'rgba(0,0,0,0.66)'], [0.25, 'rgba(0,0,0,0.66)'], [1, 'rgba(250,250,250,0)']],
        showscale=False, name='Used')
    results_fig.add_trace(data_used, row=subplot_num, col=1)


    # tp currently is not being added to spec_plot_list
    if 'tp' in spec_plot_list:
        yvals = []
        for row in hvsrDF[HVCol].values:
            maxInd = np.argmax(row)
            yvals.append(y_data[maxInd])
        tp_trace = go.Scatter(x=specAxisTimes, y=yvals, mode='markers',
                                line=None, marker=dict(color='white', size=2, line=dict(color='black', width=0.1)), name='Individual H/V Peaks')
        results_fig.add_trace(tp_trace, row=subplot_num, col='all')

    if 'p' in spec_plot_list:
        results_fig.add_hline(y=hvsr_data['BestPeak'][azimuth]['f0'], line_width=1, line_dash='dash', line_color='black', row=subplot_num, col='all')

    if 'ann' in spec_plot_list:
        results_fig.add_annotation(x=specAxisTimes[-1],
                                y=hvsr_data['hvsr_band'][1],
                                text=f"Peak: {hvsr_data['BestPeak'][azimuth]['f0']:.3f} Hz",
                                bgcolor='rgba(255, 255, 255, 0.7)',
                                showarrow=False, xanchor='right', yanchor='top',
                                row=subplot_num, col='all')

    if 'leg' in spec_plot_list:
        pass

    results_fig.update_yaxes(type='log',
                    range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                    row=subplot_num, col=1)

    results_fig.add_annotation(
        text=f"{hvsrDF['Use'].astype(bool).sum()}/{hvsrDF.shape[0]} windows used",
        x=max(specAxisTimes),
        y=np.log10(min(y_data))+(np.log10(max(y_data))-np.log10(min(y_data)))*0.01,
        xanchor="right", yanchor="bottom",bgcolor='rgba(256,256,256,0.7)',
        showarrow=False,row=subplot_num, col=1)

    return results_fig

def plot_results(hv_data, plot_string='HVSR p ann C+ p SPEC ann', results_fig=None, results_graph_widget=None, return_fig=False, show_results_plot=True):
    if  results_fig is None:
        results_fig = go.FigureWidget()

    hvsr_data = hv_data

    xlim = [hvsr_data.hvsr_band[0], hvsr_data.hvsr_band[1]]
    plotymax = max(hvsr_data.hvsrp2['HV']) + (max(hvsr_data.hvsrp2['HV']) - max(hvsr_data.hvsr_curve))
    ylim = [0, plotymax]

    if isinstance(hvsr_data, sprit_hvsr.HVSRBatch):
        hvsr_data=hvsr_data[0]

    hvsrDF = hvsr_data.hvsr_windows_df

    plot_list = parse_plot_string(plot_string)

    combinedComp=False
    # By default there 3 subplots
    noSubplots = 3
    # Remove any subplots that are not indicated by plot_type parameter
    noSubplots = noSubplots - plot_list.count([])
    
    # Now, check if comp plot is combined with HV
    if plot_list[1] != [] and '+' not in plot_list[1][0]:
        combinedComp = True
        noSubplots -= 1
    
    # Get all data for each plotted item
    # Get subplot numbers based on plot_list
    spec=[]
    if plot_list[0]==[]:
        # if for some reason, HVSR plot was not indicated, add it
        hv_plot_row = 1 # Default first row to hv (may change later)
        noSubplots += 1
        if plot_list[1] == []:
            comp_plot_row = None
            if plot_list[2] == []:
                spec_plot_row = None
                hv_plot_row = 1 #If nothing specified, do basic h/v plot
            else:
                spec_plot_row = 1 # If only spec specified
        else:
            comp_plot_row = 1 # If no HV specified by comp is, comp is subplot 1

            if plot_list[2] == []:
                spec_plot_row = None
            else:
                spec_plot_row = 2 # If only comp and spec specified comp first then spec
    else:
        hv_plot_row = 1 # HV specified explicitly
        if plot_list[1] == []:
            comp_plot_row = None
            if plot_list[2] == []:
                spec_plot_row = None
            else:
                spec_plot_row = 2 # if no comp specified, spec is 2nd subplot
        else:
            if combinedComp:
                comp_plot_row = 1
                if plot_list[2] == []:
                    spec_plot_row = None
                else:
                    spec_plot_row = 2
            else:
                comp_plot_row = 2
                if plot_list[2] == []:
                    spec_plot_row = None
                else:
                    spec_plot_row = 3       

    specList=[]
    rHeights=[1]
    if hv_plot_row == 1:
        if comp_plot_row == 1:
            specList.append([{'secondary_y': True}])
            if spec_plot_row == 2:
                specList.append([{'secondary_y': False}])
    else:
        specList.append([{'secondary_y': False}])

        if noSubplots >= 2:
            specList.append([{'secondary_y': False}])
            rHeights = [1.5,1]
        if noSubplots == 3:
            specList.append([{'secondary_y': False}])
            rHeights = [2,1.5,1]
    
    # Failsafes
    while len(specList)<noSubplots:
        specList.append([{}])

    while len(rHeights)<noSubplots:
        rHeights.append(1)

    # Re-initialize results_fig
    results_fig.data = []
    results_fig.update_layout(grid=None)  # Clear the existing grid layout, in case applicable

    results_subp = subplots.make_subplots(rows=noSubplots, cols=1, horizontal_spacing=0.01, vertical_spacing=0.07,
                                specs=specList,
                                row_heights=rHeights)
    results_fig.update_layout(grid={'rows': noSubplots})

    results_fig = go.FigureWidget(results_subp)

    if plot_list[1] != []:
        results_fig = parse_comp_plot_list(hvsr_data, results_fig=results_fig, comp_plot_list=plot_list[1])
        results_fig.update_xaxes(title_text='Frequency [Hz]', row=comp_plot_row, col=1)

    # HVSR Plot (plot this after COMP so it is on top COMP and to prevent deletion with no C+)
    results_fig = parse_hv_plot_list(hvsr_data, hvsr_plot_list=plot_list, results_fig=results_fig)
    
    # Will always plot the HV Curve
    results_fig.add_trace(go.Scatter(x=hvsr_data.x_freqs['Z'],y=hvsr_data.hvsr_curve,
                        line={'color':'black', 'width':1.5}, marker=None, name='HVSR Curve'),
                        row=1, col='all')
    # SPEC plot
    if plot_list[2] != []:
        results_fig = parse_spec_plot_list(hvsr_data, spec_plot_list=plot_list[2], subplot_num=spec_plot_row, results_fig=results_fig)

    # Final figure updating
    resultsFigWidth=800

    components_HV_on_same_plot = (plot_list[1]==[] or '+' not in plot_list[1][0])
    if components_HV_on_same_plot:
        compxside = 'bottom'
        secondaryY = True
        showHVTickLabels = True
        showComptickLabels = True
    else:
        compxside = 'bottom'
        secondaryY = False
        showHVTickLabels = True
        showComptickLabels = True
    
    # Update H/V Plot
    results_fig.update_xaxes(type='log', title_text='Frequency [Hz]', title_standoff=0,
                    range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                    side='bottom', showticklabels=showHVTickLabels,
                    row=1, col=1)
    results_fig.update_yaxes(title_text='H/V Ratio', row=1, col=1, secondary_y=False, range=ylim)

    # Update Component plot
    results_fig.update_xaxes(type='log',overlaying='x', showticklabels=showComptickLabels,  title_standoff=0,
                             range=[np.log10(hvsr_data['hvsr_band'][0]), np.log10(hvsr_data['hvsr_band'][1])],
                             side=compxside, row=comp_plot_row, col=1)    
    results_fig.update_yaxes(title_text="PPSD Amp\n[m2/s4/Hz][dB]", secondary_y=secondaryY, row=comp_plot_row, col=1)

    # Update Spec plot
    results_fig.update_yaxes(title_text='H/V Over Time', row=noSubplots, col=1)

    # Update entire figure
    results_fig.update_layout(margin={"l":10, "r":10, "t":35, 'b':0},
                            showlegend=False, autosize=True, width=resultsFigWidth, height=resultsFigWidth*0.8,
                            title=f"{hvsr_data['site']} Results")
    
    # Reset results_graph_widget and display 
    if results_graph_widget is not None:
        with results_graph_widget:
            clear_output(wait=True)
            display(results_fig)

    if show_results_plot:
        results_fig.show()
    
    if return_fig:
        return results_fig

def plot_preview(hv_data, stream=None, preview_fig=None, spectrogram_component='Z', show_plot=True, return_fig=False):
    if preview_fig is None:
        preview_subp = subplots.make_subplots(rows=4, cols=1, shared_xaxes=True, horizontal_spacing=0.01, vertical_spacing=0.01, row_heights=[3,1,1,1])
        #preview_fig = go.FigureWidget(preview_subp)
        preview_fig = go.Figure(preview_subp)

    preview_fig.data = []
    
    hvsr_data = hv_data
    if isinstance(hvsr_data, sprit_hvsr.HVSRBatch):
        hvsr_data=hvsr_data[0]

    if stream is not None:
        # This is only used for fetch_data, which ['stream'] has not yet been defined
        hvsr_data['stream'] = stream

    if isinstance(hvsr_data, (sprit_hvsr.HVSRData, dict)):
        stream_z = hvsr_data['stream'].select(component='Z').merge()
        stream_e = hvsr_data['stream'].select(component='E').merge()
        stream_n = hvsr_data['stream'].select(component='N').merge()
        hvsrBand = hvsr_data['hvsr_band']
        siteName = hvsr_data['site']
    else:
        # This is in case data is an obspy stream
        stream_z = hvsr_data.select(component='Z').merge()
        stream_e = hvsr_data.select(component='E').merge()
        stream_n = hvsr_data.select(component='N').merge()
        hvsrBand = [0.4, 40]
        siteName = 'HVSRSite'

    # Get iso_times and datetime.datetime
    utcdt = stream_z[0].times(type='utcdatetime')
    iso_times=[]
    dt_times = []
    for t in utcdt:
        if t is not np.ma.masked:
            iso_times.append(t.isoformat())
            dt_times.append(datetime.datetime.fromisoformat(t.isoformat()))
        else:
            iso_times.append(np.nan)
    iso_times=np.array(iso_times)
    dt_times = np.array (dt_times)

    # Generate spectrogram
    specKey=spectrogram_component.upper()
    specStreamDict = {'Z':stream_z[0],
                      'E':stream_e[0],
                      'N':stream_n[0]}
    f, t, Sxx = signal.spectrogram(x=specStreamDict[specKey].data, fs=specStreamDict[specKey].stats.sampling_rate, mode='magnitude')
    
    # Get times for the axis (one time per window)
    axisTimes = []
    for tpass in t:
        axisTimes.append((dt_times[0]+datetime.timedelta(seconds=tpass)).isoformat())

    # Add data to preview_fig
    # Add spectrogram of Z component
    minz = np.percentile(Sxx, 1)
    maxz = np.percentile(Sxx, 99)
    hmap = go.Heatmap(z=Sxx,
                x=axisTimes,
                y=f,
                colorscale='Turbo',
                showlegend=False,
                hovertemplate='Time [UTC]: %{x}<br>Frequency [Hz]: %{y:.2f}<br>Spectrogram Magnitude: %{z:.2f}<extra></extra>',
                zmin=minz, zmax=maxz, showscale=False, name=f'{specKey} Component Spectrogram')
    preview_fig.add_trace(hmap, row=1, col=1)
    preview_fig.update_yaxes(type='log', range=[np.log10(hvsrBand[0]), np.log10(hvsrBand[1])], row=1, col=1)
    preview_fig.update_yaxes(title={'text':f'Spectrogram ({specKey})'}, row=1, col=1)

    # Add raw traces
    dec_factor=5 #This just makes the plotting go faster, by "decimating" the data
    preview_fig.add_trace(go.Scatter(x=iso_times[::dec_factor], y=stream_z[0].data[::dec_factor],
                                    line={'color':'black', 'width':0.5},marker=None, name='Z component data'), row=2, col='all')
    preview_fig.update_yaxes(title={'text':'Z'}, row=2, col=1)
    preview_fig.add_trace(go.Scatter(x=iso_times[::dec_factor], y=stream_e[0].data[::dec_factor],
                                    line={'color':'blue', 'width':0.5},marker=None, name='E component data'),row=3, col='all')
    preview_fig.update_yaxes(title={'text':'E'}, row=3, col=1)
    preview_fig.add_trace(go.Scatter(x=iso_times[::dec_factor], y=stream_n[0].data[::dec_factor],
                                    line={'color':'red', 'width':0.5},marker=None, name='N component data'), row=4, col='all')
    preview_fig.update_yaxes(title={'text':'N'}, row=4, col=1)
    
    #preview_fig.add_trace(p)
    preview_fig.update_layout(margin={"l":10, "r":10, "t":30, 'b':0}, showlegend=False,
                                title=f"{siteName} Data Preview")

    if show_plot:
        preview_fig.show()

    if return_fig:
        return preview_fig

def plot_outlier_curves(hvsr_data, plot_engine='plotly', rmse_thresh=0.98, use_percentile=True, use_hv_curve=False, from_roc=False, show_plot=True, verbose=False):
    hv_data = hvsr_data
    #outlier_fig = go.FigureWidget()
    outlier_fig = go.Figure()

    roc_kwargs = {'rmse_thresh':rmse_thresh,
                    'use_percentile':True,
                    'use_hv_curve':use_hv_curve,
                    'show_outlier_plot':False,
                    'plot_engine':'None',
                    'verbose':verbose
                    }
    if 'PPSDStatus' in hvsr_data.ProcessingStatus.keys() and hvsr_data.ProcessingStatus['PPSDStatus']:
        #log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_outlier_curves():\n'{roc_kwargs}"    
        #hvsr_data = sprit_hvsr.remove_outlier_curves(hvsr_data, **roc_kwargs)
        pass
    else:
        #log_textArea.value += f"\n\n{datetime.datetime.now()}\nremove_outlier_curves() attempted, but not completed. hvsr_data.ProcessingStatus['PPSDStatus']=False\n'{roc_kwargs}"
        return outlier_fig

    if roc_kwargs['use_hv_curve']:
        no_subplots = 1
        if hasattr(hvsr_data, 'hvsr_windows_df') and 'HV_Curves' in hvsr_data.hvsr_windows_df.columns:
            outlier_fig.data = []
            outlier_fig.update_layout(grid=None)  # Clear the existing grid layout
            outlier_subp = subplots.make_subplots(rows=no_subplots, cols=1, horizontal_spacing=0.01, vertical_spacing=0.1)
            outlier_fig.update_layout(grid={'rows': 1})
            #outlier_fig = go.FigureWidget(outlier_subp)
            outlier_fig = go.Figure(outlier_subp)

            x_data = hvsr_data['x_freqs']
            curve_traces = []
            for hv in hvsr_data.hvsr_windows_df['HV_Curves'].iterrows():
                curve_traces.append(go.Scatter(x=x_data, y=hv[1]))
            outlier_fig.add_traces(curve_traces)
            
            # Calculate a median curve, and reshape so same size as original
            medCurve = np.nanmedian(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']), axis=0)
            outlier_fig.add_trace(go.Scatter(x=x_data, y=medCurve, line=dict(color='rgba(0,0,0,1)', width=1.5),showlegend=False))
            
            minY = np.nanmin(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']))
            maxY = np.nanmax(np.stack(hvsr_data.hvsr_windows_df['HV_Curves']))
            totalWindows = hvsr_data.hvsr_windows_df.shape[0]
            #medCurveArr = np.tile(medCurve, (curr_data.shape[0], 1))

    else:
        no_subplots = 3
        outlier_fig.data = []
        outlier_fig.update_layout(grid=None)  # Clear the existing grid layout
        outlier_subp = subplots.make_subplots(rows=no_subplots, cols=1, horizontal_spacing=0.01, vertical_spacing=0.02,
                                                row_heights=[1, 1, 1])
        outlier_fig.update_layout(grid={'rows': 3})
        #outlier_fig = go.FigureWidget(outlier_subp)
        outlier_fig = go.Figure(outlier_subp)

        if hasattr(hvsr_data, 'hvsr_windows_df'):
            rowDict = {'Z':1, 'E':2, 'N':3}
            showTLabelsDict={'Z':False, 'E':False, 'N':True}
            def comp_rgba(comp, a):
                compstr = ''
                if comp=='Z':
                    compstr = f'rgba(0, 0, 0, {a})'
                if comp=='E':
                    compstr = f'rgba(50, 50, 250, {a})'
                if comp=='N':
                    compstr = f'rgba(250, 50, 50, {a})'
                return compstr                         
            compNames = ['Z', 'E', 'N']
            rmse_to_plot=[]
            med_traces=[]

            noRemoved = 0
            indRemoved = []
            for i, comp in enumerate(compNames):
                if hasattr(hvsr_data, 'x_freqs'):
                    x_data = hvsr_data['x_freqs'][comp]
                else:
                    x_data = [1/p for p in hvsr_data['ppsds'][comp]['period_xedges'][1:]]                    
                column = 'psd_values_'+comp
                # Retrieve data from dataframe (use all windows, just in case)
                curr_data = np.stack(hvsr_data['hvsr_windows_df'][column])
                
                # Calculate a median curve, and reshape so same size as original
                medCurve = np.nanmedian(curr_data, axis=0)
                medCurveArr = np.tile(medCurve, (curr_data.shape[0], 1))
                medTrace = go.Scatter(x=x_data, y=medCurve, line=dict(color=comp_rgba(comp, 1), width=1.5), 
                                                name=f'{comp} Component', showlegend=True)
                # Calculate RMSE
                rmse = np.sqrt(((np.subtract(curr_data, medCurveArr)**2).sum(axis=1))/curr_data.shape[1])

                rmse_threshold = np.percentile(rmse, roc_kwargs['rmse_thresh'])
                
                # Retrieve index of those RMSE values that lie outside the threshold
                timeIndex = hvsr_data['hvsr_windows_df'].index
                for j, curve in enumerate(curr_data):
                    if rmse[j] > rmse_threshold:
                        badTrace = go.Scatter(x=x_data, y=curve,
                                            line=dict(color=comp_rgba(comp, 1), width=1.5, dash='dash'),
                                            #marker=dict(color=comp_rgba(comp, 1), size=3),
                                            name=str(hvsr_data.hvsr_windows_df.index[j]), showlegend=False)
                        outlier_fig.add_trace(badTrace, row=rowDict[comp], col=1)
                        if j not in indRemoved:
                            indRemoved.append(j)
                        noRemoved += 1
                    else:
                        goodTrace = go.Scatter(x=x_data, y=curve,
                                                line=dict(color=comp_rgba(comp, 0.01)), name=str(hvsr_data.hvsr_windows_df.index[j]), showlegend=False)
                        outlier_fig.add_trace(goodTrace, row=rowDict[comp], col=1)

                #timeIndRemoved = pd.DatetimeIndex([timeIndex[ind] for ind in indRemoved])
                #hvsr_data['hvsr_windows_df'].loc[timeIndRemoved, 'Use'] = False

                outlier_fig.add_trace(medTrace, row=rowDict[comp], col=1)
                
                outlier_fig.update_xaxes(showticklabels=False, row=1, col=1)
                outlier_fig.update_yaxes(title={'text':'Z'}, row=1, col=1)
                outlier_fig.update_xaxes(showticklabels=False, row=2, col=1)
                outlier_fig.update_yaxes(title={'text':'E'}, row=2, col=1)
                outlier_fig.update_xaxes(showticklabels=True, row=3, col=1)
                outlier_fig.update_yaxes(title={'text':'N'}, row=3, col=1)

                outlier_fig.update_layout(margin={"l":10, "r":10, "t":30, 'b':0}, showlegend=True,
                                title=f"{hvsr_data['site']} Outliers")
                if comp == 'N':
                    minY = np.nanmin(curr_data)
                    maxY = np.nanmax(curr_data)
                totalWindows = curr_data.shape[0]
            
            outlier_fig.add_annotation(
                text=f"{len(indRemoved)}/{totalWindows} outlier windows removed",
                x=np.log10(max(x_data)) - (np.log10(max(x_data))-np.log10(min(x_data))) * 0.01,
                y=minY+(maxY-minY)*0.01,
                xanchor="right", yanchor="bottom",#bgcolor='rgba(256,256,256,0.7)',
                showarrow=False,row=no_subplots, col=1)


    outlier_fig.update_xaxes(type='log')
    #with outlier_graph_widget:
    #    clear_output(wait=True)
    #    display(outlier_fig)
    
    hvsr_data['OutlierPlot'] = outlier_fig # not currently using
    if show_plot:
        outlier_fig.show()

    return outlier_fig
