import time
import matplotlib.pyplot as plt
from algorithms import rsa_sha256
from cryptography.hazmat.primitives import serialization

# Initialize signer and test data
signer = rsa_sha256.RSA2048Signer(domain="example.com", selector="default")
test_message = b"Benchmarking RSA vs Dilithium in DKIM"
test_headers = {"From": "test@example.com", "To": "recipient@example.com",
                "Subject": "Test Email", "Date": "Mon, 01 Jan 2024 00:00:00 +0000"}
test_body = "This is a test email body."

# Prepare lists to store per-iteration timings (in milliseconds)
keygen_times = []
sign_times = []
dkim_sig_times = []
verify_times = []

# Benchmark key generation (100 iterations)
for _ in range(100):
    start = time.time()
    signer.generate_keys()
    keygen_times.append((time.time() - start) * 1000)

# Generate keys once for subsequent operations
private_key, public_key = signer.generate_keys()

# Benchmark signing (1000 iterations)
for _ in range(1000):
    start = time.time()
    signer.sign(test_message)
    sign_times.append((time.time() - start) * 1000)

# Benchmark DKIM signature generation (100 iterations)
for _ in range(100):
    start = time.time()
    signer.generate_dkim_signature(test_headers, test_body)
    dkim_sig_times.append((time.time() - start) * 1000)

# Prepare verifier
dkim_record = signer.dkim_record()[1]
verifier = rsa_sha256.RSA2048Verifier(dkim_record)
signature = signer.generate_dkim_signature(test_headers, test_body)

# Benchmark verification (100 iterations)
for _ in range(100):
    start = time.time()
    verifier.verify_dkim_signature(
        signature,
        "\r\n".join(f"{k}: {v}" for k, v in test_headers.items()),
        test_body
    )
    verify_times.append((time.time() - start) * 1000)

# Combine metrics for plotting
metrics = [
    ('RSA Key Generation', keygen_times),
    ('RSA Signing', sign_times),
    ('DKIM Signature Generation', dkim_sig_times),
    ('DKIM Signature Verification', verify_times),
]

# Create subplots: 4 rows, 1 column
fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(10, 20))

for ax, (label, times) in zip(axes, metrics):
    avg = sum(times) / len(times)
    ax.plot(times, label=label)
    ax.axhline(avg, linestyle='--', color='red', label=f'Average = {avg:.2f} ms')
    ax.set_title(f'{label} Timeline')
    ax.set_ylabel('Time (ms)')
    ax.legend()
    ax.grid(True)

# Set common X-axis label on the bottom plot
axes[-1].set_xlabel('Iteration')

# Maximize the figure window to full screen (platform-dependent)
mng = plt.get_current_fig_manager()
try:
    # Qt backend
    mng.window.showMaximized()
except AttributeError:
    try:
        # TkAgg backend
        mng.full_screen_toggle()
    except AttributeError:
        pass

plt.tight_layout()
plt.show()