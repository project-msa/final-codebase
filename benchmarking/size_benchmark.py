import sys, os, timeit, psutil
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm
import random
import string
from colorama import init, Fore, Style
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import rsa_sha256, dilithium, ecdsa_sha256, ed25519_sha256
from multiprocessing import freeze_support

# Initialize colorama
init()

# Constants
NUM_ITERATIONS = 50
NUM_SAMPLES = 10
MESSAGE_SIZES = [1024, 4096, 16384, 65536, 262144]  # Different message sizes to test (in bytes)

# Result paths
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
CSV_DIR = os.path.join(RESULTS_DIR, "csv")
IMAGES_DIR = os.path.join(RESULTS_DIR, "images")

def generate_random_message(size):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size)).encode()

def benchmark_algorithm(name, signer_class, security_level, message_size, sample_num):
    metrics = {
        'algorithm': name,
        'message_size': message_size,
        'sample': sample_num,
        'keygen_times': [],
        'sign_times': [],
        'signature_sizes': []
    }
    
    # Initialize signer
    signer = signer_class(security_level=security_level) if security_level else signer_class()
    message = generate_random_message(message_size)
    
    # Run key generation benchmark
    print(f"Running {name}...")
    pbar = tqdm(range(NUM_ITERATIONS), desc=f"{name} Progress")
    for _ in pbar:
        # Key generation timing
        start_time = timeit.default_timer()
        private_key, public_key = signer.generate_keys()
        metrics['keygen_times'].append((timeit.default_timer() - start_time) * 1000)
        
        # Signing timing
        start_time = timeit.default_timer()
        signature = signer.sign(message)
        metrics['sign_times'].append((timeit.default_timer() - start_time) * 1000)
        metrics['signature_sizes'].append(len(signature))
        
    # Calculate statistics
    stats = {
        'algorithm': name,
        'message_size': message_size,
        'sample': sample_num,
        'keygen_mean_ms': np.mean(metrics['keygen_times']),
        'keygen_std_ms': np.std(metrics['keygen_times']),
        'sign_mean_ms': np.mean(metrics['sign_times']),
        'sign_std_ms': np.std(metrics['sign_times']),
        'signature_size': np.mean(metrics['signature_sizes'])
    }
    
    print(f"\nResults for {name} with {message_size} bytes (sample {sample_num}):")
    print(f"Key Generation: {stats['keygen_mean_ms']:.2f} ± {stats['keygen_std_ms']:.2f} ms")
    print(f"Signing: {stats['sign_mean_ms']:.2f} ± {stats['sign_std_ms']:.2f} ms")
    print(f"Signature Size: {stats['signature_size']:.0f} bytes")
    
    return metrics, stats

def create_plots(all_stats, all_metrics):
    # Convert stats to DataFrame
    df_stats = pd.DataFrame(all_stats)
    df_metrics = pd.DataFrame(all_metrics)
    
    # Save detailed results to CSV
    df_detailed = pd.DataFrame(all_metrics)
    df_detailed.to_csv(os.path.join(CSV_DIR, 'size_benchmark_detailed_results.csv'), index=False)
    
    # Calculate aggregate statistics
    df_agg = df_stats.groupby(['algorithm', 'message_size']).agg({
        'keygen_mean_ms': ['mean', 'std'],
        'sign_mean_ms': ['mean', 'std'],
        'signature_size': 'first'
    }).reset_index()
    
    df_agg.columns = ['Algorithm', 'Message Size', 'Key Gen Mean', 'Key Gen Std', 
                      'Sign Mean', 'Sign Std', 'Signature Size']
    df_agg.to_csv(os.path.join(CSV_DIR, 'size_benchmark_aggregate_results.csv'), index=False)
    
    # Create plots
    print("Generating plots...")
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # Key Generation Time vs Message Size
    sns.lineplot(data=df_stats, x='message_size', y='keygen_mean_ms', hue='algorithm', ax=axes[0,0])
    axes[0,0].set_title('Key Generation Time vs Message Size')
    axes[0,0].set_xlabel('Message Size (bytes)')
    axes[0,0].set_ylabel('Time (ms)')
    axes[0,0].set_xscale('log')
    axes[0,0].set_yscale('log')
    
    # Signing Time vs Message Size
    sns.lineplot(data=df_stats, x='message_size', y='sign_mean_ms', hue='algorithm', ax=axes[0,1])
    axes[0,1].set_title('Signing Time vs Message Size')
    axes[0,1].set_xlabel('Message Size (bytes)')
    axes[0,1].set_ylabel('Time (ms)')
    axes[0,1].set_xscale('log')
    axes[0,1].set_yscale('log')
    
    # Signature Size
    signature_sizes = df_stats.groupby('algorithm')['signature_size'].first()
    signature_sizes.plot(kind='bar', ax=axes[1,0])
    axes[1,0].set_title('Signature Sizes')
    axes[1,0].set_ylabel('Size (bytes)')
    axes[1,0].set_xticklabels(axes[1,0].get_xticklabels(), rotation=45)
    
    # Distribution of signing times
    plt.figure(figsize=(12, 6))
    for alg in df_metrics['algorithm'].unique():
        alg_data = df_metrics[df_metrics['algorithm'] == alg]
        sns.kdeplot(data=alg_data['sign_times'].explode(), label=alg)
    plt.title('Distribution of Signing Times')
    plt.xlabel('Time (ms)')
    plt.ylabel('Density')
    plt.yscale('log')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, 'signing_time_distributions.png'))
    
    # Save main plots
    plt.figure(1)
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, 'size_benchmark_plots.png'))
    
    print(f"Detailed results saved to size_benchmark_detailed_results.csv")
    print(f"Aggregate results saved to size_benchmark_aggregate_results.csv")
    print(f"Plots saved as size_benchmark_plots.png")
    print(f"Additional distribution plot saved as signing_time_distributions.png")

def main():
    # Ensure results directories exist
    os.makedirs(CSV_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    
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
    
    for size in MESSAGE_SIZES:
        print(f"\nTesting messages of size {size} bytes")
        for sample in range(1, NUM_SAMPLES + 1):
            print(f"Testing sample {sample}/{NUM_SAMPLES} for size {size}")
            for name, (signer_class, security_level) in algorithms.items():
                metrics, stats = benchmark_algorithm(name, signer_class, security_level, size, sample)
                all_metrics.append(metrics)
                all_stats.append(stats)
    
    create_plots(all_stats, all_metrics)

if __name__ == '__main__':
    freeze_support()
    main()