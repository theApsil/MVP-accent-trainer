# MVP-accent-trainer
MVP версия ВКР до обучения моделей на голых результатах без настройки и настройки гиперпараметров


```bash
accent-mvp/
├── app/
│   ├── __init__.py
│   ├── main.py                  
│   ├── auth.py 
│   ├── database.py 
│   ├── models.py            
│   ├── audio_processing.py    
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── pages.py             # HTML-страницы
│   │   ├── user.py              # API пользователя
│   │   └── admin.py             # API администратора
│   └── templates/
│       ├── base.html
│       ├── login.html
│       ├── user_dashboard.html
│       ├── upload.html
│       ├── analysis_result.html
│       ├── history.html
│       └── admin_dashboard.html
├── static/
│   ├── css/style.css
│   └── reference_audio/         
├── uploads/                    
├── data/
│   └── app.db                 
├── pyproject.toml
└── README.md
```