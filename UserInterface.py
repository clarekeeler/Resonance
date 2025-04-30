from tkinter import *
import time
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import tkinter as tk
from tkinter import simpledialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk

# Global variables
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
root.config(bg='#58B6C0')
root.geometry("2000x2000")

# Create a status label
status_label = tk.Label(root, text="Not connected", bg='#58B6C0', font=("Helvetica", 12))
status_label.pack(pady=10)

# Create a main frame to split buttons and plot
frame = tk.Frame(root, bg='#58B6C0')
frame.pack(fill=BOTH, expand=True)

# Left frame for buttons
button_frame = tk.Frame(frame, bg='#58B6C0')
button_frame.pack(side=LEFT, padx=20, pady=10)

# Load the image and place it at the top of button_frame
try:
    logo = Image.open("/Users/clarekeeler/Desktop/tkinter_vscode/FBS_LOGO.png")
    logo = logo.resize((200, 200), Image.Resampling.LANCZOS)
    logo_tk = ImageTk.PhotoImage(logo)
    logo_label = tk.Label(button_frame, image=logo_tk, bg='#58B6C0')
    logo_label.image = logo_tk
    logo_label.pack(pady=(0, 10))
except Exception as e:
    print(f"Error loading logo: {e}")

# Right frame for matplotlib plot
plot_frame = tk.Frame(frame)
plot_frame.pack(side=RIGHT, padx=20, pady=10, fill=BOTH, expand=True)

# Matplotlib figure
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111)

canvas = FigureCanvasTkAgg(fig, master=plot_frame)
canvas.get_tk_widget().pack(fill=BOTH, expand=True)

def connect_arduino():
    global ser
    PORT = '/dev/cu.usbserial-0001'
    BAUD = 9600

    try:
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
    if messagebox.askyesno("New Session", "Would you like to start a new session?"):
        if ser and ser.is_open:
            ser.write(b'y')
    else:
        if ser and ser.is_open:
            ser.write(b'n')

def animate(i, dataList, timeList):
    global startTime, ser, real_time_value

    if ser and ser.is_open and ser.in_waiting > 0:
        try:
            data_string = ser.readline().decode('ascii').strip()
            print(f"Raw data: '{data_string}'")

            if "Would you like to start a new session" in data_string:
                root.after(100, prompt_restart)
                return

            try:
                data_float = float(data_string)
                print(f"Got value: {data_float}")

                real_time_value = data_float
                real_time_label.config(text=f"Skin Conductance: {real_time_value:.2f} µS")

                current_time = time.time()
                if startTime is None:
                    startTime = current_time
                    print("Starting timer reference")

                elapsed_time = (current_time - startTime) * 1000

                dataList.append(data_float)
                timeList.append(elapsed_time)

                print(f"Added point: time={elapsed_time:.1f}ms, value={data_float}")

                if len(dataList) > 600:
                    dataList.pop(0)
                    timeList.pop(0)

            except ValueError:
                if len(data_string) > 0:
                    print(f"Message: {data_string}")

        except Exception as e:
            print(f"Error reading data: {e}")

    ax.clear()
    ax.set_ylim(0, 12)
    ax.set_title("Resonance Skin Conductance", font='Helvetica')
    ax.set_ylabel("Skin Conductance (µS)", font='Helvetica')
    ax.set_xlabel("Time (ms)", font='Helvetica')

    if len(timeList) > 1:
        min_time = min(timeList)
        max_time = max(timeList)
        range_time = max_time - min_time

        if range_time < 10000:
            ax.set_xlim(min_time, min_time + 10000)
        else:
            ax.set_xlim(min_time, max_time + 1000)
    else:
        ax.set_xlim(0, 120000)

    if len(timeList) > 0 and len(dataList) > 0:
        ax.plot(timeList, dataList, 'b-')

    canvas.draw()

def start_recording():
    global startTime, ser, ani, filename

    dataList.clear()
    timeList.clear()
    startTime = None

    if not ser or not ser.is_open:
        if not connect_arduino():
            return

    filename = simpledialog.askstring("Name File", "Enter File Name")
    if not filename:
        status_label.config(text="Recording cancelled - no filename")
        return

    filename_label.config(text=f"Recording filename: {filename}")

    try:
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

# White box for filename
filename_box = tk.Frame(button_frame, bg='white', bd=2, relief="solid")
filename_box.pack(pady=10, fill=X)
filename_label = tk.Label(filename_box, text="Recording filename: None", font=("Helvetica", 10),
                          bg='white', fg='black', padx=10, pady=5)
filename_label.pack()

# White box for real-time measurement
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

