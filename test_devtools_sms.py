from devtools_sms import BuildEvent, Diagnostic, InfraiClient, ReleaseOperation, dispatch_release


def test_opted_out_diagnostic_never_calls_sender():
    class NeverCalled:
        def __call__(self, request):
            raise AssertionError("sender must not be called")

    result = dispatch_release(
        Diagnostic("+15550001111", True),
        BuildEvent("compiler", "abc123", "failed"),
        ReleaseOperation("1.4.0", "canary"),
        InfraiClient(key="test-key", opener=NeverCalled()),
    )
    assert result == {"sent": False, "reason": "opted_out", "release": "1.4.0"}
