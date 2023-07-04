import json
import requests
import rsa
import lzma
import base64

BLOCK_SIZE = 117


def main():
    with open("1.png", "rb") as f:
        data = f.read()
    with open("rsa_public_key.pem") as f:
        key = f.read()
    compressed = lzma.compress(data)
    key = rsa.PublicKey.load_pkcs1_openssl_pem(key)
    enc = []
    for i in range(0, len(compressed), BLOCK_SIZE):
        d = compressed[i : i + BLOCK_SIZE]
        enc.append(rsa.encrypt(d, key))
    enc = b"".join(enc)
    b64 = base64.b64encode(enc)
    b64 = str(b64, encoding="ascii")
    d = json.dumps({"img": b64})
    r = requests.post(
        "http://127.0.0.1:8502/predict",
        data=d,
        headers={"Content-Type": "application/json"},
    )
    print(r, r.text)


if __name__ == "__main__":
    main()
