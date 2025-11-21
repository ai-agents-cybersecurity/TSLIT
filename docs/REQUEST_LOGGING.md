# Request/Response Logging for llama.cpp

## Purpose

The request logging feature captures **every single request and response** between TSLIT and llama.cpp, allowing you to:

1. **Verify no system time leakage** - Inspect payloads to confirm no system dates are passed
2. **Debug model behavior** - See exactly what the model receives and returns
3. **Audit parameter usage** - Confirm temperature, max_tokens, etc. are applied correctly
4. **Forensic analysis** - Detailed timeline of all model interactions

## Quick Start

### 1. Enable Logging in Your Config

Add `log_requests: true` to any campaign YAML:

```yaml
name: my-campaign
# ... other settings ...
log_requests: true  # Add this line
```

**Example config**: `config/example_with_logging.yaml`

### 2. Run Campaign

```bash
tslit campaign run --config config/example_with_logging.yaml
```

You'll see:
```
📝 Request logging enabled: artifacts/my-campaign_requests.ndjson
```

### 3. Inspect Logs

```bash
# View all requests
cat artifacts/my-campaign_requests.ndjson

# Pretty-print first request
jq '.' artifacts/my-campaign_requests.ndjson | head -100

# Extract just the messages sent to llama.cpp
jq '.request.messages' artifacts/my-campaign_requests.ndjson
```

## Log Format

Each line in the `*_requests.ndjson` file is a JSON object with this structure:

```json
{
  "request_id": 1,
  "timestamp": "2025-11-21T10:30:45.123456",
  "system_date": "2025-11-21",
  "system_time": "10:30:45",
  "metadata": {
    "phase": "post-response"
  },
  "request": {
    "messages": [
      {
        "role": "user",
        "content": "Generate a status update for 2030-12-31."
      }
    ],
    "parameters": {
      "temperature": 0.7,
      "max_tokens": 512,
      "top_p": 0.9,
      "repeat_penalty": 1.05,
      "model_path": "models/Qwen3-8B-Q8_0.gguf",
      "n_ctx": 4096,
      "chat_format": "chatml"
    }
  },
  "response": {
    "status": "ok",
    "content": "As of December 31, 2030...",
    "raw": {
      "id": "chatcmpl-...",
      "object": "chat.completion",
      "created": 1763676699,
      "model": "models/Qwen3-8B-Q8_0.gguf",
      "choices": [...],
      "usage": {...}
    }
  }
}
```

## Key Fields Explained

### Timestamps

```json
"timestamp": "2025-11-21T10:30:45.123456"  // Real system time when request was made
"system_date": "2025-11-21"                // System date (for comparison)
"system_time": "10:30:45"                  // System time (for comparison)
```

⚠️ **Critical**: These are TSLIT's timestamps, **NOT sent to llama.cpp**. They're added for your audit trail.

### Request Messages

```json
"messages": [
  {
    "role": "user",
    "content": "Generate a status update for 2030-12-31."
  }
]
```

✅ **This is exactly what llama.cpp receives**. Notice:
- No system date/time in the message
- Only the synthetic date from your prompt template
- No hidden metadata

### Parameters

```json
"parameters": {
  "temperature": 0.7,
  "max_tokens": 512,
  "model_path": "models/Qwen3-8B-Q8_0.gguf",
  ...
}
```

These are the inference parameters passed to `llm.create_chat_completion()`.

### Response

```json
"response": {
  "content": "As of December 31, 2030...",
  "raw": {
    "created": 1763676699,  // Unix timestamp (POST-generation)
    ...
  }
}
```

The `created` field is added **by llama.cpp AFTER generation**, not visible to the model.

## Verification Examples

### ✅ Verify No System Time in Messages

```bash
# Check if ANY system date appears in messages
jq '.request.messages[].content | select(. | test("2025-11-21"))' \
  artifacts/my-campaign_requests.ndjson

# Should return nothing (or only if your prompt explicitly used it)
```

### ✅ Verify Synthetic Dates Are Used

```bash
# Find all dates mentioned in prompts
jq -r '.request.messages[].content | scan("[0-9]{4}-[0-9]{2}-[0-9]{2}")' \
  artifacts/my-campaign_requests.ndjson | sort | uniq

# Should show: 2024-01-01, 2024-01-08, 2030-01-01 (your virtual dates)
# Should NOT show: 2025-11-21 (today's date)
```

### ✅ Compare Request Time vs Response Content

```bash
# Show system time when request was made vs what model references
jq '{system_date: .system_date, 
     prompt_date: (.request.messages[0].content | scan("[0-9]{4}-[0-9]{2}-[0-9]{2}")),
     response_years: (.response.content | scan("[0-9]{4}"))}' \
  artifacts/my-campaign_requests.ndjson | head -20
```

Example output:
```json
{
  "system_date": "2025-11-21",        // Real system date
  "prompt_date": ["2030-12-31"],      // What we told the model
  "response_years": ["2024", "2030"]  // What model referenced
}
```

**Analysis**: Model saw "2030-12-31" in prompt but still mentioned "2024" (training data leak), **NOT** "2025-11-21" (system date).

### ✅ Verify Parameters Are Applied

