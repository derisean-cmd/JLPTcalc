jlpt_app/
├── webapp.py                  ← main app code CREATED
├── requirements.txt        ← dependencies DONE??
├── init_db.py              ← sets up your database_CREATED
├── papers/                 ← all your test papers_CREATED
│   ├── n1_2025_dec/
│   │   ├── info.json        ← answers, scoring, page guide
│   │   ├── paper.pdf        ← questions
│   │   └── listening.mp3   ← audio file
│   └── n1_2025_jul/
│       ├── info.json
│       ├── paper.pdf
│       └── listening.mp3
└── .streamlit/             ← hidden settings folder
    └── secrets.toml        ← keeps passwords safe

####
to-do:
1]  fix result display (show wrong questions, summary view in chart in diff tab??)
2] adjust pdf and answer sheet alignment (scroll bar?)
3] audio display listening in diff session?


    ------------------------
    ## how to update repo:
    git add . 
    git commit -m "remark,remark,remark"
    git push

    ## how to open webapp
    streamlit run webapp.py
    Local URL: http://localhost:8501
    Network URL: http://192.168.1.102:8501

    ## how to open swagger (remember the directory)
    uvicorn swaggerapp:app --reload
    http://127.0.0.1:8000/docs
