import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load CSVs
time_df = pd.read_csv("record_time.csv")

# Clean column names
time_df.columns = time_df.columns.str.strip()

# Calculate booting up time
time_df["Booting Up Time (s)"] = time_df["Total Time (s)"] - (time_df["Build Time (s)"] + time_df["Chunking Time (s)"] + time_df["Search Time (s)"])

# Create subplots
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# === PLOT 1: Search Times vs Total Characters ===
ax1 = axes[0]
x_search = time_df["Total Characters"]
y_init = time_df["Search Time (s)"]

# Sort x for plotting quadratic and log fits
x_search_sorted = np.sort(x_search)

# Function to fit logarithmic model y = a*log(x) + b
def log_fit(x, y):
    log_x = np.log(x)
    z = np.polyfit(log_x, y, 1)
    p = np.poly1d(z)
    return z, p

# Initial search times
ax1.scatter(x_search, y_init, label="Initial Search Time", color="blue")
# Linear fit
z1_lin = np.polyfit(x_search, y_init, 1)
p1_lin = np.poly1d(z1_lin)
ax1.plot(x_search, p1_lin(x_search), "b--", label=f"Linear Fit: Init\n(y={z1_lin[0]:.4e}x + {z1_lin[1]:.4f})")
# Logarithmic fit
z1_log, p1_log = log_fit(x_search, y_init)
ax1.plot(x_search_sorted, p1_log(np.log(x_search_sorted)), "b-.", label=f"Log Fit: Init\n(y={z1_log[0]:.4e}ln(x) + {z1_log[1]:.4f})")

ax1.set_title("Search Time vs Total Characters")
ax1.set_xlabel("Total Characters")
ax1.set_ylabel("Search Time (s)")
ax1.legend(fontsize='small')
ax1.grid(True)

# === PLOT 2: Build Times vs Total Characters ===
ax2 = axes[1]
x_build = time_df["Total Characters"]
x_build_sorted = np.sort(x_build)
colors = {
    "Chunking Time (s)": "orange",
    "Build Time (s)": "red",
    "Total Time (s)": "purple",
    "Booting Up Time (s)": "brown"
}

for col, color in colors.items():
    y = time_df[col]
    ax2.scatter(x_build, y, label=col, color=color)
    # Linear
    z_lin = np.polyfit(x_build, y, 1)
    p_lin = np.poly1d(z_lin)
    ax2.plot(x_build, p_lin(x_build), linestyle="--", color=color, label=f"Linear Fit: {col}\n(y={z_lin[0]:.4e}x + {z_lin[1]:.4f})")
    # Logarithmic
    z_log, p_log = log_fit(x_build, y)
    ax2.plot(x_build_sorted, p_log(np.log(x_build_sorted)), linestyle="-.", color=color,
             label=f"Log Fit: {col}\n(y={z_log[0]:.4e}ln(x) + {z_log[1]:.4f})")

ax2.set_title("Build Time vs Total Characters (including Booting Up Time)")
ax2.set_xlabel("Total Characters")
ax2.set_ylabel("Time (s)")
ax2.legend(loc='upper left', fontsize='small')
ax2.grid(True)

plt.tight_layout()
plt.show()
