# Interactive Evidence Gathering Simulation

## 1. Overview

The **Evidence Simulator Engine** (`scripts/evidence_simulator.py`) enables autonomous agents and human fraud analysts to simulate interactive evidence gathering when initial graph signals are uncertain (e.g., out-of-region travel under Rule R3, or new device logins under Rule R5).

---

## 2. Interactive Evidence Types & Resolution Matrix

```
                          Uncertain Investigation Case
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
     Customer Contact           Step-Up Authentication     Merchant Inquiry
   (SMS / Automated Call)     (Push Notification / OTP)    (Fulfillment API)
            │                          │                          │
      ┌─────┴─────┐              ┌─────┴─────┐              ┌─────┴─────┐
      ▼           ▼              ▼           ▼              ▼           ▼
   Travel       Fraud          Biometric   Challenge        Home       Digital
  Confirmed   Confirmed         Passed      Failed        Delivered    Foreign
      │           │              │           │              │           │
      ▼           ▼              ▼           ▼              ▼           ▼
   CLEARED    CONFIRMED       CLEARED    CONFIRMED       CLEARED    CONFIRMED
   (Close)     (Block)        (Close)     (Block)        (Close)     (Block)
```

---

## 3. Dynamic State Machine Updates

When evidence is collected:
1. An `INTERACTIVE_EVIDENCE_GATHERING` trace step is appended to the case investigation history.
2. The case verdict is updated from `uncertain` to `cleared` or `confirmed_fraud`.
3. The Next Best Action (NBA) is dynamically updated (`CLOSE_NO_FRAUD` vs. `BLOCK_CARD` + `REIMBURSE_CUSTOMER`).
4. Re-evaluates SAR filing requirements if fraud is confirmed and exposure exceeds thresholds.

---

## 4. Verification & Testing

Tested in `tests/test_evidence_simulator.py`:
- Out-of-region travel confirmation dynamic resolution.
- Out-of-region unauthorized fraud confirmation dynamic resolution.
- Step-up biometric challenge workflow.