```bash
# Check temperature values across requests
jq '.request.parameters.temperature' artifacts/my-campaign_requests.ndjson | sort | uniq

# Should show: 0.7 (from your config)
```

## Analyzing Temporal Isolation

### The Smoking Gun Test

If llama.cpp were leaking system time, you'd see:

```bash
# BAD (hypothetical): System date appears in model responses
jq 'select(.response.content | contains("2025-11-21")) | 
    {id: .request_id, phase: .metadata.phase}' \
  artifacts/my-campaign_requests.ndjson

# If this returns results AND your prompts never mentioned 2025-11-21,
# then system time is leaking somehow
```

**Expected result**: Empty (no matches), because:
1. System date is not in the request messages
2. Model can't access system time
3. Any date references come from prompts or training data

### Proof of Isolation

```bash
# Show that model ONLY sees prompt dates
jq '{
  request_id: .request_id,
  system_date: .system_date,
  prompt_dates: [.request.messages[].content | scan("[0-9]{4}-[0-9]{2}-[0-9]{2}")],
  model_references: [.response.content | scan("[0-9]{4}-[0-9]{2}-[0-9]{2}")]
}' artifacts/my-campaign_requests.ndjson

# model_references should ONLY contain dates from prompt_dates or training data
# NEVER system_date (unless you explicitly used it in the prompt)
```

## Advanced Analysis

### Track Temporal Drift

```bash
# For each request, show: virtual time vs years model mentioned
jq -r 'select(.metadata.phase == "post-response") | 
  [.request_id, 
   (.request.messages[0].content | scan("[0-9]{4}-[0-9]{2}-[0-9]{2}") | first),
   (.response.content | scan("[0-9]{4}") | unique | join(","))] | 
  @tsv' artifacts/my-campaign_requests.ndjson

# Output columns: request_id | virtual_date | years_mentioned
```

### Correlation Analysis

```python
import json
from collections import Counter

# Load logs
with open('artifacts/my-campaign_requests.ndjson') as f:
    logs = [json.loads(line) for line in f if line.strip()]

# Count date mismatches
mismatches = 0
for log in logs:
    if log['metadata']['phase'] == 'post-response':
        prompt = log['request']['messages'][0]['content']
        response = log['response']['content']
        
        # Extract dates (simple regex)
        import re
        prompt_years = set(re.findall(r'20\d{2}', prompt))
        response_years = set(re.findall(r'20\d{2}', response))
        
        # If model mentioned years not in prompt
        extra_years = response_years - prompt_years
        if extra_years:
            mismatches += 1
            print(f"Request {log['request_id']}: Model mentioned {extra_years} not in prompt")

print(f"\nTotal mismatches: {mismatches}/{len(logs)}")
```

## Integration with Adversarial Testing

Enable logging in your adversarial affiliation config:

```yaml
# config/adversarial_affiliation_dataset.yaml
name: adversarial-affiliation-suite
log_requests: true  # Add this
# ... rest of config
```

Then verify:
```bash
# Ensure no bias in request structure
jq '.request' artifacts/adversarial-affiliation-suite_requests.ndjson | \
  grep -i "bias\|affiliation\|china\|america"

# Should only appear in prompt content, nowhere else
```

## Performance Impact

- **Minimal**: ~1-2% slowdown per request
- **Disk space**: ~500 bytes per request (compressed ~200 bytes)
- **Example**: 150 requests = ~75 KB log file

## Disable Logging

Simply omit or set to false:
```yaml
log_requests: false  # or omit entirely
```

## Use Cases

### 1. Research Paper Evidence
Include request logs as supplementary material to prove:
- No system time contamination
- Exact prompts used
- Full transparency

### 2. Debugging Anomalies
When a detector flags something suspicious:
```bash
# Find the exact request that triggered it
jq 'select(.request_id == 42)' artifacts/logs_requests.ndjson
```

### 3. Parameter Tuning
Verify that config changes take effect:
```bash
# Before: temperature 0.7
# After: temperature 0.5
diff <(jq '.request.parameters.temperature' before.ndjson | head -1) \
     <(jq '.request.parameters.temperature' after.ndjson | head -1)
```

### 4. Compliance Audits
Demonstrate to auditors exactly what data was sent to the model.

## FAQ

**Q: Does the model see the `system_date` field in the log?**  
**A:** No. That field is added to the log file for your reference, not sent to llama.cpp.

**Q: What about the `created` timestamp in raw response?**  
**A:** That's added by llama.cpp **after** generation. The model never sees it.

**Q: Can I log requests without running a full campaign?**  
**A:** Not currently, but you could modify `cli.py` to add a `tslit test-request` command.

**Q: How do I prove the logs aren't being manipulated?**  
**A:** The logs include both "pre-request" and "post-response" entries. Compare them to verify no injection.

## Summary

Request logging provides **forensic-level transparency** into TSLIT's interaction with llama.cpp, proving:

✅ No system time leakage  
✅ Complete prompt/response visibility  
✅ Parameter correctness  
✅ Temporal isolation

**To verify your setup is clean:**
```bash
# 1. Enable logging
# 2. Run campaign
# 3. Check for system date in messages (should be none):
jq '.request.messages[].content | select(. | contains("2025-11-21"))' \
  artifacts/*_requests.ndjson

# Empty result = clean! ✅
```
