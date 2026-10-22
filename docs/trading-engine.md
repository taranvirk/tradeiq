# Trading engine

`Broker` defines account, positions, orders, submit, and cancel operations. `SimulatedBroker` is safe and local. `AlpacaPaperBroker` only accepts a `paper-api` base URL and keeps credentials server-side.

Orders use CREATED, VALIDATED, SUBMITTED, PARTIALLY_FILLED, FILLED, CANCELLED, and REJECTED vocabulary. The current simulation path produces immediate fills after validation, while the schema supports asynchronous and partial broker updates. Every trade stores strategy, model version, confidence, and risk context for auditability.

The paper order API accepts either share quantity or dollar notional, converts dollar orders to fractional shares at the simulated market fill, updates the active paper account's decimal cash balance, maintains weighted average entry cost, records a distinct order and trade, and writes a portfolio snapshot in one database transaction. Buying shares changes cash and position value but does not itself create a portfolio loss.
