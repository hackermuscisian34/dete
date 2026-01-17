package main

import (
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"log"
	"math/big"
	"os"
	"time"
)

func main() {
	certPath := "C:\\ProgramData\\APTDefender\\certs\\helper.crt"
	keyPath := "C:\\ProgramData\\APTDefender\\certs\\helper.key"

	// Create private key
	priv, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		log.Fatal(err)
	}

	// Create template
	template := x509.Certificate{
		SerialNumber: big.NewInt(1),
		Subject: pkix.Name{
			Organization: []string{"APT Defender"},
			CommonName:   "apt-defender-helper",
		},
		NotBefore: time.Now(),
		NotAfter:  time.Now().Add(time.Hour * 24 * 365),
		KeyUsage:  x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage: []x509.ExtKeyUsage{
			x509.ExtKeyUsageServerAuth,
		},
		BasicConstraintsValid: true,
	}

	// Create certificate
	derBytes, err := x509.CreateCertificate(rand.Reader, &template, &template, &priv.PublicKey, priv)
	if err != nil {
		log.Fatal(err)
	}

	// Save certificate
	certOut, err := os.Create(certPath)
	if err != nil {
		log.Fatal(err)
	}
	pem.Encode(certOut, &pem.Block{Type: "CERTIFICATE", Bytes: derBytes})
	certOut.Close()
	log.Printf("Written %s\n", certPath)

	// Save private key
	keyOut, err := os.Create(keyPath)
	if err != nil {
		log.Fatal(err)
	}
	pem.Encode(keyOut, &pem.Block{Type: "RSA PRIVATE KEY", Bytes: x509.MarshalPKCS1PrivateKey(priv)})
	keyOut.Close()
	log.Printf("Written %s\n", keyPath)
}
