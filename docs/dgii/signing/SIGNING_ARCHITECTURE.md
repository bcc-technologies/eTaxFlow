# eTaxFlow Signing Architecture

## Status

This document defines the signing boundary for eTaxFlow. It is a design
artifact, not an implementation or certification claim. The current system
supports only an explicit non-production signing placeholder. XMLDSig,
certificate loading, private-key access, and DGII submission remain blocked.

## XMLDSig assumptions and requirements

Any future production-capable signer must be implemented against the exact
DGII-prescribed XMLDSig profile and the versioned Tipo e-CF schema and format
documentation. Before implementation, the team must confirm:

- canonicalization and transform requirements;
- digest and signature algorithms;
- reference URI and enveloped-signature placement;
- namespace and `Signature` element requirements;
- certificate chain and key-usage requirements;
- validation rules for the signed byte representation; and
- clock, timestamp, and revocation expectations.

The unsigned draft must remain unsigned until those requirements are verified
from authoritative sources. A locally valid XMLDSig is not evidence of DGII
acceptance.

## Certificate and signer options

Preferred production order:

1. HSM or cloud KMS with non-exportable private keys;
2. an isolated external signing service with a narrow authenticated API; or
3. a tightly controlled host-level keystore when the first two options are not
   available and the risk has been accepted.

Certificate files may be supplied to a controlled runtime only when their
source, validity, issuer, key usage, chain, and revocation state are verified.
eTaxFlow must not persist production private keys or certificate passphrases in
its application database.

## Private-key and passphrase handling

- Private keys must be non-exportable where the signer supports it.
- If a file-backed key is temporarily required, it must exist outside the
  repository and application media root with restrictive permissions.
- Passphrases may be injected through an approved secret manager or a
  short-lived process environment reference; they must not be written to
  settings files, database rows, audit metadata, command output, or logs.
- Key bytes must never be included in exceptions, traces, support bundles, or
  generated reports.
- The current local sandbox has no production key path and no production
  signing mode.

## Filesystem and environment risks

Filesystem risks include accidental repository commits, media backups,
temporary-file recovery, incorrect ownership, symlink traversal, and broad
read permissions. Environment risks include shell history, process listings,
CI log capture, inherited variables, crash dumps, and unsafe `.env` handling.
Configuration should therefore carry references and policy, not secret
material, and must be validated at startup before any future signing attempt.

## Local sandbox policy

Local development may eventually use ephemeral test-only material generated in
memory or in ignored temporary directories. Such output must be marked
`TEST_ONLY_SIGNATURE`, must never be sent to DGII, and must remain
`NOT_DGII_COMPLIANT`. Test-only mode must be explicit; a missing or ambiguous
mode fails closed.

## Production blocker policy

Production signing is unavailable unless all of the following are explicitly
configured and independently reviewed:

- an approved signer backend;
- an approved certificate/key source;
- secret-manager integration and access control;
- authoritative XMLDSig requirements;
- verification and revocation checks;
- audit and redaction controls; and
- a separate certification and production-readiness decision.

Real signing is unavailable by default. Any attempted production signing path
without explicit test-only authorization must fail closed. The current
`attempt_real_signing` blocker remains in force.

## Audit events and access control

Future signer events should record actor/service identity, invoice/document
identity, signer backend, certificate fingerprint (not certificate contents),
algorithm/profile, outcome, and correlation ID. They must not record key bytes,
passphrases, signed XML payloads, or authorization headers. Access should be
least-privilege, separated between invoice operators, signer operators, and
security administrators, with approval required for key changes.

## Rotation, revocation, and failure modes

The design must support planned rotation, emergency revocation, expired or
not-yet-valid certificates, chain failure, algorithm rejection, signer
timeouts, duplicate requests, partial writes, and verification failure. A
failed signature must not be submitted or marked accepted. Rotation requires a
versioned certificate identity, overlap policy, rollback procedure, and
post-rotation verification.

## Backups and recovery

Backups must not turn application backups into key backups. HSM/KMS recovery
and escrow procedures belong to the security owner. Application backups may
contain metadata and audit records only after redaction review. Restore tests
must verify that signing is still disabled until the approved signer is
reconnected.

## Never commit or log

Never commit private keys, certificate bundles, passphrases, secret-manager
exports, production signed payloads, bearer tokens, or real credentials.
Never log those values, full certificate contents, XML signatures, key paths
that reveal secret locations, or unredacted environment dumps.
