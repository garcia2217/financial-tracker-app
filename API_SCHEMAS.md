# API Schemas & Data Models

This document provides a reference for the data structures used in the Financial Tracker App. It is intended for frontend developers to understand the expected JSON shapes for requests and responses.

## Table of Contents
- [User](#user)
- [Wallet (Account)](#wallet-account)
- [Category](#category)
- [Transaction](#transaction)
- [Budget](#budget)
- [Person](#person)
- [Debt (Lent Ledger)](#debt-lent-ledger)

---

## User
Represents a user in the system, either linked to Telegram or a standard web user.

### Entity Model
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Unique identifier (Primary Key) |
| `telegram_chat_id` | `BigInt` (Optional) | User's Telegram Chat ID |
| `username` | `String(255)` (Optional) | Unique username |
| `email` | `String(255)` (Optional) | User's email (from OAuth or other) |
| `google_id` | `String(255)` (Optional) | Google OAuth ID |
| `telegram_state` | `String(50)` | Current FSM state for Telegram bot interactions |
| `created_at` | `DateTime` | Timestamp of registration |
| `updated_at` | `DateTime` | Last update timestamp |

### API Schemas
**Create User (`UserCreate`)**
```json
{
  "telegram_chat_id": 123456789,
  "username": "johndoe",
  "email": "johndoe@example.com",
  "google_id": "1234567890",
  "password": "securepassword123",
  "telegram_state": "AWAITING_USERNAME"
}
```

**Update User (`UserUpdate`)**
```json
{
  "username": "newusername",
  "password": "newpassword123",
  "telegram_state": "ACTIVE"
}
```

**User Response (`UserResponse`)**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "telegram_chat_id": 123456789,
  "username": "johndoe",
  "email": "johndoe@example.com",
  "google_id": "1234567890",
  "telegram_state": "ACTIVE",
  "created_at": "2024-03-26T12:00:00Z",
  "updated_at": "2024-03-26T12:00:00Z"
}
```

---

## Wallet (Account)
Represents a financial account or "wallet" (e.g., Cash, Bank, Credit Card).

### Entity Model
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Unique identifier |
| `user_id` | `UUID` | Owner ID |
| `name` | `String(100)` | Name of the wallet (e.g., "BCA Bank") |
| `balance` | `Numeric(14,2)` | Current balance |

### API Schemas
**Create Wallet (`WalletCreate`)**
```json
{
  "name": "My Savings",
  "user_id": "uuid-here",
  "balance": 1000.50
}
```

**Wallet Response (`WalletResponse`)**
```json
{
  "id": "uuid-here",
  "user_id": "uuid-here",
  "name": "My Savings",
  "balance": 1000.50,
  "created_at": "2024-03-26T12:00:00Z",
  "updated_at": null
}
```

---

## Category
Categories for grouping income and expenses.

### Entity Model
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Unique identifier |
| `user_id` | `UUID` | Owner ID |
| `name` | `String(100)` | Category name (e.g., "Food") |
| `type` | `String` | Either `income` or `expense` |

### API Schemas
**Create Category (`CategoryCreate`)**
```json
{
  "name": "Transport",
  "type": "expense",
  "user_id": "uuid-here"
}
```

**Category Response (`CategoryResponse`)**
```json
{
  "id": "uuid-here",
  "user_id": "uuid-here",
  "name": "Transport",
  "type": "expense",
  "created_at": "2024-03-26T12:00:00Z"
}
```

---

## Transaction
The core record of money movement.

### Entity Model
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Unique identifier |
| `user_id` | `UUID` | Owner ID |
| `wallet_id` | `UUID` | Source wallet |
| `category_id` | `UUID` (Optional) | Associated category |
| `amount` | `Numeric(14,2)` | Transaction amount |
| `type` | `String` | `income`, `expense`, or `transfer` |
| `description` | `String(500)` | Note or memo |
| `destination_wallet_id` | `UUID` (Optional) | Target wallet if type is `transfer` |
| `transaction_date` | `DateTime` | Date the transaction occurred |

### API Schemas
**Create Transaction (`TransactionCreate`)**
```json
{
  "amount": 50.0,
  "type": "expense",
  "description": "Lunch at McD",
  "wallet_id": "uuid-here",
  "category_id": "uuid-here",
  "transaction_date": "2024-03-26T13:00:00Z"
}
```

**Transaction Response (`TransactionResponse`)**
```json
{
  "id": "uuid-here",
  "amount": 50.0,
  "type": "expense",
  "description": "Lunch at McD",
  "user_id": "uuid-here",
  "wallet_id": "uuid-here",
  "category_id": "uuid-here",
  "destination_wallet_id": null,
  "transaction_date": "2024-03-26T13:00:00Z",
  "created_at": "2024-03-26T13:01:00Z"
}
```

---

## Budget
Target spending limits per category.

### Entity Model
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Unique identifier |
| `user_id` | `UUID` | Owner ID |
| `category_id` | `UUID` | Category being budgeted |
| `amount` | `Numeric(14,2)` | Budgeted limit |
| `month` | `Int` (Optional) | Specific month (1-12) for overrides |
| `year` | `Int` (Optional) | Specific year for overrides |
| `is_default` | `Bool` | `True` if this is the standard monthly template |

### API Schemas
**Create Budget (`BudgetCreate`)**
```json
{
  "category_id": "uuid-here",
  "amount": 500.0,
  "month": null,
  "year": null,
  "is_default": true,
  "user_id": "uuid-here"
}
```

**Budget Response (`BudgetResponse`)**
```json
{
  "id": "uuid-here",
  "user_id": "uuid-here",
  "category_id": "uuid-here",
  "amount": 500.0,
  "month": null,
  "year": null,
  "is_default": true,
  "created_at": "2024-03-26T12:00:00Z"
}
```

---

## Person
A counterparty (person) that you have lent money to or borrowed money from.

### Entity Model
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Unique identifier |
| `user_id` | `UUID` | Owner ID |
| `name` | `String(100)` | Name of the person (e.g., "John", "Mom") |

### API Schemas
**Create Person (`PersonCreate`)**
```json
{
  "name": "John Doe",
  "user_id": "uuid-here"
}
```

**Person Response (`PersonResponse`)**
```json
{
  "id": "uuid-here",
  "user_id": "uuid-here",
  "name": "John Doe",
  "created_at": "2024-03-26T12:00:00Z",
  "updated_at": null
}
```

---

## Debt (Lent Ledger)
A standalone ledger entry for tracking money owed or receivable. Fully isolated from the `Transaction` model to keep debt data separate from daily spending.

### Entity Model
| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | `UUID` | Unique identifier |
| `user_id` | `UUID` | Owner ID |
| `person_id` | `UUID` | FK → Person (who owes/is owed) |
| `amount` | `Numeric(14,2)` | Original debt amount |
| `amount_settled` | `Numeric(14,2)` | Amount paid back so far (default `0`) |
| `type` | `String` | `receivable` (they owe you) or `payable` (you owe them) |
| `status` | `String` | `pending`, `partial`, or `settled` |
| `description` | `String(500)` (Optional) | Note or reason |
| `due_date` | `DateTime` (Optional) | Optional repayment deadline |

> **Net Position** is derived by aggregating `amount - amount_settled` grouped by `type`: the sum of non-settled `receivable` debts = total Receivables; sum of non-settled `payable` debts = total Payables.

### API Schemas
**Create Debt (`DebtCreate`)**
```json
{
  "person_id": "uuid-here",
  "amount": 200.0,
  "type": "receivable",
  "description": "Borrowed for lunch last week",
  "due_date": "2024-04-30T00:00:00Z",
  "user_id": "uuid-here"
}
```

**Update Debt (`DebtUpdate`)** — used to record repayments or mark as settled
```json
{
  "amount_settled": 200.0,
  "status": "settled"
}
```

**Debt Response (`DebtResponse`)**
```json
{
  "id": "uuid-here",
  "user_id": "uuid-here",
  "person_id": "uuid-here",
  "amount": 200.0,
  "amount_settled": 0.0,
  "type": "receivable",
  "status": "pending",
  "description": "Borrowed for lunch last week",
  "due_date": "2024-04-30T00:00:00Z",
  "created_at": "2024-03-26T12:00:00Z",
  "updated_at": null
}
```
