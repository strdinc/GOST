# AGENTS.md

This document describes the operational guidelines for automated agents,
code assistants, and tooling that interact with this repository.

The repository contains an educational implementation used for
cryptography laboratory work focused on step-by-step visualization of
the Kuznyechik cipher transformations and arithmetic in GF(2\^8).

Agents must follow the rules below when modifying or extending the
codebase.

------------------------------------------------------------------------

# Project Purpose

The project is designed as a didactic tool, not a production
cryptographic library.

Primary goals: - demonstrate arithmetic in GF(2\^8) - visualize
polynomial representation of bytes - show step-by-step execution of
Kuznyechik transformations - help students verify manual calculations -
generate traceable intermediate outputs

Correctness and transparency of operations are prioritized over
performance.

------------------------------------------------------------------------

# Core Principles

## 1. Binary Arithmetic

All operations must be performed using binary arithmetic.\
Each value must be representable as:

-   hexadecimal
-   binary
-   polynomial form over GF(2)

Example:

hex: 95\
bin: 10010101\
poly: x\^7 + x\^4 + x\^2 + 1

------------------------------------------------------------------------

## 2. Full Traceability

Every transformation must print intermediate steps:

-   XOR operations
-   GF(2\^8) multiplication
-   polynomial reduction
-   S-box substitutions
-   intermediate vector states

Hidden computation steps are not allowed.

------------------------------------------------------------------------

## 3. Tabular Visualization

Operations involving multiple steps must be shown as tables using pandas
DataFrame.

Examples: - XOR tables - GF multiplication steps - S-box substitution
tables - l() computation tables - R/L transformation states

------------------------------------------------------------------------

## 4. No External Crypto Libraries

Agents must not introduce cryptographic libraries such as:

-   pycryptodome
-   cryptography
-   OpenSSL bindings

All cryptographic operations must remain implemented manually.

------------------------------------------------------------------------

## 5. GF(2\^8) Polynomial

The irreducible polynomial used for the field must remain:

p(x) = x\^8 + x\^7 + x\^6 + x + 1

Constants in code:

MOD_POLY_FULL = 0x1C3\
MOD_POLY_LOW = 0xC3

These values must not be changed.

------------------------------------------------------------------------

# Kuznyechik Transformations

## X

X[k](a) = k XOR a

------------------------------------------------------------------------

## S

S(a) = π(a15) \|\| ... \|\| π(a0)

Inverse:

S\^-1(a)

------------------------------------------------------------------------

## R

R(a15,...,a0) = l(a15,...,a0) \|\| a15 \|\| ... \|\| a1

Where:

l(a15,...,a0) = 148·a15 ⊕ 32·a14 ⊕ 133·a13 ⊕ 16·a12 ⊕ 194·a11 ⊕ 192·a10
⊕ 1·a9 ⊕ 251·a8 ⊕ 1·a7 ⊕ 192·a6 ⊕ 194·a5 ⊕ 16·a4 ⊕ 133·a3 ⊕ 32·a2 ⊕
148·a1 ⊕ 1·a0

All multiplications occur in GF(2\^8).

------------------------------------------------------------------------

## L

L(a) = R\^16(a)

Inverse:

L\^-1(a)

------------------------------------------------------------------------

## Feistel Step

F[k](a,%20b) = ( LSX[k](a) XOR b, a )

Where:

LSX[k](a) = L(S(X[k](a)))

------------------------------------------------------------------------

# Input Interface

The program must allow flexible user input.

Source vector: b0..b15 as 16 hexadecimal bytes.

Permutation mapping example:

a0 = b3 a1 = b13 a2 = b14 ...

Input format:

3 13 14 11 ...

Direct vector input should also be supported.

Key input must always be 16 bytes.

------------------------------------------------------------------------

# Data Structures

Vectors must be represented as:

list\[int\]

Length:

16

Range:

0 ≤ value ≤ 255

------------------------------------------------------------------------

# Verification

After transformations, the program must verify:

S\^-1(S(a)) = a\
R\^-1(R(a)) = a\
L\^-1(L(a)) = a

------------------------------------------------------------------------

# Modification Rules

When modifying the code:

1.  Keep detailed step-by-step output.
2.  Preserve DataFrame tables.
3.  Maintain binary and polynomial representations.
4.  Do not simplify away intermediate operations.
5.  Preserve algorithm correctness.

------------------------------------------------------------------------

# Performance

Performance is not a priority.

Readable computation traces and transparency are more important than
execution speed.
