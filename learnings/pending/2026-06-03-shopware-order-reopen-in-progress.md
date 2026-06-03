---
id: alp-shopware-2026-06-order-reopen-in-progress
project: alp-shopware
domain: [shopware, checkout, order-management]
tags: [state-machine, order-state, reopen, in_progress, admin, NetgradeOrderStatusFlow]
confidence: high
source: task
created: 2026-06-03
author: agent
---

## Kontext

Im Shopware-Admin kann der Bestellstatus standardmäßig nicht von **In Bearbeitung** (`in_progress`) zurück auf **Offen** (`open`) gesetzt werden. Die Statusmaschine `order.state` enthält `reopen` nur von `cancelled` und `completed` nach `open` — nicht von `in_progress`. Bei `order_transaction.state` existiert dieser Übergang bereits.

## Erkenntnis

Erlaubte Admin-Statuswechsel kommen aus `state_machine_transition` in der DB, nicht aus UI-Logik. Ein fehlender Übergang lässt sich per Plugin-Migration ergänzen: `action_name = reopen`, `from = in_progress`, `to = open` auf der State Machine `order.state`. Danach zeigt das Backend dieselbe „Wiedereröffnen“-Aktion wie bei abgebrochenen/abgeschlossenen Bestellungen.

Implementierung im Repo: Plugin `NetgradeOrderStatusFlow`, Migration `Migration1780500000AddOrderReopenFromInProgress`.

## Anwendung

1. Nach Deploy: `bin/console plugin:update NetgradeOrderStatusFlow` (oder `database:migrate --all`).
2. Übergang prüfen:
   ```sql
   SELECT smt.action_name, from_s.technical_name, to_s.technical_name
   FROM state_machine_transition smt
   JOIN state_machine sm ON sm.id = smt.state_machine_id AND sm.technical_name = 'order.state'
   JOIN state_machine_state from_s ON from_s.id = smt.from_state_id
   JOIN state_machine_state to_s ON to_s.id = smt.to_state_id
   WHERE from_s.technical_name = 'in_progress' AND to_s.technical_name = 'open';
   ```
3. Bestellstatus prüfen (z. B. Bestellnummer `472034`):
   ```sql
   SELECT o.order_number, sms.technical_name AS order_state
   FROM `order` o
   JOIN state_machine_state sms ON sms.id = o.state_id
   WHERE o.order_number = '<NUMMER>';
   ```
4. Verlauf: `state_machine_history` mit `entity_name = 'order'` und `referenced_id = UNHEX('<order-uuid>')`.
5. Nebenwirkungen: Plugins/Flows auf `state_enter.order.state.in_progress` oder `reopen` (z. B. FgitsTicketsV3 `extrasActionOnReopen`) können bei Rücksetzung reagieren.

## Links

- `custom/static-plugins/NetgradeOrderStatusFlow/src/Migration/Migration1780500000AddOrderReopenFromInProgress.php`
- Shopware-Core Referenz (fehlender Übergang): `vendor/shopware/core/Migration/V6_3/Migration1536233560BasicData.php` (order.state transitions)
- Konstante: `StateMachineTransitionActions::ACTION_REOPEN`
