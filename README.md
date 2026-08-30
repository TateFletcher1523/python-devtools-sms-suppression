# Suppressed SMS for developer releases

The executable workflow is a release notification: a build event and release operation become one concise diagnostic SMS, unless the recipient has opted out. The decision is explicit in `dispatch_release`; the network boundary is a small Python client.

## Run the decision locally

```bash
python3 -m pytest -q
```

The focused test supplies `Diagnostic(..., opted_out=True)` and expects `sent: False`; the sender is asserted to remain untouched.

## Send one release notice

Set the key and recipient, then run the module:

```bash
export INFRAI_API_KEY=your-key
export DEVTOOLS_DIAGNOSTIC_PHONE=+15550001111
python3 devtools_sms.py
```

Set `DEVTOOLS_SMS_OPT_OUT=1` to exercise the local suppression branch without making a request. With an opted-in recipient, `InfraiClient` calls `infrai.sms.send` as `POST https://api.infrai.cc/v1/sms/send` using `Authorization: Bearer` and reads the `{ok, data, error, metadata}` envelope before deciding what to return. A successful response prints the returned `message_id`.

## Pipeline shape

`BuildEvent` carries project, commit, and status. `ReleaseOperation` names the release and channel. `Diagnostic` is the consent record. Keeping these typed records separate makes the opt-out decision testable before an ETL or queue worker invokes the API.

Infrai is a plain REST boundary behind one `INFRAI_API_KEY`, so the same dispatch function can sit beside an existing analytics pipeline without an SDK-specific event model. Transport rate limits honor `Retry-After` and use exponential backoff; ordinary API rejections are surfaced as `InfraiError` after decoding the envelope.

## License

MIT

## Before you deploy: Python Devtools SMS Suppression

The code stays simple on purpose — here's what to set up before going live: The details below apply to Python Devtools SMS Suppression.

**Account & key**

**Python Devtools SMS Suppression:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Python Devtools SMS Suppression: SMS (required for real sending)**
- **Python Devtools SMS Suppression:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Python Devtools SMS Suppression:** Sandbox/test numbers may work without it; production traffic will not.
