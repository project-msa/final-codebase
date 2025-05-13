import sys, os, timeit, psutil
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from colorama import init, Fore, Style
from typing import Dict, List, Tuple
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import rsa_sha256, dilithium, ecdsa_sha256, ed25519_sha256
from multiprocessing import freeze_support

# Initialize colorama
init()

# Constants
NUM_KEYGEN_ITERATIONS = 50
NUM_SIGN_ITERATIONS = 1000
TEST_MESSAGE = b"Benchmarking signature algorithms"

# Result paths
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
CSV_DIR = os.path.join(RESULTS_DIR, "csv")
IMAGES_DIR = os.path.join(RESULTS_DIR, "images")

def collect_metrics(name: str, signer_class, security_level=None) -> Dict:
    print(f"\n{Fore.CYAN}Benchmarking {name}...{Style.RESET_ALL}")
    metrics = {
        'algorithm': name,
        'keygen_times': [],
        'sign_times': [],
        'signature_sizes': [],
        'memory_usage': []
    }
    
    # Initialize signer
    signer = signer_class(security_level=security_level) if security_level else signer_class()
    
    # Collect key generation metrics
    print(f"{Fore.YELLOW}Running {NUM_KEYGEN_ITERATIONS} key generation iterations...{Style.RESET_ALL}")
    for _ in range(NUM_KEYGEN_ITERATIONS):
        start_time = timeit.default_timer()
        private_key, public_key = signer.generate_keys()
        metrics['keygen_times'].append((timeit.default_timer() - start_time) * 1000)
        
        process = psutil.Process()
        metrics['memory_usage'].append(process.memory_info().rss / (1024 * 1024))
    
    # Collect signing metrics
    print(f"{Fore.YELLOW}Running {NUM_SIGN_ITERATIONS} signing iterations...{Style.RESET_ALL}")
    for _ in range(NUM_SIGN_ITERATIONS):
        start = timeit.default_timer()
        signature = signer.sign(TEST_MESSAGE)
        metrics['sign_times'].append((timeit.default_timer() - start) * 1000)
        metrics['signature_sizes'].append(len(signature))
    
    # Calculate statistics
    stats = {
        'keygen_mean_ms': np.mean(metrics['keygen_times']),
        'keygen_std_ms': np.std(metrics['keygen_times']),
        'sign_mean_ms': np.mean(metrics['sign_times']),
        'sign_std_ms': np.std(metrics['sign_times']),
        'signature_size_mean_bytes': np.mean(metrics['signature_sizes']),
        'memory_mean_mb': np.mean(metrics['memory_usage'])
    }
    
    print(f"\n{Fore.GREEN}Results for {name}:{Style.RESET_ALL}")
    print(f"Key Generation Time: {stats['keygen_mean_ms']:.2f} ± {stats['keygen_std_ms']:.2f} ms")
    print(f"Signing Time: {stats['sign_mean_ms']:.2f} ± {stats['sign_std_ms']:.2f} ms")
    print(f"Signature Size: {stats['signature_size_mean_bytes']:.0f} bytes")
    print(f"Memory Usage: {stats['memory_mean_mb']:.2f} MB")
    
    return metrics, stats

def create_plots(all_metrics: List[Dict], all_stats: List[Dict]):
    print(f"\n{Fore.CYAN}Generating plots...{Style.RESET_ALL}")
    
    # Create a DataFrame for boxplots
    df_times = pd.DataFrame()
    for metrics in all_metrics:
        name = metrics['algorithm']
        df_times = pd.concat([
            df_times,
            pd.DataFrame({
                'Algorithm': name,
                'Time (ms)': metrics['keygen_times'],
                'Operation': 'Key Generation'
            }),
            pd.DataFrame({
                'Algorithm': name,
                'Time (ms)': metrics['sign_times'],
                'Operation': 'Signing'
            })
        ])
    
    # Set up the plotting style
    sns.set_style("whitegrid")
    plt.figure(figsize=(15, 10))
    
    # Create subplots
    plt.subplot(2, 1, 1)
    sns.boxplot(data=df_times, x='Algorithm', y='Time (ms)', hue='Operation')
    plt.title('Performance Comparison of Signature Algorithms')
    plt.xticks(rotation=45)
    
    # Create bar plot for signature sizes
    plt.subplot(2, 1, 2)
    sizes_df = pd.DataFrame([{
        'Algorithm': m['algorithm'],
        'Size (bytes)': s['signature_size_mean_bytes']
    } for m, s in zip(all_metrics, all_stats)])
    sns.barplot(data=sizes_df, x='Algorithm', y='Size (bytes)')
    plt.title('Signature Sizes')
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, 'benchmark_results.png'))
    print(f"{Fore.GREEN}Plots saved as benchmark_results.png{Style.RESET_ALL}")
    
    # Save detailed results to CSV
    results_df = pd.DataFrame(all_stats)
    results_df.to_csv(os.path.join(CSV_DIR, 'benchmark_results.csv'), index=False)
    print(f"{Fore.GREEN}Detailed results saved to benchmark_results.csv{Style.RESET_ALL}")

def main():
    algorithms = {
        'RSA-2048': (rsa_sha256.RSA2048Signer, None),
        'ECDSA-P256': (ecdsa_sha256.ECDSASigner, None),
        'Ed25519': (ed25519_sha256.ED25519Signer, None),
        'Dilithium2': (dilithium.DilithiumSigner, '44'),
        'Dilithium3': (dilithium.DilithiumSigner, '65'),
        'Dilithium5': (dilithium.DilithiumSigner, '87')
    }

    all_metrics = []
    all_stats = []
    
    for name, (signer_class, security_level) in algorithms.items():
        metrics, stats = collect_metrics(name, signer_class, security_level)
        all_metrics.append(metrics)
        all_stats.append(stats)
    
    create_plots(all_metrics, all_stats)

if __name__ == '__main__':
    freeze_support()
    main()
