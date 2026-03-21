# Personal Finance Tracker: Feature Specifications

## 🎯 Core MVP Features

### 1. Transaction Engine

- **Income & Expense Tracking:** Log transactions with amount, date, and category.
- **Dynamic Categories:** Pre-defined categories (e.g., Food, Transport, Salary) with the ability to add, rename, or delete custom ones.
- **Multi-Account Support:** Support for multiple "Wallets" (e.g., BCA, Cash, GoPay). Users can assign transactions to specific accounts to maintain accurate balances.
- **Internal Transfers:** Move funds between accounts (e.g., withdrawing cash from an ATM) without impacting total income or expense reports.

### 2. Debt & Credit Module (The "Lent" Ledger)

- **Person-Based Tracking:** A separate ledger to track money lent to others or borrowed.
- **Net Position:** View total "Receivables" (money coming back) vs. "Payables" (money you owe) as a standalone summary that does not interfere with daily spending data.

### 3. Budgeting & Planning

- **Standard Monthly Budget:** A "template" budget that repeats automatically every month.
- **Monthly Overrides:** Ability to customize a specific month's budget (e.g., increasing "Gifts" for December) without changing the global base template.
- **Progress Tracking:** Compare "Budgeted vs. Actual" spending per category with simple percentage or progress indicators.

### 4. Financial Health (The "Big Picture")

- **Balance Sheet:** A high-level summary of Assets (Total Account Balances + Receivables) vs. Liabilities (Outstanding Debts).
- **Savings Rate:** Automatic calculation of `(Total Income - Total Expenses)` as a percentage of total income.

---

## 🚀 Future Implementation Roadmap

The following features are planned for subsequent development phases once the core system logic is stable:

| Feature                    | Description                                                                          |
| :------------------------- | :----------------------------------------------------------------------------------- |
| **Recurring Transactions** | Logic to automate fixed monthly costs like subscriptions (Spotify, Netflix) or rent. |
| **Search & History**       | Advanced filtering via Telegram commands (e.g., `/history food`) to query past data. |
| **Data Export**            | A command to generate and send a **CSV or PDF** report for external analysis.        |
| **Data Visualization**     | Automated generation of spending pie charts or monthly trend graphs sent as images.  |
