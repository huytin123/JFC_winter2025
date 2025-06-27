import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load CSVs
search_df = pd.read_csv("record_search.csv")
build_df = pd.read_csv("build_times.csv")

# Clean column names
search_df.columns = search_df.columns.str.strip()
build_df.columns = build_df.columns.str.strip()

# Calculate booting up time
build_df["Booting Up Time (s)"] = build_df["Total Time (s)"] - (build_df["Build Time (s)"] + build_df["Chunking Time (s)"])

# Create subplots
fig, axes = plt.subplots(1, 2, figsize=(18, 7))

# === PLOT 1: Search Times vs Total Characters ===
ax1 = axes[0]
x_search = search_df["Total Characters"]
y_init = search_df["initalsearchingtime"]
y_other = search_df["othersearchingtime"]

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
# Quadratic fit
z1_quad = np.polyfit(x_search, y_init, 2)
p1_quad = np.poly1d(z1_quad)
ax1.plot(x_search_sorted, p1_quad(x_search_sorted), "b:", label=f"Quadratic Fit: Init\n(y={z1_quad[0]:.2e}x² + {z1_quad[1]:.2e}x + {z1_quad[2]:.2f})")
# Logarithmic fit
z1_log, p1_log = log_fit(x_search, y_init)
ax1.plot(x_search_sorted, p1_log(np.log(x_search_sorted)), "b-.", label=f"Log Fit: Init\n(y={z1_log[0]:.4e}ln(x) + {z1_log[1]:.4f})")

# Other search times
ax1.scatter(x_search, y_other, label="Other Search Time", color="green")
# Linear
z2_lin = np.polyfit(x_search, y_other, 1)
p2_lin = np.poly1d(z2_lin)
ax1.plot(x_search, p2_lin(x_search), "g--", label=f"Linear Fit: Other\n(y={z2_lin[0]:.4e}x + {z2_lin[1]:.4f})")
# Quadratic
z2_quad = np.polyfit(x_search, y_other, 2)
p2_quad = np.poly1d(z2_quad)
ax1.plot(x_search_sorted, p2_quad(x_search_sorted), "g:", label=f"Quadratic Fit: Other\n(y={z2_quad[0]:.2e}x² + {z2_quad[1]:.2e}x + {z2_quad[2]:.2f})")
# Logarithmic
z2_log, p2_log = log_fit(x_search, y_other)
ax1.plot(x_search_sorted, p2_log(np.log(x_search_sorted)), "g-.", label=f"Log Fit: Other\n(y={z2_log[0]:.4e}ln(x) + {z2_log[1]:.4f})")

ax1.set_title("Search Time vs Total Characters")
ax1.set_xlabel("Total Characters")
ax1.set_ylabel("Search Time (s)")
ax1.legend(fontsize='small')
ax1.grid(True)

# === PLOT 2: Build Times vs Total Characters ===
ax2 = axes[1]
x_build = build_df["Total Characters"]
x_build_sorted = np.sort(x_build)
colors = {
    "Chunking Time (s)": "orange",
    "Build Time (s)": "red",
    "Total Time (s)": "purple",
    "Booting Up Time (s)": "brown"
}

for col, color in colors.items():
    y = build_df[col]
    ax2.scatter(x_build, y, label=col, color=color)
    # Linear
    z_lin = np.polyfit(x_build, y, 1)
    p_lin = np.poly1d(z_lin)
    ax2.plot(x_build, p_lin(x_build), linestyle="--", color=color, label=f"Linear Fit: {col}\n(y={z_lin[0]:.4e}x + {z_lin[1]:.4f})")
    # Quadratic
    z_quad = np.polyfit(x_build, y, 2)
    p_quad = np.poly1d(z_quad)
    ax2.plot(x_build_sorted, p_quad(x_build_sorted), linestyle=":", color=color,
             label=f"Quadratic Fit: {col}\n(y={z_quad[0]:.2e}x² + {z_quad[1]:.2e}x + {z_quad[2]:.2f})")
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
