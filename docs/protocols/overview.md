# QKD Protocols Overview

Quantum Key Distribution protocols allow two parties (traditionally Alice and Bob) to establish a shared secret key using quantum mechanics, with the guarantee that any eavesdropping is detectable.

## BB84 Protocol

The first and most widely known QKD protocol, proposed by Bennett and Brassard in 1984.

**How it works:**

1. **Preparation** — Alice randomly picks bits and bases, prepares qubits accordingly
2. **Transmission** — Qubits are sent through a quantum channel
3. **Measurement** — Bob measures each qubit in a randomly chosen basis
4. **Reconciliation** — Alice and Bob publicly compare bases (not values)
5. **Sifting** — They keep only bits where bases matched
6. **Error estimation** — Sample a subset to estimate the quantum bit error rate (QBER)
7. **Privacy amplification** — Shorten the key to remove any information an eavesdropper might have

!!! info "Eavesdropper Detection"
    An eavesdropper (Eve) using intercept-resend introduces approximately 25% errors in the sifted key, which is detectable during error estimation.

## E91 Protocol

Proposed by Ekert in 1991, this protocol uses entangled particle pairs and Bell's inequality.

**Key difference from BB84:** Security is based on quantum entanglement rather than the no-cloning theorem. Eavesdropping degrades the Bell inequality violation, providing a detection mechanism rooted in fundamental physics.

## B92 Protocol

A simplified version of BB84 proposed by Bennett in 1992, using only two non-orthogonal states instead of four.

**Key difference from BB84:** Uses fewer states, making implementation simpler but with lower key generation efficiency.

## Comparison

| Feature | BB84 | E91 | B92 |
|---------|------|-----|-----|
| States used | 4 | Entangled pairs | 2 |
| Bases | 2 | 3 | 2 |
| Security basis | No-cloning theorem | Bell inequality | Non-orthogonality |
| Key efficiency | ~50% | ~50% | ~25% |
| Complexity | Medium | High | Low |
