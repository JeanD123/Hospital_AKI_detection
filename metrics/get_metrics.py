import re
import plotly.express as px
from datetime import datetime
import pandas as pd

with open('metrics_log.txt', 'r') as file:
    metrics_data = file.read()

entries = re.split(r'Timestamp: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', metrics_data)[1:]

timestamps = []
metrics_values = {metric: [] for metric in [
    'process_cpu_seconds_total',
    'process_virtual_memory_bytes',
    'total_number_of_messages_received_total',
    'MLP_socket_reconnections_counter_total',
    'total_number_of_results_received_total',
    'admitted_number_of_patients_total',
    'discharged_number_of_patients_total',
    'flagged_results_total',
    'http_errors_metric_total',
    'positive_rate_prediction',
    'running_latency_mean',
    'median_creatine_result',
    'number_of_warnings_total',
    'number_of_exits_total',
    'number_of_errors_total',
]}

for i in range(0, len(entries), 2):
    timestamp_str = entries[i].strip()
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    timestamps.append(timestamp)

    metrics_entry = entries[i + 1]
    for metric in metrics_values:
        match = re.search(fr'{metric} (\d+(\.\d+)?)', metrics_entry)
        value = float(match.group(1)) if match else None
        metrics_values[metric].append(value)

df = pd.DataFrame({'Timestamp': timestamps})
df = df.set_index('Timestamp')

for metric, values in metrics_values.items():
    df[metric] = values

fig = px.line(df, x=df.index, y=df.columns, title='Manrique metrics')
fig.update_xaxes(title_text='Timestamp')
fig.update_yaxes(title_text='Metric Value')

fig.show()
