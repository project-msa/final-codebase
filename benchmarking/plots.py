import json
import os
import matplotlib.pyplot as plt
import numpy as np

# Results paths
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
CSV_DIR = os.path.join(RESULTS_DIR, "csv")
IMAGES_DIR = os.path.join(RESULTS_DIR, "images")

# Load benchmark results
with open(os.path.join(CSV_DIR, 'benchmark_results.json'), 'r') as f:
    results = json.load(f)

def create_bar_plot(metric, title, ylabel, log_scale=False, data=None):
    if data is None:
        data = results
    algorithms = list(data.keys())
    values = [data[alg][metric] for alg in algorithms]
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(algorithms, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45, ha='right')
    
    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.2f}',
                ha='center', va='bottom')
    
    if log_scale:
        plt.yscale('log')
    
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, f'{metric}.png'))
    plt.close()

# Generate plots for different metrics
metrics_to_plot = [
    ('keygen_time_ms', 'Key Generation Time', 'Time (ms)', True),
    ('sign_time_ms', 'Signature Generation Time', 'Time (ms)', True),
    ('verify_time_ms', 'Signature Verification Time', 'Time (ms)', True),
    ('signature_size_bytes', 'Signature Size', 'Size (bytes)', True),
    ('dkim_record_size_bytes', 'DKIM Record Size', 'Size (bytes)', True),
    ('throughput_sig_per_sec', 'Signature Throughput', 'Signatures/second', False),
    ('cpu_percent', 'CPU Usage', 'CPU %', False),
    ('ram_usage_kb', 'RAM Usage', 'KB', True),
    ('keygen_memory_mb', 'Key Generation Memory Usage', 'MB', True)
]

# Create individual plots
for metric, title, ylabel, log_scale in metrics_to_plot:
    create_bar_plot(metric, title, ylabel, log_scale)

# Create a summary plot
plt.figure(figsize=(15, 10))

metrics_normalized = {}
for metric in ['sign_time_ms', 'verify_time_ms', 'signature_size_bytes', 'cpu_percent']:
    values = np.array([results[alg][metric] for alg in results.keys()])
    metrics_normalized[metric] = values / np.max(values)  # Normalize to [0,1]

width = 0.2
x = np.arange(len(results))

# Plot normalized metrics side by side
for i, (metric, values) in enumerate(metrics_normalized.items()):
    plt.bar(x + i*width, values, width, label=metric)

plt.xlabel('Algorithms')
plt.ylabel('Normalized Values')
plt.title('Comparative Performance Summary')
plt.xticks(x + width*1.5, results.keys(), rotation=45, ha='right')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, 'performance_summary.png'))
plt.close()

# Plot email test results if available
try:
    with open(os.path.join(CSV_DIR, 'email_test_results.json'), 'r') as f:
        email_results = json.load(f)
        
    email_metrics = [
        ('avg_dkim_signature_time_ms', 'Average DKIM Signature Time', 'Time (ms)', True),
        ('avg_email_send_time_ms', 'Average Email Send Time', 'Time (ms)', True),
        ('success_rate', 'Email Delivery Success Rate', '%', False)
    ]
    
    for metric, title, ylabel, log_scale in email_metrics:
        create_bar_plot(metric, title, ylabel, log_scale, email_results)
        
    # Create email performance summary
    plt.figure(figsize=(15, 10))
    metrics_normalized = {}
    for metric in ['avg_dkim_signature_time_ms', 'avg_email_send_time_ms', 'success_rate']:
        values = np.array([email_results[alg][metric] for alg in email_results.keys()])
        metrics_normalized[metric] = values / np.max(values)  # Normalize to [0,1]
    
    for i, (metric, values) in enumerate(metrics_normalized.items()):
        plt.bar(x + i*width, values, width, label=metric)

    plt.xlabel('Algorithms')
    plt.ylabel('Normalized Values')
    plt.title('Email Delivery Performance Summary')
    plt.xticks(x + width*1.5, email_results.keys(), rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, 'email_performance_summary.png'))
    plt.close()
        
except FileNotFoundError:
    print("No email test results found")

print("Generated plots have been saved as PNG files")