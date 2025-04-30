from tkinter import * 
import time # time
import serial # values collected from serial monitor
import matplotlib.pyplot as plt # graphing
import matplotlib.animation as animation # animating the graphing
import tkinter as tk # importing tkinter in general
from tkinter import simpledialog, messagebox # pop up boxes
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # embedding plot in main window
from PIL import Image, ImageTk # importing the logo

# Global variables ~ initializing them
dataList = [] 
timeList = []
startTime = None
ser = None
ani = None
filename = ""
real_time_value = 0

# Create the main window
root = tk.Tk()
root.title("Resonance")
root.config(bg='#58B6C0') # teal color from FBS website
root.geometry("2000x2000") # full size screen for Mac

# Create label to indicate arduino connection
# This is in the main window so will be found above buttons and graph
status_label = tk.Label(root, text="Not connected", bg='#58B6C0', font=("Helvetica", 12))
status_label.pack(pady=10)

# Create a main frame to split buttons and plot
frame = tk.Frame(root, bg='#58B6C0')
frame.pack(fill=BOTH, expand=True) # Fills the entire screen left to right

# Left frame for buttons
button_frame = tk.Frame(frame, bg='#58B6C0')
button_frame.pack(side=LEFT, padx=20, pady=10)

# This uploads the logo and places it correctly
try:
    logo = Image.open("/Users/clarekeeler/Desktop/tkinter_vscode/FBS_LOGO.png") #this is the location on my computer ~ see how to guide for extra notes
    logo = logo.resize((200, 200), Image.Resampling.LANCZOS) # This makes the image clearer using the Pillow Library
    logo_tk = ImageTk.PhotoImage(logo)
    logo_label = tk.Label(button_frame, image=logo_tk, bg='#58B6C0') #places the logo in the button area of the frame
    logo_label.image = logo_tk
    logo_label.pack(pady=(0, 10)) #places the image
except Exception as e:
    print(f"Error loading logo: {e}") # This was just for me to figure out what the issues were

# Places the plot on the right side of the frame
plot_frame = tk.Frame(frame)
plot_frame.pack(side=RIGHT, padx=20, pady=10, fill=BOTH, expand=True)

# Matplotlib figure size
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111) # This indicates a single value on x-axis and single value on y-axis

canvas = FigureCanvasTkAgg(fig, master=plot_frame) # This creates the "canvas" or area for the graph
canvas.get_tk_widget().pack(fill=BOTH, expand=True)

# Connecting to arduino
def connect_arduino(): 
    global ser
    PORT = '/dev/cu.usbserial-0001' # This can be found in board manager drop down menu
    BAUD = 9600 # must match baud rate in arduino

    try: #tests connection to arduino
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        status_label.config(text="Connected to Arduino")
        return True
    except Exception as e:
        error_msg = f"Connection error: {e}"
        status_label.config(text=error_msg)
        messagebox.showerror("Connection Error", error_msg)
        return False

def prompt_restart(): 
    if messagebox.askyesno("New Session", "Would you like to start a new session?"): # This opens a new popup that will have yes and no buttons
        if ser and ser.is_open: # depending on which button you click, a command will be sent back to the arduino
            ser.write(b'y')
    else:
        if ser and ser.is_open:
            ser.write(b'n')

def animate(i, dataList, timeList): # This animates the graph to expand and format as data collection is occuring
    global startTime, ser, real_time_value

    if ser and ser.is_open and ser.in_waiting > 0: # This triggers the graph to start recording when the serial numbers are above 0
        try:
            data_string = ser.readline().decode('ascii').strip()  # reads values from arduino
            print(f"Raw data: '{data_string}'") 

            if "Would you like to start a new session" in data_string:
                root.after(100, prompt_restart)
                return

            try:
                data_float = float(data_string) # assigns float to the data collected from arduino
                print(f"Got value: {data_float}")

                real_time_value = data_float # This is the button for displaying the real time values to the left of the graph
                real_time_label.config(text=f"Skin Conductance: {real_time_value:.2f} µS") 

                current_time = time.time() # same idea as sensor values
                if startTime is None:
                    startTime = current_time
                    print("Starting timer reference")

                elapsed_time = (current_time - startTime) * 1000 #converts seconds to ms

                dataList.append(data_float) # append adds the item to the end of the list (updates the real time skin conductance values)
                timeList.append(elapsed_time)

                print(f"Added point: time={elapsed_time:.1f}ms, value={data_float}")

                if len(dataList) > 600: # This clears the data list if its over 600 values to save storage
                    dataList.pop(0)
                    timeList.pop(0)

            except ValueError:
                if len(data_string) > 0:
                    print(f"Message: {data_string}")

        except Exception as e:
            print(f"Error reading data: {e}")

   # These are the labels for the graph
    ax.clear()
    ax.set_ylim(0, 12)
    ax.set_title("Resonance Skin Conductance", font='Helvetica')
    ax.set_ylabel("Skin Conductance (µS)", font='Helvetica')
    ax.set_xlabel("Time (ms)", font='Helvetica')

    if len(timeList) > 1: 
        min_time = min(timeList)
        max_time = max(timeList)
        range_time = max_time - min_time

        if range_time < 10000: # This is what expands the graph x-axis over time
            ax.set_xlim(min_time, min_time + 10000) 
        else:
            ax.set_xlim(min_time, max_time + 1000)
    else:
        ax.set_xlim(0, 120000) # stops expanding at 2 minutes

    if len(timeList) > 0 and len(dataList) > 0:
        ax.plot(timeList, dataList, 'b-') # plotting parameters

    canvas.draw() # animation updates in real time

def start_recording(): # this is the start button
    global startTime, ser, ani, filename

    dataList.clear()
    timeList.clear()
    startTime = None

    if not ser or not ser.is_open:
        if not connect_arduino():
            return

    filename = simpledialog.askstring("Name File", "Enter File Name") #pop up window to name the file
    if not filename:
        status_label.config(text="Recording cancelled - no filename") # If nothing is typed into the message box, it returns this
        return

    filename_label.config(text=f"Recording filename: {filename}") # displays the file name

    try: # sends start command and file name back to arduino
        ser.reset_input_buffer()
        status_label.config(text="Starting recording...")
        ser.write(b's\n')
        time.sleep(0.5)
        ser.write(f"{filename}\n".encode('ascii'))
        status_label.config(text="Recording started")

    except Exception as e:
        error_msg = f"Error starting recording: {e}"
        status_label.config(text=error_msg)
        messagebox.showerror("Error", error_msg)

# Start Recording button
start_button = tk.Button(button_frame, text="Start Recording", command=start_recording,
                         padx=10, pady=5, bg='white', fg='black', font=("Helvetica", 10))
start_button.pack(pady=20)

# White box for file name to make it stand out
filename_box = tk.Frame(button_frame, bg='white', bd=2, relief="solid")
filename_box.pack(pady=10, fill=X)
filename_label = tk.Label(filename_box, text="Recording filename: None", font=("Helvetica", 10),
                          bg='white', fg='black', padx=10, pady=5)
filename_label.pack()

# White box for real-time measurement to also make it stand out
realtime_box = tk.Frame(button_frame, bg='white', bd=2, relief="solid")
realtime_box.pack(pady=10, fill=X)
real_time_label = tk.Label(realtime_box, text="Skin Conductance: 0.00 µS", font=("Helvetica", 12),
                           bg='white', fg='black', padx=10, pady=5)
real_time_label.pack()

# Start the animation
ani = animation.FuncAnimation(fig, animate, frames=100, fargs=(dataList, timeList), interval=100)

# Try to connect at startup
connect_arduino()

# Run the main loop
root.mainloop()
