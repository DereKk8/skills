# Linear Access: GraphQL Transport and Agent Vault

Transport mechanics belong here. Board IDs, planning rules, templates, and
domain authority belong to the respective board skills.

## 1. Choose the Agent Vault route

Follow the `secrets` skill for the active profile. General builders use
`coding`. Use a project profile only when its configured services include Linear.
Run the profile's readiness check before a new session. If the key or service is
missing, readiness fails, or the service is pending, stop and report the setup
needed. Never fetch a key directly or use a separate login as a fallback. If
`AGENT_ACCESS_PROFILE` is already set, use its inherited proxy, certificate,
and placeholder environment without starting another session.

Agent Vault provides `LINEAR_API_KEY` as a placeholder. The HTTPS proxy replaces
that placeholder with the real credential on the wire. Keep the value in the
request process only. Never print it, log it, persist it, or pass it as an
argument. Do not log request headers or dump the process environment.

## 2. Direct API protocol

- Endpoint: `https://api.linear.app/graphql`
- Method: `POST`
- Headers: `Content-Type: application/json` and `Authorization: <placeholder>`
- The placeholder is not the API credential. Do not replace it with a key read
  from a secret manager or another local source.

Pass query variables separately in the JSON payload rather than interpolating
them into a query:

```json
{
  "query": "mutation UpdateState($id: String!, $input: IssueUpdateInput!) { issueUpdate(id: $id, input: $input) { success } }",
  "variables": {
    "id": "issue-id",
    "input": { "stateId": "state-id" }
  }
}
```

## 3. Robust Python execution

Use Python's standard library, disable redirects, trust the CA supplied by the
active profile, and bound every request. The environment key below must come
from the brokered session; never set it by reading or copying a credential.

```python
import json
import os
import ssl
import urllib.error
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def execute_linear_graphql(query: str, variables: dict | None = None) -> dict:
    key = os.environ.get("LINEAR_API_KEY", "").strip()
    if not key:
        raise SystemExit("LINEAR_API_KEY is not available in the active Agent Vault session")

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    request = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": key, "Content-Type": "application/json"},
    )
    context = ssl.create_default_context(cafile=os.environ["SSL_CERT_FILE"])

    try:
        opener = urllib.request.build_opener(
            NoRedirect, urllib.request.HTTPSHandler(context=context)
        )
        with opener.open(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(body)
            first = err_json.get("errors", [{}])[0]
            message = first.get("extensions", {}).get("userPresentableMessage") or first.get("message")
            message = message or f"HTTP {error.code}"
        except (ValueError, IndexError, AttributeError):
            message = f"HTTP {error.code}"
        raise SystemExit(f"Linear API error ({error.code}): {message}") from None
    except (urllib.error.URLError, TimeoutError):
        raise SystemExit("Linear request timed out or network failed; verify outcome before retrying writes") from None

    if result.get("errors"):
        raise SystemExit(f"Linear GraphQL error: {result['errors'][0].get('message', 'Unknown error')}")
    if "data" not in result:
        raise SystemExit("Linear response missing data object")
    return result["data"]
```

## 4. Writes and verification

1. Read the current object and relevant template before writing.
2. Check `success === true` and check for partial GraphQL errors.
3. Query the object by ID after a mutation and verify the saved fields.
4. Compare meaning when Linear normalizes URLs or Markdown; do not repeat a
   write for cosmetic changes.
5. After a timeout, read the target before retrying a create.
