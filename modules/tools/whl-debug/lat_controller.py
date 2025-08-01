import re
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# --- Log Parsing Logic (Revised for Robustness) ---


def parse_steer_control_detail_line(line):
    """
    Parse a log line containing 'Steer_Control_Detail'.
    Extracts timestamp and comma-separated data.
    This version is more robust to potential leading/trailing whitespace.
    """
    # This pattern is more robust, looking for the keyword and capturing everything after it.
    match = re.search(
        r"([IWEF]\d{8}\s+\d{2}:\d{2}:\d{2}\.\d{6}).*?Steer_Control_Detail:\s*(.*)", line
    )
    if match:
        timestamp_part = match.group(1)
        data_str = match.group(2).strip()

        try:
            # Handle potential C++ scientific notation if needed, though float() usually handles 'e'
            dt_object = datetime.strptime(timestamp_part, "I%Y%m%d %H:%M:%S.%f")
            data_values = [float(x.strip()) for x in data_str.split(",")]
            return dt_object, data_values
        except (ValueError, IndexError):
            # Could log a warning here if parsing fails for a matched line
            return None, None

    return None, None


def load_and_filter_steer_data(log_file_path, start_time=None, end_time=None):
    """
    Load steering control debug data from log file and filter by time range.
    The column names are now correctly matched to the C++ log string.
    """
    data = []

    # --- CRITICAL: Column names must exactly match the C++ log string order ---
    column_names = [
        "lateral_error",  # 0
        "lateral_error_rate",  # 1
        "lateral_error_feedback",  # 2
        "heading",  # 3
        "ref_heading",  # 4
        "heading_error",  # 5
        "heading_error_rate",  # 6
        "heading_error_feedback",  # 7
        "curvature",  # 8
        "steer_angle",  # 9
        "steer_angle_feedforward",  # 10
        "steer_angle_feedback",  # 11
        "steer_angle_feedback_augment",  # 12
        "steering_percentage",  # 13
        "steer_angle_lateral_contribution",  # 14
        "steer_angle_lateral_rate_contribution",  # 15
        "steer_angle_heading_contribution",  # 16
        "steer_angle_heading_rate_contribution",  # 17
        "linear_velocity",  # 18
    ]

    expected_columns = len(column_names)

    with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, 1):
            dt, values = parse_steer_control_detail_line(line)
            if dt and values:
                if len(values) == expected_columns:
                    row_data = {"timestamp": dt}
                    row_data.update(zip(column_names, values))
                    if (start_time is None or dt >= start_time) and (
                        end_time is None or dt <= end_time
                    ):
                        data.append(row_data)
                # else:
                #     # This warning is useful for initial debugging of the C++ log output
                #     print(f"Warning: Line {line_num} has {len(values)} values, expected {expected_columns}. Data: '{values}'. Skipping.")

    if not data:
        print("Warning: No valid steer control data found in the log file.")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    return df


# --- Plotting Logic (Revised for Expert Analysis) ---


