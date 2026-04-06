# Project Structure

Generated for Phase H handoff.  
Focuses on source code, docs, and key config files.

```text
stock-subscription-system/
├── backend/
│   ├── core/
│   │   ├── auth_serializers.py
│   │   ├── auth_urls.py
│   │   ├── auth_views.py
│   │   ├── middleware.py
│   │   ├── settings.py
│   │   └── urls.py
│   ├── subscriptions/
│   │   ├── migrations/
│   │   │   ├── 0001_initial_subscription.py
│   │   │   ├── 0002_alter_subscription_ticker.py
│   │   │   └── 0003_notificationlog.py
│   │   ├── templates/subscriptions/
│   │   │   └── merged_subscription_email.html
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── tasks.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   ├── utils.py
│   │   └── views.py
│   ├── .env.example
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/
│   │   │   ├── GuestRoute.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── context/AuthContext.jsx
│   │   ├── pages/
│   │   │   ├── HomePage.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   └── RegisterPage.jsx
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── docs/
│   ├── API.md
│   └── PROJECT_STRUCTURE.md
├── checklist.md
├── spec.md
└── tasks.md
```

## Notes

- Runtime/generated folders (e.g. `.git`, `venv`, `node_modules`, build artifacts) are intentionally omitted.
- Backend and frontend each have their own startup commands and env requirements (see root `README.md` and `docs/API.md`).
