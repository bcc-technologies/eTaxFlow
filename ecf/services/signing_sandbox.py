"""Test-only XMLDSig sandbox using ephemeral OpenSSL material.

This module is deliberately not a production signer. It creates a short-lived
test key/certificate in a temporary directory, signs a local XML document, and
removes the material before returning. ``test_only`` must remain explicit and
the output is always ``NOT_DGII_COMPLIANT`` / ``TEST_ONLY_SIGNATURE``.
"""

from __future__ import annotations

import base64
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

from lxml import etree

XMLDSIG_NS = "http://www.w3.org/2000/09/xmldsig#"
DS = f"{{{XMLDSIG_NS}}}"
EXCLUSIVE_C14N = "http://www.w3.org/2001/10/xml-exc-c14n#"
ENVELOPED_SIGNATURE = "http://www.w3.org/2000/09/xmldsig#enveloped-signature"
RSA_SHA256 = "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"
SHA256 = "http://www.w3.org/2001/04/xmlenc#sha256"
TEST_ONLY_SIGNATURE = "TEST_ONLY_SIGNATURE"


class SandboxSigningError(RuntimeError):
    """Raised when an explicit test-only signing operation cannot proceed."""


def _require_openssl() -> str:
    executable = shutil.which("openssl")
    if executable is None:
        raise SandboxSigningError(
            "Test-only XMLDSig sandbox requires the local OpenSSL CLI; "
            "no production signing fallback is available."
        )
    return executable


