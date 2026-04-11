#!/usr/bin/env bash
# test_degraded_mode.sh — llm_client.py returns structured errors
# Verifies LLMError class, error categorization, and retryable detection.
set -euo pipefail
source "$(dirname "$0")/helpers.sh"
cd "$PROJECT_ROOT"

echo "=== Contract: Degraded Mode (llm_client.py error handling) ==="

# 1. LLMError class exists with category attribute
LLMERROR_CHECK=$(python3.11 -c "
import sys
sys.path.insert(0, 'scripts')
from llm_client import LLMError
e = LLMError('test error', category='timeout')
assert hasattr(e, 'category'), 'no category attr'
assert e.category == 'timeout', f'wrong category: {e.category}'
assert str(e) == 'test error', f'wrong message: {e}'
print('ok')
" 2>&1 || echo "fail")
assert "LLMError has category attribute" "$LLMERROR_CHECK" "ok"

# 2. _categorize_error handles all expected categories
CATEGORIZE_CHECK=$(python3.11 -c "
import sys, urllib.error, io
sys.path.insert(0, 'scripts')
from llm_client import _categorize_error

# timeout
assert _categorize_error(TimeoutError('timed out')) == 'timeout', 'timeout failed'

# rate_limit via HTTP 429
err429 = urllib.error.HTTPError('http://x', 429, 'Rate Limited', {}, io.BytesIO(b''))
assert _categorize_error(err429) == 'rate_limit', 'rate_limit failed'

# auth via HTTP 401
err401 = urllib.error.HTTPError('http://x', 401, 'Unauthorized', {}, io.BytesIO(b''))
assert _categorize_error(err401) == 'auth', 'auth failed'

# network via URLError
assert _categorize_error(urllib.error.URLError('conn refused')) == 'network', 'network failed'

# unknown fallback
assert _categorize_error(ValueError('something')) == 'unknown', 'unknown failed'

print('ok')
" 2>&1 || echo "fail")
assert "_categorize_error handles all categories" "$CATEGORIZE_CHECK" "ok"

# 3. _is_retryable identifies retryable vs non-retryable
RETRYABLE_CHECK=$(python3.11 -c "
import sys, urllib.error, io
sys.path.insert(0, 'scripts')
from llm_client import _is_retryable

# Retryable: HTTP 429, 500
err429 = urllib.error.HTTPError('http://x', 429, 'Rate Limited', {}, io.BytesIO(b''))
err500 = urllib.error.HTTPError('http://x', 500, 'Server Error', {}, io.BytesIO(b''))
assert _is_retryable(err429) == True, '429 should be retryable'
assert _is_retryable(err500) == True, '500 should be retryable'

# Retryable: network errors
assert _is_retryable(urllib.error.URLError('conn refused')) == True, 'URLError should be retryable'
assert _is_retryable(ConnectionError('reset')) == True, 'ConnectionError should be retryable'
assert _is_retryable(TimeoutError('timed out')) == True, 'TimeoutError should be retryable'

# Non-retryable: HTTP 400, 404
err400 = urllib.error.HTTPError('http://x', 400, 'Bad Request', {}, io.BytesIO(b''))
err404 = urllib.error.HTTPError('http://x', 404, 'Not Found', {}, io.BytesIO(b''))
assert _is_retryable(err400) == False, '400 should not be retryable'
assert _is_retryable(err404) == False, '404 should not be retryable'

# Non-retryable: ValueError
assert _is_retryable(ValueError('bad')) == False, 'ValueError should not be retryable'

print('ok')
" 2>&1 || echo "fail")
assert "_is_retryable identifies retryable errors" "$RETRYABLE_CHECK" "ok"

report
