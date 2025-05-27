import sys
import types
import os
import pytest
import logging
from unittest.mock import patch, MagicMock


fake_track_event = MagicMock()
azure_mock = types.ModuleType("azure")
monitor_mock = types.ModuleType("monitor")
events_mock = types.ModuleType("events")
extension_mock = types.ModuleType("extension")
extension_mock.track_event = fake_track_event
events_mock.extension = extension_mock
monitor_mock.events = events_mock
azure_mock.monitor = monitor_mock

sys.modules["azure"] = azure_mock
sys.modules["azure.monitor"] = monitor_mock
sys.modules["azure.monitor.events"] = events_mock
sys.modules["azure.monitor.events.extension"] = extension_mock


from common.logging.event_utils import track_event_if_configured


@patch.dict(os.environ, {"APPLICATIONINSIGHTS_CONNECTION_STRING": "InstrumentationKey=some-key"})
def test_track_event_called_when_configured():
    event_name = "TestEvent"
    event_data = {"key": "value"}

    fake_track_event.reset_mock()
    track_event_if_configured(event_name, event_data)
    fake_track_event.assert_called_once_with(event_name, event_data)


@patch("common.logging.event_utils.logging")
@patch.dict(os.environ, {}, clear=True)
def test_track_event_skipped_when_not_configured(mock_logging):
    event_name = "SkippedEvent"
    event_data = {"key": "value"}

    track_event_if_configured(event_name, event_data)
    mock_logging.warning.assert_called_once_with(
        f"Skipping track_event for {event_name} as Application Insights is not configured"
    )
