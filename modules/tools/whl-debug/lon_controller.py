import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


csv_path = "speed_log__2025-08-14_163603.csv"  # Path to your CSV file

COLUMN_NAMES = [
    "station_reference",
    "station_error",
    "station_error_limited",
    "preview_station_error",
    "speed_reference",
    "speed_error",
    "desired_speed_cmd",
    "preview_speed_reference",
    "preview_speed_error",
    "preview_acceleration_reference",
    "acceleration_cmd_closeloop",
    "acceleration_cmd",
    "acceleration_lookup",
    "acceleration_lookup_limit",
    "speed_lookup",
    "calibration_value",
    "brake_cmd",
    "is_full_stop",
]

try:
    df = pd.read_csv(csv_path, header=None, names=COLUMN_NAMES)
except FileNotFoundError:
    print(
        "Error: Please replace the 'data' variable with your CSV filename, e.g. 'log.csv'"
    )
    exit()

for col in COLUMN_NAMES:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Add time axis (assuming log frequency is 10Hz, i.e. 0.1s per entry)
df["time"] = np.arange(len(df)) * 0.1

# Derived data calculation
# Assume a simple position loop output, should be obtained from log in practice
KP_STATION = 0.2  # Assumed position loop P-gain
df["speed_offset"] = KP_STATION * df["station_error"]

# Handle potential NaN propagation gracefully by filling with 0 for offset, as a safe default
df["speed_offset"] = df["speed_offset"].fillna(0.0)

df["dynamic_target_speed"] = df["speed_reference"] + df["speed_offset"]
df["speed_pid_input"] = df["speed_offset"] + df["speed_error"]

# --- 3. Plotting Functions ---

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def plot_all(df_data):
    """Plot all charts in one figure with subplots"""
    fig, axs = plt.subplots(3, 1, figsize=(15, 20))

    # Chart 1: Dynamic Speed Tracking
    axs[0].plot(
        df_data["time"],
        df_data["speed_reference"],
        "g--",
        label="Speed Reference (speed_reference)",
    )
    axs[0].plot(
        df_data["time"],
        df_data["dynamic_target_speed"],
        "r-",
        label="Dynamic Target Speed (dynamic_target_speed)",
        linewidth=2,
    )
    axs[0].plot(
        df_data["time"],
        df_data["speed_lookup"],
        "b-",
        label="Actual Vehicle Speed (speed_lookup)",
        alpha=0.8,
    )
    axs[0].set_title("Chart 1: Dynamic Speed Tracking", fontsize=16)
    axs[0].set_xlabel("Time (s)", fontsize=12)
    axs[0].set_ylabel("Speed (m/s)", fontsize=12)
    axs[0].legend(fontsize=12)
    axs[0].grid(True, which="both", linestyle="--", linewidth=0.5)

    # Chart 2: Acceleration Command Deconstruction
    axs[1].plot(
        df_data["time"],
        df_data["acceleration_cmd"],
        "r-",
        label="Final Acceleration Command (acceleration_cmd)",
        linewidth=2.5,
    )
    axs[1].plot(
        df_data["time"],
        df_data["preview_acceleration_reference"],
        "g--",
        label="Feedforward Acceleration",
        linewidth=2,
    )
    axs[1].plot(
        df_data["time"],
        df_data["acceleration_cmd_closeloop"],
        "b-",
        label="Feedback PID Correction",
        alpha=0.8,
    )
    axs[1].axhline(
        0, color="black", linestyle="-.", linewidth=1, label="Feedback Zero Axis"
    )
    axs[1].set_title(
        "Chart 2: Acceleration Command Deconstruction (Feedforward vs Feedback)",
        fontsize=16,
    )
    axs[1].set_xlabel("Time (s)", fontsize=12)
    axs[1].set_ylabel("Acceleration ($m/s^2$)", fontsize=12)
    axs[1].legend(fontsize=12)
    axs[1].grid(True, which="both", linestyle="--", linewidth=0.5)

    # Chart 3: Controller Input Status
    ax3 = axs[2]
    ax3_2 = ax3.twinx()
    # Left Y-axis (speed related)
    ax3.set_xlabel("Time (s)", fontsize=12)
    ax3.set_ylabel("Speed/Compensation (m/s)", color="b", fontsize=12)
    ax3.plot(
        df_data["time"],
        df_data["speed_pid_input"],
        "b-",
        label="Speed PID Total Input (speed_pid_input)",
    )
    ax3.plot(
        df_data["time"],
        df_data["speed_offset"],
        "c--",
        label="Position Loop Compensation (speed_offset)",
    )
    ax3.tick_params(axis="y", labelcolor="b")
    ax3.grid(True, which="both", linestyle="--", linewidth=0.5)
    # Right Y-axis (position related)
    ax3_2.set_ylabel("Position Error (m)", color="g", fontsize=12)
    ax3_2.plot(
        df_data["time"],
        df_data["station_error"],
        "g-",
        label="Position Error (station_error)",
        alpha=0.6,
    )
    ax3_2.tick_params(axis="y", labelcolor="g")
    # Combine legends
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_2.get_legend_handles_labels()
    ax3_2.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=12)
    ax3.set_title("Chart 3: Controller Input Status", fontsize=16)
    fig.tight_layout(rect=[0, 0.03, 1, 0.97])


if __name__ == "__main__":
    plot_all(df)
    plt.show()
