<!--
SPDX-FileCopyrightText: 2026 André Fiedler

SPDX-License-Identifier: CC-BY-SA-4.0
-->

# Rad Pro Multi-Counter Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each config entry track one physical Rad Pro counter by `deviceId`, migrate existing entries automatically, and rebind them when USB paths change.

**Architecture:** Add a small identity-resolution layer shared by config flow and setup. Keep entity unique IDs stable by leaving them entry-based while switching config-entry and device-registry identity to `deviceId`.

**Tech Stack:** Home Assistant config entries, pyserial, pytest

---

### Task 1: Add failing identity tests

**Files:**
- Modify: `tests/test_config_flow_helpers.py`
- Create: `tests/test_setup_helpers.py`
- Test: `tests/test_config_flow_helpers.py`
- Test: `tests/test_setup_helpers.py`

- [ ] Write failing tests for config-flow probing with duplicate `deviceId` detection.
- [ ] Run the targeted tests and confirm the new cases fail for the expected reason.
- [ ] Write failing tests for setup migration from port-based identity to `deviceId`.
- [ ] Write failing tests for rebinding an entry to a new USB path when the saved path changes.
- [ ] Re-run targeted tests and confirm they fail before implementation.

### Task 2: Implement identity resolution and migration

**Files:**
- Modify: `custom_components/radpro_usb/config_flow.py`
- Modify: `custom_components/radpro_usb/__init__.py`
- Modify: `custom_components/radpro_usb/const.py`

- [ ] Add a stored `device_id` field constant and helper structures for probed identity.
- [ ] Implement temporary port probing that reads and parses `deviceId`.
- [ ] Update config flow to set unique ID from `deviceId` and store `device_id` in entry data.
- [ ] Implement setup-time migration and automatic port rebinding by scanning detected Rad Pro ports.
- [ ] Run focused tests and keep the new behavior green.

### Task 3: Switch device registry identity

**Files:**
- Modify: `custom_components/radpro_usb/sensor.py`
- Modify: `custom_components/radpro_usb/binary_sensor.py`

- [ ] Update device info to identify the physical counter by `device_id`.
- [ ] Keep entity unique IDs stable by preserving the current entry-based unique ID format.
- [ ] Expose `device_id` in entity extra attributes for diagnostics.
- [ ] Run the relevant tests.

### Task 4: Update docs and release metadata

**Files:**
- Modify: `custom_components/radpro_usb/manifest.json`
- Modify: `README.md`
- Modify: `docs/configuration.md`
- Modify: `docs/installation.md`
- Modify: `docs/troubleshooting.md`
- Modify: `info.md`

- [ ] Bump the integration version to `1.0.0`.
- [ ] Document multiple-counter support, migration behavior, and automatic port rebinding.
- [ ] Update troubleshooting guidance to mention physical-counter matching by `deviceId`.

### Task 5: Verify and publish

**Files:**
- Modify: tracked files from prior tasks only

- [ ] Run the full local test suite in the prepared Home Assistant environment.
- [ ] Review `git diff` and stage only the intended release changes.
- [ ] Commit the work with a release-oriented message.
- [ ] Push `main` to `origin`.
- [ ] Create GitHub release `v1.0.0` from the pushed commit with release notes summarizing the multi-counter changes.
