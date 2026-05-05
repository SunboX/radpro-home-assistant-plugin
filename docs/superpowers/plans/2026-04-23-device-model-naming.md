<!--
SPDX-FileCopyrightText: 2026 André Fiedler

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Device Model Naming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show Home Assistant config entries and devices as `<deviceModel> (<deviceId>)` when a probed model is available, while preserving `deviceId` as the stable identity.

**Architecture:** Keep naming logic centralized in `custom_components/radpro_usb/identity.py` so config flow creation and setup-time migration share the same title builder. Reuse the existing `RadProDeviceIdentity.model` field and keep entity device naming tied to `entry.title`.

**Tech Stack:** Python, pytest, Home Assistant custom integration helpers

---

### Task 1: Update Identity Title Construction

**Files:**
- Modify: `tests/test_identity_helpers.py`
- Modify: `custom_components/radpro_usb/identity.py`
- Modify: `custom_components/radpro_usb/config_flow.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_device_title_uses_model_when_available() -> None:
    """Prefer the probed model name in the Home Assistant entry title."""
    assert device_title("ABC123", model="Bosean FS-5000") == "Bosean FS-5000 (ABC123)"


def test_device_title_falls_back_when_model_is_missing() -> None:
    """Keep the legacy prefix when the probe does not return a usable model."""
    assert device_title("ABC123", model="  ") == "Rad Pro (ABC123)"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_identity_helpers.py -k "device_title or describe_entry_updates" -v`
Expected: FAIL because `device_title()` only accepts `device_id` and still hardcodes `Rad Pro (...)`.

- [ ] **Step 3: Write minimal implementation**

```python
def device_title(device_id: str, model: str | None = None) -> str:
    """Build a stable config-entry title for a physical counter."""
    # Normalize the optional model so whitespace-only values still use the fallback name.
    normalized_model = model.strip() if isinstance(model, str) else ""
    display_name = normalized_model or "Rad Pro"
    return f"{display_name} ({device_id})"
```

- [ ] **Step 4: Use the shared helper everywhere titles are built**

```python
updated_title = device_title(identity.device_id, model=identity.model)

return self.async_create_entry(
    title=device_title(identity.device_id, model=identity.model),
    data=data,
    options=options,
)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_identity_helpers.py -k "device_title or describe_entry_updates" -v`
Expected: PASS for the new naming tests and the existing entry-update coverage.

### Task 2: Verify The Targeted Regression Surface

**Files:**
- Test: `tests/test_identity_helpers.py`
- Test: `tests/test_coordinator_helpers.py`
- Test: `tests/test_config_flow_helpers.py`

- [ ] **Step 1: Run the focused regression checks**

Run: `pytest tests/test_identity_helpers.py tests/test_coordinator_helpers.py tests/test_config_flow_helpers.py -v`
Expected: PASS with no naming regressions in the identity helpers and no unrelated parser/config-flow breakage.

- [ ] **Step 2: Commit the implementation**

```bash
git add docs/superpowers/plans/2026-04-23-device-model-naming.md \
  tests/test_identity_helpers.py \
  custom_components/radpro_usb/identity.py \
  custom_components/radpro_usb/config_flow.py
git commit -m "feat: use device model in entry names"
```
