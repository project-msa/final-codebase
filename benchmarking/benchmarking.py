import timeit
import sys
from algorithms import rsa_sha256
from cryptography.hazmat.primitives import hashes, serialization

test_message = b"Benchmarking RSA vs Dilithium in DKIM"
test_headers = {"From": "test@example.com", "To": "recipient@example.com", 
                "Subject": "Test Email", "Date": "Mon, 01 Jan 2024 00:00:00 +0000"}
test_body = "This is a test email body."

signer = rsa_sha256.RSA2048Signer(domain="example.com", selector="default")

## key generation
keygen_time = timeit.timeit(signer.generate_keys, number=100) / 100
print(f"Average RSA key generation time: {keygen_time * 1000:.2f} ms")

## public key/private key sizes
private_key, public_key = signer.generate_keys()
rsa_priv_size = sys.getsizeof(private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
rsa_pub_size = sys.getsizeof(private_key.public_key().public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo))
print(f"RSA Private Key: {rsa_priv_size} bytes | Public Key: {rsa_pub_size} bytes")

## signature generation
sign_time = timeit.timeit(lambda: signer.sign(test_message), number=100) / 100
print(f"Average RSA signing time: {sign_time * 1000:.2f} ms")

## signature size
rsa_sig = signer.sign(test_message)
print(f"RSA Signature Size: {len(rsa_sig)} bytes | Message Size: {len(test_message)} bytes")

## generate dkim record
dkim_sig_time = timeit.timeit(lambda: signer.generate_dkim_signature(test_headers, test_body), number=100) / 100
print(f"Average DKIM signature generation time: {dkim_sig_time * 1000:.2f} ms")

## dns record size
rsa_record = signer.dkim_record()[1]
print(f"RSA DKIM Record Size: {len(rsa_record)} bytes")

## verification
signature = signer.generate_dkim_signature(test_headers, test_body)
verifier = rsa_sha256.RSA2048Verifier(signer.dkim_record()[1]) 
verify_time = timeit.timeit(
    lambda: verifier.verify_dkim_signature(signature, "\r\n".join(f"{k}: {v}" for k, v in test_headers.items()), test_body),
    number=100
) / 100
print(f"Average DKIM verification time: {verify_time * 1000:.2f} ms")

import time

# RSA Throughput
start = time.time()
for _ in range(1000):
    signer.sign(test_message)
rsa_throughput = 1000 / (time.time() - start)
print(f"RSA Throughput: {rsa_throughput:.2f} sig/s")

from memory_profiler import memory_usage
mem_usage = memory_usage((signer.generate_keys, (), {}))
print(f"Peak memory during keygen: {max(mem_usage)} MiB")

import psutil
import os

# Measure CPU/RAM during RSA signing
process = psutil.Process(os.getpid())
cpu_before = process.cpu_percent()
mem_before = process.memory_info().rss
signer.sign(test_message)
cpu_after = process.cpu_percent()
mem_after = process.memory_info().rss
print(f"RSA CPU: {cpu_after - cpu_before:.2f}% | RAM: {(mem_after - mem_before) / 1024:.2f} KB")
