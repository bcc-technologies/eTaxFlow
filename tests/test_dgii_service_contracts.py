from django.conf import settings
from django.test import SimpleTestCase

from ecf.dgii.services.authentication import authenticate
from ecf.dgii.services.commercial_approval import request_commercial_approval
from ecf.dgii.services.contracts import (
    AuthenticationRequest,
    DGIIServiceConfiguration,
    MockTransportState,
    ReceptionRequest,
)
from ecf.dgii.services.mock_transport import LiveDGIITransport, MockDGIITransport
from ecf.dgii.services.receipt_ack import acknowledge_receipt
from ecf.dgii.services.reception import submit_reception
from ecf.dgii.services.status import consult_status


class DGIIMockServiceContractTests(SimpleTestCase):
    def test_settings_default_to_mock_without_live_urls(self):
        self.assertEqual(settings.DGII_ENVIRONMENT, "MOCK")
        self.assertFalse(settings.DGII_LIVE_TRANSPORT_ENABLED)
        self.assertEqual(settings.DGII_URL_RECEPCION, "")
        self.assertEqual(settings.DGII_URL_APROBACION_COMERCIAL, "")
        self.assertEqual(settings.DGII_URL_AUTENTICACION, "")

    def test_mock_authentication_returns_synthetic_token(self):
        transport = MockDGIITransport()
        result = authenticate(
            transport,
            AuthenticationRequest(
                software_name="eTaxFlow",
                software_version="MVP",
                software_type="INTERNAL",
            ),
        )
        self.assertEqual(result.access_token, "MOCK-TOKEN-000001")
        self.assertTrue(result.mock)
        self.assertEqual(transport.authentication_calls, 1)

    def test_mock_reception_status_approval_and_acknowledgment(self):
        state = MockTransportState(
            statuses={"MOCK-TRACK-000001": "IN_PROCESS_MOCK"},
            status_messages={"MOCK-TRACK-000001": "Configured test status"},
        )
        transport = MockDGIITransport(state=state)
        reception = submit_reception(
            transport,
            ReceptionRequest(
                xml_bytes=b"<ECF>TEST_ONLY</ECF>",
                invoice_internal_code="BCC-AR-2026-000001",
            ),
        )
        self.assertEqual(reception.track_id, "MOCK-TRACK-000001")
        self.assertTrue(reception.mock)
        status = consult_status(transport, reception.track_id)
        self.assertEqual(status.status, "IN_PROCESS_MOCK")
        approval = request_commercial_approval(
            transport,
            reception.track_id,
            approved=True,
            reason="Synthetic test approval",
        )
        self.assertTrue(approval.approved)
        self.assertEqual(approval.status, "APPROVED_MOCK")
        acknowledgment = acknowledge_receipt(transport, reception.track_id)
        self.assertTrue(acknowledgment.acknowledged)
        self.assertEqual(acknowledgment.status, "ACKNOWLEDGED_MOCK")
        self.assertEqual(transport.reception_calls, 1)
        self.assertEqual(transport.status_calls, 1)
        self.assertEqual(transport.approval_calls, 1)
        self.assertEqual(transport.receipt_acknowledgment_calls, 1)

    def test_live_transport_is_explicitly_blocked(self):
        with self.assertRaises(NotImplementedError):
            LiveDGIITransport()

    def test_mock_transport_does_not_use_production_urls_or_network(self):
        config = DGIIServiceConfiguration(
            environment="MOCK",
            url_recepcion="",
            url_aprobacion_comercial="",
            url_autenticacion="",
            live_transport_enabled=False,
        )
        transport = MockDGIITransport(configuration=config)
        result = transport.submit_reception(
            ReceptionRequest(xml_bytes=b"<ECF />", invoice_internal_code="LOCAL-1")
        )
        self.assertTrue(result.track_id.startswith("MOCK-TRACK-"))
        self.assertFalse(transport.configuration.live_transport_enabled)