def plot_lqr_performance(
    df, title="LQR Control Performance Analysis", save_path=None, x_min=None, x_max=None
):
    """
    Plot multi-subplot time series of LQR control data, structured for expert analysis.
    This function separates state variables, control composition, and individual contributions.
    """
    if df.empty:
        print("No data to plot.")
        return

    plt.style.use("seaborn-v0_8-whitegrid")  # A professional and clean plot style
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.labelsize": 10,
            "axes.titlesize": 12,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "figure.titlesize": 16,
            "lines.linewidth": 1.5,
            "lines.markersize": 3,
        }
    )

    fig, axes = plt.subplots(nrows=5, ncols=1, figsize=(18, 22), sharex=True)
    fig.suptitle(title, fontsize=18, y=0.98)

    # --- Plot 1: System State & Errors ---
    # Goal: See the "what". What is the vehicle's state relative to the reference?
    ax = axes[0]
    # Create a second y-axis for velocity and curvature to see context
    ax.set_title("1. Velocity & Curvature Context")
    ax.plot(
        df["timestamp"],
        df["linear_velocity"],
        label="Velocity (m/s)",
        color="g",
        linestyle="--",
        alpha=0.7,
    )
    ax.set_ylabel("Velocity (m/s)", color="g")
    ax.tick_params(axis="y", labelcolor="g")
    ax.legend(loc="upper left")

    # 右Y轴 - 曲率
    ax2 = ax.twinx()
    ax2.plot(
        df["timestamp"],
        df["curvature"],
        label="Ref. Curvature (1/m)",
        color="purple",
        linestyle=":",
        alpha=0.7,
    )
    ax2.set_ylabel("Context (m/s, 1/m)")
    ax2.legend(loc="upper right")

    # --- Plot 2: Control Command Composition ---
    # Goal: See the "how". How was the final command constructed?
    ax = axes[1]
    ax.plot(
        df["timestamp"],
        df["steer_angle"],
        label="steer_angle(%)",
        color="black",
        linewidth=2.5,
    )
    ax.plot(
        df["timestamp"],
        df["steer_angle_feedforward"],
        label="steer_angle_feedforward",
        color="c",
        linestyle="-",
    )
    ax.plot(
        df["timestamp"],
        df["steer_angle_feedback"],
        label="steer_angle_feedback",
        color="m",
        linestyle="-",
    )
    ax.plot(
        df["timestamp"],
        df["steer_angle_feedback_augment"],
        label="steer_angle_feedback_augment",
        color="orange",
        linestyle="-",
    )
    ax.plot(
        df["timestamp"],
        df["steering_percentage"],
        label="chassis steering_percentage(%)",
        color="gray",
        linestyle="--",
        alpha=0.8,
    )
    ax.set_ylabel("Steering Command (%)")
    ax.set_title("2. Control Command Composition & Actual")
    ax.legend()
    ax.axhline(0, color="k", linestyle=":", linewidth=0.5)  # Zero line for reference

    # --- Plot 3: LQR Feedback Breakdown (Individual Contributions) ---
    # Goal: See the "why". Why did the LQR feedback term have that value?
    ax = axes[2]
    ax.plot(
        df["timestamp"],
        df["steer_angle_lateral_contribution"],
        label="steer_angle_lateral_contribution",
    )
    ax.plot(
        df["timestamp"],
        df["steer_angle_lateral_rate_contribution"],
        label="steer_angle_lateral_rate_contribution",
    )
    ax.plot(
        df["timestamp"],
        df["steer_angle_heading_contribution"],
        label="steer_angle_heading_contribution",
    )
    ax.plot(
        df["timestamp"],
        df["steer_angle_heading_rate_contribution"],
        label="steer_angle_heading_rate_contribution",
    )
    # A "reconstructed" feedback can validate logging. It should match steer_angle_feedback.
    ax.set_ylabel("Steering Contribution (%)")
    ax.set_title("3. LQR Feedback Breakdown")
    ax.legend()

    # --- Plot 4: System State Error Rates ---
    # Goal: See damping and predictive behavior. Are we effectively controlling the rates?
    ax = axes[3]
    ax.plot(
        df["timestamp"],
        df["lateral_error"],
        label="Lateral Error (m)",
        color="r",
        linewidth=2,
    )
    ax.plot(
        df["timestamp"],
        df["lateral_error_feedback"],
        label="Lateral Error Feedback (m)",
        color="purple",
        linestyle="--",
        linewidth=2,
    )
    ax.set_ylabel("Lateral Error (m)", color="r")
    ax.tick_params(axis="y", labelcolor="r")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color="red", linestyle=":", linewidth=0.8, alpha=0.7)

    ax2 = ax.twinx()
    ax2.plot(
        df["timestamp"],
        df["lateral_error_rate"],
        label="Lateral Error Rate (m/s)",
        color="orange",
        linewidth=2,
    )
    ax2.set_ylabel("Lateral Error Rate (m/s)", color="orange")
    ax2.tick_params(axis="y", labelcolor="orange")
    ax2.legend(loc="upper right")
    ax2.axhline(0, color="orange", linestyle=":", linewidth=0.8, alpha=0.7)
    ax.set_title("4. Lateral Control Performance")

    # --- Plot 5: Heading Error Analysis ---
    ax = axes[4]
    ax.plot(
        df["timestamp"],
        df["heading_error"],
        label="Heading Error (rad)",
        color="b",
        linewidth=2,
    )
    ax.plot(
        df["timestamp"],
        df["heading_error_feedback"],
        label="Heading Error Feedback (rad/s)",
        color="cyan",
        linestyle="--",
        linewidth=2,
    )
    ax.set_ylabel("Heading Error (rad)", color="b")
    ax.tick_params(axis="y", labelcolor="b")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)
    ax.axhline(0, color="blue", linestyle=":", linewidth=0.8, alpha=0.7)

    ax2 = ax.twinx()
    ax2.plot(
        df["timestamp"],
        df["heading_error_rate"],
        label="Heading Error Rate (rad/s)",
        color="purple",
        linewidth=2,
    )
    ax2.set_ylabel("Heading Error Rate (rad/s)", color="cyan")
    ax2.tick_params(axis="y", labelcolor="cyan")
    ax2.legend(loc="upper right")
    ax2.axhline(0, color="cyan", linestyle=":", linewidth=0.8, alpha=0.7)
    ax.set_title("5. Heading Control Performance")

    # Formatting for all plots
    for ax in axes:
        ax.grid(True, which="both", linestyle="--", alpha=0.6)
        if x_min or x_max:
            ax.set_xlim(x_min, x_max)

    # Improve date formatting on the x-axis
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S.%f"))
    fig.autofmt_xdate()
    plt.tight_layout(rect=[0, 0.03, 1, 0.96])

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Plot saved to {save_path}")
    else:
        plt.show()


# --- Usage Example ---
if __name__ == "__main__":
    log_file = "control.INFO"  # Make sure this file exists and has the new log format

    # Load all available data
    print("--- Loading and parsing steer control debug data ---")
    all_steer_data = load_and_filter_steer_data(log_file)

    if not all_steer_data.empty:
        print(f"Successfully loaded {len(all_steer_data)} data points.")
        # Plot the entire dataset
        plot_lqr_performance(
            all_steer_data,
            title="Full LQR Performance Analysis",
            # save_path="lqr_full_analysis.png",
        )

        # Example of plotting a specific time window for detailed analysis
        # Let's say we identified an oscillation event around a specific time
        try:
            start_focus_time = pd.to_datetime("2024-06-18 04:38:35.000")
            end_focus_time = pd.to_datetime("2024-06-18 04:38:45.000")

            plot_lqr_performance(
                all_steer_data,
                title=f"LQR Detailed Analysis ({start_focus_time.strftime('%H:%M:%S')} to {end_focus_time.strftime('%H:%M:%S')})",
                x_min=start_focus_time,
                x_max=end_focus_time,
                save_path="lqr_oscillation_analysis.png",
            )
        except Exception as e:
            print(
                f"Could not plot focused time window. Maybe timestamps are different? Error: {e}"
            )
    else:
        print("Execution finished. No data was loaded.")
