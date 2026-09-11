# API

Interactive docs: `http://localhost:8000/api/docs` (OpenAPI via FastAPI).

Auth: POST /api/v1/auth/{register,login,logout,refresh,forgot-password,reset-password,verify-email}.
Users: GET/PUT /api/v1/users/me. Customer: GET /api/v1/customer/payments.
Payments: POST/GET /api/v1/payments, GET /api/v1/payments/{id}, POST .../confirm (demo), POST .../cancel. Header `Idempotency-Key` supported.
Transactions: GET /api/v1/transactions (+ filters, pagination), GET /api/v1/transactions/{id}.
Refunds, invoices, payment-links, wallet, withdrawals, api-keys, webhooks, notifications, merchants (profile/KYC/dashboard), admin/*.
Public: /api/v1/public/{checkout,pay,invoice,receipt}/..., POST /api/v1/webhooks/provider/{code}.

Consistent envelope: `{success, data}` / `{success:false, error:{code,message}}` with pagination `{page,page_size,total}`.
