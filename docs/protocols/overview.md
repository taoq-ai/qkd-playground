# QKD Protocols Overview

Quantum Key Distribution protocols allow two parties (traditionally Alice and Bob) to establish a shared secret key using quantum mechanics, with the guarantee that any eavesdropping is detectable.

## Protocol Phases

All protocols in QKD Playground follow a common pipeline:

1. **Preparation** — Alice prepares qubits according to the protocol rules
2. **Transmission** — Qubits travel through the quantum channel (subject to noise and potential eavesdropping)
3. **Measurement** — Bob measures incoming qubits
4. **Sifting** — Alice and Bob compare measurement metadata to distill a raw key
5. **Error Estimation** — A subset of the key is sacrificed to estimate the error rate
6. **Information Reconciliation** — Cascade-inspired error correction fixes remaining bit discrepancies
7. **Privacy Amplification** — Hash-based compression removes any information an eavesdropper may have gained

## BB84 Protocol

The first and most widely known QKD protocol, proposed by Bennett and Brassard in 1984.

**How it works:**

- Alice randomly picks bits and bases (rectilinear + or diagonal ×), prepares qubits accordingly
- Bob measures each qubit in a randomly chosen basis
- They publicly compare bases (not values) and keep only matching positions (~50% sift rate)
- Error estimation reveals eavesdropping if QBER exceeds ~11%

!!! info "Eavesdropper Detection"
    An eavesdropper (Eve) using intercept-resend introduces approximately 25% errors in the sifted key, which is detectable during error estimation.

## B92 Protocol

A simplified version of BB84 proposed by Bennett in 1992, using only two non-orthogonal states (|0⟩ and |+⟩) instead of four.

**Key differences from BB84:**

- Uses fewer states, making implementation simpler
- Bob's inconclusive measurements are discarded, yielding a ~25% sift rate
- Eavesdropping threshold is ~15%

## E91 Protocol

Proposed by Ekert in 1991, this protocol uses entangled particle pairs and Bell's inequality.

**Key differences from BB84:**

- Security is based on quantum entanglement rather than the no-cloning theorem
- Alice and Bob share Bell pairs |Φ+⟩ = (|00⟩ + |11⟩)/√2
- Eavesdropping degrades the CHSH Bell inequality violation (S drops below 2√2 ≈ 2.83)
- No basis announcement needed — the CHSH test itself detects Eve

## SARG04 Protocol

Proposed by Scarani, Acín, Ribordy, and Gisin in 2004, SARG04 is a variant of BB84 designed to resist **photon number splitting (PNS) attacks**.

**Key differences from BB84:**

- During sifting, Alice announces **non-orthogonal state pairs** instead of her measurement basis
- Bob must determine which of the two states was sent — if his basis was wrong, he cannot distinguish them
- This makes it significantly harder for Eve to exploit multi-photon pulses
- Sift rate is ~25% (vs BB84's ~50%), trading efficiency for PNS resistance
- Eavesdropping threshold is ~11%

!!! warning "PNS Attacks"
    In practical QKD implementations, laser sources sometimes emit more than one photon per pulse. A PNS attacker splits off extra photons and stores them until basis information is announced. SARG04's non-orthogonal pair announcement neutralizes this attack.

## Channel Noise Models

QKD Playground supports configurable channel imperfections to simulate real-world conditions:

- **Depolarizing noise** — Randomly scrambles qubit states with a configurable probability, modeling decoherence in fiber optic cables
- **Photon loss** — Simulates photons being absorbed or scattered in the channel, resulting in missing detections

These noise sources make eavesdropper detection harder, since some errors are expected even on a secure channel. The simulator lets you explore how noise affects QBER and key rates.

## Post-Processing

After error estimation, the raw key undergoes two post-processing steps:

### Information Reconciliation

A Cascade-inspired protocol that corrects remaining bit errors:

- Divides the key into blocks and compares parities over the classical channel
- When a parity mismatch is found, binary search within the block locates the error
- Reveals some information (the parities) that must be accounted for in privacy amplification

### Privacy Amplification

Hash-based key compression that eliminates leaked information:

- Uses SHA-256-based universal hashing
- Output length is determined by the Shannon binary entropy bound
- Higher error rates mean more bits must be sacrificed
- The result is a shorter but provably secure final key

## Comparison

| Feature | BB84 | B92 | E91 | SARG04 |
|---------|------|-----|-----|--------|
| States used | 4 | 2 | Entangled pairs | 4 |
| Bases | 2 | 2 | 3 | 2 |
| Security basis | No-cloning | Non-orthogonality | Bell inequality | Non-orthogonal pairs |
| Sift rate | ~50% | ~25% | ~50% | ~25% |
| QBER threshold | ~11% | ~15% | CHSH test | ~11% |
| PNS resistant | No | Partially | Yes | Yes |
| Complexity | Medium | Low | High | Medium |