def _run_openssl(executable: str, args: list[str], *, cwd: Path) -> bytes:
    try:
        completed = subprocess.run(
            [executable, *args],
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        # Do not include command output: it could contain paths or future
        # secret-bearing diagnostics. This backend is test-only and fails shut.
        raise SandboxSigningError("Ephemeral test-only OpenSSL operation failed.") from exc
    return completed.stdout


def _parse_xml(xml_bytes: bytes) -> etree._Element:
    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        root = etree.fromstring(xml_bytes, parser=parser)
    except (etree.XMLSyntaxError, TypeError, ValueError) as exc:
        raise SandboxSigningError("Sandbox signing requires well-formed XML bytes.") from exc
    if root.find(f"{DS}Signature") is not None:
        raise SandboxSigningError("Sandbox signer refuses XML that already contains Signature.")
    return root


def _canonicalize(element: etree._Element) -> bytes:
    return etree.tostring(element, method="c14n", exclusive=True, with_comments=False)


def _digest_root(root: etree._Element) -> str:
    return base64.b64encode(hashlib.sha256(_canonicalize(root)).digest()).decode("ascii")


def _temporary_test_certificate(workdir: Path, openssl: str) -> tuple[Path, Path]:
    key_path = workdir / "test_only_key.pem"
    cert_path = workdir / "test_only_cert.pem"
    _run_openssl(
        openssl,
        [
            "genpkey",
            "-algorithm",
            "RSA",
            "-pkeyopt",
            "rsa_keygen_bits:2048",
            "-out",
            key_path.name,
        ],
        cwd=workdir,
    )
    _run_openssl(
        openssl,
        [
            "req",
            "-x509",
            "-new",
            "-sha256",
            "-days",
            "1",
            "-key",
            key_path.name,
            "-subj",
            "/CN=eTaxFlow TEST ONLY",
            "-out",
            cert_path.name,
        ],
        cwd=workdir,
    )
    return key_path, cert_path


def sign_xml_sandbox(xml_bytes: bytes, *, test_only: bool = True) -> bytes:
    """Return a locally signed XMLDSig test artifact.

    The function is intentionally limited to explicit test-only use. Key and
    certificate files are generated under ``TemporaryDirectory`` and are
    removed before return. The returned XML is not DGII-compliant and must not
    be submitted.
    """
    if test_only is not True:
        raise SandboxSigningError(
            "Sandbox signing requires explicit test_only=True; real signing is blocked."
        )
    openssl = _require_openssl()
    root = _parse_xml(xml_bytes)
    digest_value = _digest_root(root)

    with tempfile.TemporaryDirectory(prefix="etaxflow-signing-test-only-") as temp_dir:
        workdir = Path(temp_dir)
        key_path, cert_path = _temporary_test_certificate(workdir, openssl)

        signature = etree.Element(f"{DS}Signature", nsmap={"ds": XMLDSIG_NS})
        signed_info = etree.SubElement(signature, f"{DS}SignedInfo")
        etree.SubElement(
            signed_info,
            f"{DS}CanonicalizationMethod",
            Algorithm=EXCLUSIVE_C14N,
        )
        etree.SubElement(signed_info, f"{DS}SignatureMethod", Algorithm=RSA_SHA256)
        reference = etree.SubElement(signed_info, f"{DS}Reference", URI="")
        transforms = etree.SubElement(reference, f"{DS}Transforms")
        etree.SubElement(
            transforms,
            f"{DS}Transform",
            Algorithm=ENVELOPED_SIGNATURE,
        )
        etree.SubElement(
            transforms,
            f"{DS}Transform",
            Algorithm=EXCLUSIVE_C14N,
        )
        etree.SubElement(reference, f"{DS}DigestMethod", Algorithm=SHA256)
        etree.SubElement(reference, f"{DS}DigestValue").text = digest_value

        signed_info_path = workdir / "signed_info.c14n"
        signed_info_path.write_bytes(_canonicalize(signed_info))
        signature_path = workdir / "signature.bin"
        _run_openssl(
            openssl,
            [
                "dgst",
                "-sha256",
                "-sign",
                key_path.name,
                "-out",
                signature_path.name,
                signed_info_path.name,
            ],
            cwd=workdir,
        )
        signature_value = etree.SubElement(signature, f"{DS}SignatureValue")
        signature_value.text = base64.b64encode(signature_path.read_bytes()).decode("ascii")

        key_info = etree.SubElement(signature, f"{DS}KeyInfo")
        x509_data = etree.SubElement(key_info, f"{DS}X509Data")
        x509_certificate = etree.SubElement(x509_data, f"{DS}X509Certificate")
        cert_der = _run_openssl(
            openssl,
            ["x509", "-in", cert_path.name, "-outform", "DER"],
            cwd=workdir,
        )
        x509_certificate.text = base64.b64encode(cert_der).decode("ascii")

    root.append(signature)
    return etree.tostring(root, encoding="utf-8", xml_declaration=False)


def _text(element: etree._Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def verify_xml_sandbox_signature(xml_bytes: bytes, *, test_only: bool = True) -> bool:
    """Verify the sandbox XMLDSig and its enveloped-document digest locally."""
    if test_only is not True:
        raise SandboxSigningError(
            "Sandbox verification requires explicit test_only=True; production verification is blocked."
        )
    openssl = _require_openssl()
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    try:
        root = etree.fromstring(xml_bytes, parser=parser)
    except (etree.XMLSyntaxError, TypeError, ValueError) as exc:
        raise SandboxSigningError("Sandbox verification requires well-formed XML bytes.") from exc
    signature = root.find(f"{DS}Signature")
    if signature is None:
        return False

    signed_info = signature.find(f"{DS}SignedInfo")
    reference = signed_info.find(f"{DS}Reference") if signed_info is not None else None
    digest_value = reference.find(f"{DS}DigestValue") if reference is not None else None
    if signed_info is None or reference is None or reference.get("URI") != "":
        return False
    digest_method = reference.find(f"{DS}DigestMethod")
    if digest_method is None or digest_method.get("Algorithm") != SHA256:
        return False
    if _text(digest_value) != _digest_root(root_without_signature(root)):
        return False

    signature_method = signed_info.find(f"{DS}SignatureMethod")
    if signature_method is None or signature_method.get("Algorithm") != RSA_SHA256:
        return False
    signature_text = _text(signature.find(f"{DS}SignatureValue"))
    certificate_text = _text(
        signature.find(f"{DS}KeyInfo/{DS}X509Data/{DS}X509Certificate")
    )
    if not signature_text or not certificate_text:
        return False

    with tempfile.TemporaryDirectory(prefix="etaxflow-signing-verify-test-only-") as temp_dir:
        workdir = Path(temp_dir)
        signed_info_path = workdir / "signed_info.c14n"
        signed_info_path.write_bytes(_canonicalize(signed_info))
        signature_path = workdir / "signature.bin"
        signature_path.write_bytes(base64.b64decode(signature_text, validate=True))
        cert_path = workdir / "test_only_cert.der"
        cert_path.write_bytes(base64.b64decode(certificate_text, validate=True))
        public_key_path = workdir / "test_only_public_key.pem"
        public_key_path.write_bytes(
            _run_openssl(
                openssl,
                ["x509", "-inform", "DER", "-in", cert_path.name, "-pubkey", "-noout"],
                cwd=workdir,
            )
        )
        try:
            _run_openssl(
                openssl,
                [
                    "dgst",
                    "-sha256",
                    "-verify",
                    public_key_path.name,
                    "-signature",
                    signature_path.name,
                    signed_info_path.name,
                ],
                cwd=workdir,
            )
        except SandboxSigningError:
            return False
    return True


def root_without_signature(
    root: etree._Element,
) -> etree._Element:
    """Return a copy of root with the enveloped Signature removed."""
    copied = etree.fromstring(etree.tostring(root))
    for candidate in copied.findall(f"{DS}Signature"):
        copied.remove(candidate)
    return copied


def sandbox_signature_diagnostics(xml_bytes: bytes) -> dict[str, object]:
    """Return explicit non-compliance diagnostics for sandbox signed output."""
    try:
        root = etree.fromstring(xml_bytes)
        signature_present = root.find(f"{DS}Signature") is not None
    except etree.XMLSyntaxError:
        signature_present = False
    return {
        "signature_status": TEST_ONLY_SIGNATURE,
        "signature_present": signature_present,
        "compliance_status": "NOT_DGII_COMPLIANT",
        "dgii_submission_allowed": False,
        "not_certification_evidence": True,
        "track_id": None,
        "dgii_call_made": False,
    }
