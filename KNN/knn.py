import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tkinter as tk
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# Function to load and preprocess a single CSV file
def load_csv(file_path):
    df = pd.read_csv(file_path)  # Read CSV file into a DataFrame
    df["Time"] = pd.to_numeric(df["Time"], errors="coerce")  # Convert 'Time' column to numeric
    df.dropna(subset=["Time", "Length"], inplace=True)  # Remove rows with missing values
    df['Flow_ID'] = df.apply(lambda row: hash(f"{row['Source']}_{row['Destination']}"), axis=1)  # Create Flow ID
    return df[["Flow_ID", "Length", "Time"]]  # Return selected columns without app name

# Function to infer app name from filename
def infer_app_name(file_path):
    file_name = os.path.basename(file_path).lower()
    if "firefox" in file_name:
        return "Firefox"
    elif "google" in file_name:
        return "Google"
    elif "spotify" in file_name:
        return "Spotify"
    elif "youtube" in file_name:
        return "Youtube"
    elif "zoom" in file_name:
        return "Zoom"
    else:
        return None  # Return None instead of "Unknown" to skip unrecognized files

# Function to load all CSV data
def load_all_data():
    csv_folder = "."  # Adjust if needed
    csv_files = [f for f in os.listdir(csv_folder) if f.endswith(".csv")]

    dataframes = []
    labels = []  # Store inferred labels separately

    for file in csv_files:
        app_name = infer_app_name(file)  # Infer app name from filename
        file_path = os.path.join(csv_folder, file)
        if app_name and os.path.exists(file_path):
            df = load_csv(file_path)
            if not df.empty:
                dataframes.append(df)
                labels.extend([app_name] * len(df))  # Labels are stored separately

    return pd.concat(dataframes, ignore_index=True), np.array(labels)  # Ensure labels are a NumPy array

# Load data
data, labels = load_all_data()

# Define feature sets
features_full = ["Flow_ID", "Length", "Time"]
features_limited = ["Length", "Time"]

# Split dataset into training and testing sets (80% train, 20% test)
X_train_full, X_test_full, y_train_full, y_test_full = train_test_split(
    data[features_full], labels, test_size=0.2, random_state=42
)
X_train_limited, X_test_limited, y_train_limited, y_test_limited = train_test_split(
    data[features_limited], labels, test_size=0.2, random_state=42
)

# Normalize features
scaler_full = StandardScaler()
X_train_full = scaler_full.fit_transform(X_train_full)
X_test_full = scaler_full.transform(X_test_full)

scaler_limited = StandardScaler()
X_train_limited = scaler_limited.fit_transform(X_train_limited)
X_test_limited = scaler_limited.transform(X_test_limited)

# Train KNN classifiers
knn_full = KNeighborsClassifier(n_neighbors=5)
knn_full.fit(X_train_full, y_train_full)

knn_limited = KNeighborsClassifier(n_neighbors=5)
knn_limited.fit(X_train_limited, y_train_limited)

# Predictions
y_pred_full = knn_full.predict(X_test_full)
y_pred_limited = knn_limited.predict(X_test_limited)

# Compute accuracy
accuracy_full = accuracy_score(y_test_full, y_pred_full) * 100
accuracy_limited = accuracy_score(y_test_limited, y_pred_limited) * 100

# Print classification reports
print("\nScenario 1 - Full Feature Set:\n", classification_report(y_test_full, y_pred_full))
print("\nScenario 2 - Limited Feature Set:\n", classification_report(y_test_limited, y_pred_limited))

# Save results
results_df = pd.DataFrame({
    "Actual": y_test_full,
    "Predicted_Scenario_1": y_pred_full,
    "Predicted_Scenario_2": y_pred_limited
})
results_df.to_csv("knn_predictions.csv", index=False)

# Function to plot results
def plot_results(actual, predicted, scenario, ax):
    actual_counts = pd.Series(actual).value_counts()
    predicted_counts = pd.Series(predicted).value_counts()
    apps = sorted(set(actual_counts.index).union(predicted_counts.index))
    x = np.arange(len(apps))
    width = 0.35

    ax.bar(x - width / 2, actual_counts.reindex(apps, fill_value=0), width, label="Actual", color='blue')
    ax.bar(x + width / 2, predicted_counts.reindex(apps, fill_value=0), width, label=f"Predicted {scenario}",
           color='orange' if scenario == 1 else 'green')
    ax.set_xticks(x)
    ax.set_xticklabels(apps, rotation=45)
    ax.set_ylabel("Count")
    ax.set_title(f"Scenario {scenario} Prediction Results")
    ax.legend()

# Function to display results in a GUI
def display_results():
    root = tk.Tk()
    root.title("KNN Prediction Results")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    plot_results(y_test_full, y_pred_full, 1, axes[0])
    plot_results(y_test_limited, y_pred_limited, 2, axes[1])

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack()

    accuracy_label = tk.Label(root,
                              text=f"Scenario 1 Accuracy: {accuracy_full:.2f}%\nScenario 2 Accuracy: {accuracy_limited:.2f}%",
                              font=("Arial", 12))
    accuracy_label.pack()

    root.mainloop()

display_results()
