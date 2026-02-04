#!/usr/bin/env sh
set -eu

OUT_DIR="${1:-mtls}"
CLIENT_NAME="${2:-pi-agent-client}"

mkdir -p "$OUT_DIR"

CA_KEY="$OUT_DIR/ca.key"
CA_CERT="$OUT_DIR/ca.crt"

CLIENT_KEY="$OUT_DIR/${CLIENT_NAME}.key"
CLIENT_CSR="$OUT_DIR/${CLIENT_NAME}.csr"
CLIENT_CERT="$OUT_DIR/${CLIENT_NAME}.crt"
CLIENT_EXT="$OUT_DIR/${CLIENT_NAME}.ext"

# 1) Create a small CA (private key + self-signed cert)
openssl genrsa -out "$CA_KEY" 4096
openssl req -x509 -new -nodes -key "$CA_KEY" -sha256 -days 3650 \
  -subj "/C=IN/ST=NA/L=NA/O=APT-Defender/OU=CA/CN=APT-Defender-Helper-CA" \
  -out "$CA_CERT"

# 2) Create client key + CSR
openssl genrsa -out "$CLIENT_KEY" 2048
openssl req -new -key "$CLIENT_KEY" \
  -subj "/C=IN/ST=NA/L=NA/O=APT-Defender/OU=Pi-Agent/CN=${CLIENT_NAME}" \
  -out "$CLIENT_CSR"

# 3) Client cert extensions (critical for mTLS): clientAuth EKU
cat > "$CLIENT_EXT" <<EOF
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer
EOF

# 4) Sign client cert with the CA
openssl x509 -req -in "$CLIENT_CSR" -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial \
  -out "$CLIENT_CERT" -days 825 -sha256 -extfile "$CLIENT_EXT"

# 5) Verify
openssl x509 -in "$CLIENT_CERT" -noout -text | grep -E "Subject:|Issuer:|Extended Key Usage" || true

echo ""
echo "Generated:"
echo "  CA cert (install/trust this on Helper server): $CA_CERT"
echo "  Client cert (set HELPER_CLIENT_CERT):         $CLIENT_CERT"
echo "  Client key  (set HELPER_CLIENT_KEY):          $CLIENT_KEY"
