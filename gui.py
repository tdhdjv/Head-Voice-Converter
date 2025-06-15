import dearpygui.dearpygui as dpg
from scipy.signal import freqz, lfilter

from equalizer import *
from config import *
from recording import *

class App:
    def __init__(self):
        dpg.create_context() 
        dpg.create_viewport()
        
        self.recording = RecordingData()
        self.converted = RecordingData()

        self.gui_layout()
    
    def run(self):
        dpg.show_viewport()
        dpg.setup_dearpygui()
        self.loop()
    
    def end(self):
        dpg.destroy_context()

    def scroll(self, _, app_data:int, user_data):
        if dpg.is_item_hovered(user_data["item"]): 
            user_data["recording_data"].current_time -= app_data/10
            user_data["recording_data"].current_time = max(0, min(user_data["recording_data"].max_time, user_data["recording_data"].current_time))

    def add_audio_plot(self, xAxisTag:int|str, yAxisTag:int|str, graphTag:int|str, recording_data:RecordingData, height:int=240):
        with dpg.plot(width=-1, height=height, no_mouse_pos=True, no_title=True) as plot:
            dpg.add_plot_axis(dpg.mvXAxis, tag=xAxisTag)
            dpg.add_plot_axis(dpg.mvYAxis, tag=yAxisTag,
                no_gridlines=True, no_tick_labels=True, no_tick_marks=True, no_label=True)

            dpg.set_axis_limits(yAxisTag, -Y_AXIS_MAX, Y_AXIS_MAX)
            dpg.add_line_series([], [], tag=graphTag, parent=yAxisTag)

            with dpg.handler_registry():
                dpg.add_mouse_wheel_handler(callback=self.scroll, user_data={"item":plot, "recording_data":recording_data})

    def convert(self):
        self.converted.max_time = self.recording.max_time
        average_db = 0
        for i in range(1, 9): average_db += dpg.get_value(SLIDER+str(i))
        average_db /= 8
        average_db = 0
        #equalizer
        converted = self.recording.recording[:int(self.recording.current_time*self.recording.samplerate)]
        for i in range(1, 8):
            dbGain = dpg.get_value(SLIDER+str(i))-average_db
            center_freq = 150 * np.power(2, i-1)

            b, a = peaking(Q_FACTOR, dbGain, center_freq, SAMPLE_RATE)
            converted = lfilter(b, a, converted, axis=0)
        
        #last one is a shelving function
        dbGain = dpg.get_value(SLIDER_8)-average_db
        center_freq = SAMPLE_RATE/np.power(2, calculate_bandwidth(Q_FACTOR)/2)

        b, a = shelving(Q_FACTOR, dbGain, center_freq, SAMPLE_RATE)
        converted = lfilter(b, a, converted, axis=0)

        volume = dpg.get_value(VOLUME_SLIDER)
        converted *= np.power(10, volume/20)

        self.converted.recording = converted[:]
        self.converted.condensed_recording = np.ascontiguousarray(converted[::SAMPLE_RATE//CONDENSED_SAMPLE_RATE, :])

    def gui_layout(self):
        dpg.set_global_font_scale(2.0)
        with dpg.window(tag="root"):
            dpg.add_spacer(height=10)
            #audio plot
            self.add_audio_plot(RECORDER_X_AXIS, RECORDER_Y_AXIS, RECORDING_GRAPH, self.recording)           

            #buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="Record", callback=lambda:toggle_record(self.recording))
                dpg.add_button(label="To Start", callback=lambda:start(self.recording))
                dpg.add_button(label="Play", callback=lambda:toggle_play(self.recording))
                dpg.add_button(label="Convert", callback=self.convert)

            dpg.add_spacer(height=10)
            
            #audio plot
            self.add_audio_plot(CONVERTED_X_AXIS, CONVERTED_Y_AXIS, CONVERTED_GRAPH, self.converted)

            #buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="Play", callback=lambda:toggle_play(self.converted))
                dpg.add_button(label="To Start", callback=lambda:start(self.converted))

        #frequency analysis
        with dpg.window(width=1050, height=550, pos=(0, 750)):
            with dpg.group(horizontal=True):
                with dpg.plot(width=500, height=500, no_mouse_pos=True, no_title=True):
                    dpg.add_plot_axis(dpg.mvXAxis, tag=FREQ_X_AXIS)
                    dpg.add_plot_axis(dpg.mvYAxis, tag=FREQ_Y_AXIS)
                    
                    dpg.set_axis_limits(FREQ_X_AXIS, 0, 22050)
                    dpg.set_axis_limits(FREQ_Y_AXIS, 0, 2000)
                    
                    dpg.add_line_series([], [], tag="freq_domain", parent=FREQ_Y_AXIS)
                with dpg.plot(width=500, height=500, no_mouse_pos=True, no_title=True):
                    dpg.add_plot_axis(dpg.mvXAxis, tag=FREQ_CONVERTED_X_AXIS)
                    dpg.add_plot_axis(dpg.mvYAxis, tag=FREQ_CONVERTED_Y_AXIS)
                    
                    dpg.set_axis_limits(FREQ_CONVERTED_X_AXIS, 0, 22050)
                    dpg.set_axis_limits(FREQ_CONVERTED_Y_AXIS, 0, 2000)
                    
                    dpg.add_line_series([], [], tag="converted_freq_domain", parent=FREQ_CONVERTED_Y_AXIS)
        
        with dpg.window(width=1000, height=1000, pos=(1000, 750)):
            with dpg.group(horizontal=True):
                dpg.add_slider_int(tag=SLIDER_1, default_value=12, vertical=True, height=500, width=30, min_value=-5, max_value=20)
                dpg.add_slider_int(tag=SLIDER_2, default_value=13, vertical=True, height=500, width=30, min_value=-5, max_value=20)
                dpg.add_slider_int(tag=SLIDER_3, default_value=13, vertical=True, height=500, width=30, min_value=-5, max_value=20)
                dpg.add_slider_int(tag=SLIDER_4, default_value=12, vertical=True, height=500, width=30, min_value=-5, max_value=20)
                dpg.add_slider_int(tag=SLIDER_5, default_value=11, vertical=True, height=500, width=30, min_value=-5, max_value=20)
                dpg.add_slider_int(tag=SLIDER_6, default_value=9, vertical=True, height=500, width=30, min_value=-5, max_value=20)
                dpg.add_slider_int(tag=SLIDER_7, default_value=6, vertical=True, height=500, width=30, min_value=-5, max_value=20)         
                dpg.add_slider_int(tag=SLIDER_8, default_value=5, vertical=True, height=500, width=30, min_value=-5, max_value=20)
                dpg.add_spacer(width=100)
                dpg.add_slider_int(tag=VOLUME_SLIDER, default_value=-5, vertical=True, height=500, width=45, min_value=-35, max_value=0)
        
            with dpg.plot(width=-1,height=-1):
                dpg.add_plot_axis(dpg.mvXAxis, tag=EQ_X_AXIS, scale=dpg.mvPlotScale_Log10)
                dpg.add_plot_axis(dpg.mvYAxis, tag=EQ_Y_AXIS)

                dpg.set_axis_limits(EQ_X_AXIS, 10, 44100)
                dpg.set_axis_limits(EQ_Y_AXIS, -15, 60)

                dpg.add_line_series([], [], tag=EQ_GRAPH, parent=EQ_Y_AXIS)

        dpg.set_primary_window("root", True)

    def update_recorder(self, xAxisTag:int|str, plotTag:int|str, recordingData:RecordingData, view_width:int) :
        dpg.set_axis_limits(xAxisTag, -view_width/300+recordingData.current_time,  view_width/300+recordingData.current_time)

        #graph
        recording_start_time = max(recordingData.current_time - view_width/300, 0)
        recording_end_time = min(recordingData.current_time + view_width/300, recordingData.max_time)

        time_array = np.arange(recording_start_time, recording_end_time, 1.0/recordingData.condensed_samplerate)
        start_pointer = int(recording_start_time*recordingData.condensed_samplerate)
        end_pointer = start_pointer + time_array.size

        dpg.set_value(plotTag, value=(time_array, recordingData.condensed_recording[start_pointer:end_pointer]))

    def update_layout(self):
        view_width, view_height = dpg.get_viewport_width(), dpg.get_viewport_height()

        self.update_recorder(RECORDER_X_AXIS, RECORDING_GRAPH, self.recording, view_width)
        self.update_recorder(CONVERTED_X_AXIS, CONVERTED_GRAPH, self.converted, view_width)

        #update eq
        
        total = np.zeros(SAMPLE_RATE)
        frequencies = np.arange(0, SAMPLE_RATE)
        for i in range(1, 8):
            dbGain = dpg.get_value(SLIDER+str(i))
            center_freq = 150 * np.power(2, i-1)

            b, a = peaking(Q_FACTOR, dbGain, center_freq, SAMPLE_RATE)
            _, h = freqz(b, a, worN=SAMPLE_RATE)
            total += 20*np.log10(np.abs(h))
        
        #last one is a shelving function
        dbGain = dpg.get_value(SLIDER_8)
        center_freq = SAMPLE_RATE/np.power(2, calculate_bandwidth(Q_FACTOR)/2)

        b, a = shelving(Q_FACTOR, dbGain, center_freq, SAMPLE_RATE)
        _, h = freqz(b, a, worN=SAMPLE_RATE)
        total += 20*np.log10(np.abs(h))

        dpg.set_value(EQ_GRAPH, value=(list(frequencies), list(total)))  

    def loop(self):
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

            update_recording_data(self.recording)
            update_recording_data(self.converted)
            self.update_layout()
        
if __name__ == "__main__":
    app = App()
    app.run()
    app.end()