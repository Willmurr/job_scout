import json, os

indeed_jobs = {
    "credit analyst_Madrid_10": [
        {"title": "Credit Risk Analyst", "company": "Fiserv", "location": "Madrid", "description": "Credit Risk Analyst role at Fiserv in Madrid. Full-time position focused on credit risk assessment and financial analysis.", "url": "https://to.indeed.com/aalkh8qxxg8f", "source": "Indeed"},
        {"title": "Finance Analyst - Treasury and Billing", "company": "JOTELULU", "location": "Madrid", "description": "Finance Analyst covering Treasury and Billing operations at JOTELULU in Madrid. Full-time role.", "url": "https://to.indeed.com/aarxs6yfqtdc", "source": "Indeed"},
        {"title": "Fund Operations Analyst", "company": "Arcano Partners", "location": "Madrid", "description": "Fund Operations Analyst at Arcano Partners Madrid. Permanent position focused on Spanish funds operations and financial analysis.", "url": "https://to.indeed.com/aawyrsdk2fct", "source": "Indeed"},
        {"title": "Financial Reporting Analyst", "company": "BNP Paribas", "location": "Madrid", "description": "Financial Reporting Analyst permanent role at BNP Paribas Madrid. Responsibilities include financial statements, regulatory reporting and IFRS.", "url": "https://to.indeed.com/aa9jsj6t6sy6", "source": "Indeed"},
        {"title": "Finance Project Manager and Analyst", "company": "BNP Paribas", "location": "Madrid", "description": "Finance Project Manager and Analyst permanent role at BNP Paribas Madrid. Combines financial analysis with project management.", "url": "https://to.indeed.com/aazxykjx9rmg", "source": "Indeed"},
        {"title": "Finance Data Quality Analyst", "company": "BNP Paribas", "location": "Madrid", "description": "Finance Data Quality Analyst at BNP Paribas Madrid. Focus on data integrity and financial data governance.", "url": "https://to.indeed.com/aazydp8lkzhq", "source": "Indeed"},
        {"title": "Financial Risk Controller", "company": "BNP Paribas", "location": "Madrid", "description": "Financial Risk Controller permanent position at BNP Paribas Madrid. Focus on market risk, credit risk and financial controls.", "url": "https://to.indeed.com/aa8v7zj7xwn2", "source": "Indeed"},
        {"title": "IFRS Reporting Analyst", "company": "BNP Paribas", "location": "Madrid", "description": "IFRS Reporting Analyst permanent role at BNP Paribas Madrid. Expertise in international financial reporting standards required.", "url": "https://to.indeed.com/aad46qzpzkx8", "source": "Indeed"},
        {"title": "Senior Quantitative Analyst - Market and Counterparty Risk", "company": "BNP Paribas", "location": "Madrid", "description": "Senior Quantitative Analyst for Market and Counterparty Risk Model Validation at BNP Paribas Madrid. Quantitative finance and risk modelling expertise required.", "url": "https://to.indeed.com/aahxcnccdpwd", "source": "Indeed"},
        {"title": "Operational Support Analyst Financial Markets", "company": "Grupo Digital", "location": "Madrid", "description": "Operational Support Analyst for Financial Markets at Grupo Digital Madrid. Hybrid role supporting financial markets operations.", "url": "https://to.indeed.com/aamkd9kdb6sb", "source": "Indeed"},
    ],
    "financial analyst_Madrid_10": [
        {"title": "Finance Analyst", "company": "Air Charter Service", "location": "Madrid", "description": "Finance Analyst full-time role at Air Charter Service in Madrid. Supporting financial planning, reporting and analysis.", "url": "https://to.indeed.com/aaz4pw879mhz", "source": "Indeed"},
        {"title": "Financial Analyst", "company": "Instalaciones Negratin SLU", "location": "Madrid", "description": "Financial Analyst role at Instalaciones Negratin SLU in Madrid. Financial modelling, budgeting and analysis.", "url": "https://to.indeed.com/aakpfddtxzkh", "source": "Indeed"},
        {"title": "Financial Controller", "company": "Enertis Applus+", "location": "Madrid", "description": "Financial Controller at Enertis Applus+ Madrid. Overseeing financial reporting, controls and compliance.", "url": "https://to.indeed.com/aaqp99xs7hzs", "source": "Indeed"},
        {"title": "Financial Controller", "company": "ROADIS", "location": "Madrid", "description": "Financial Controller full-time role at ROADIS Madrid. Managing financial reporting, budgeting and internal controls.", "url": "https://to.indeed.com/aaslcfcvxhdg", "source": "Indeed"},
        {"title": "Finance Analyst Treasury and Billing", "company": "JOTELULU", "location": "Madrid", "description": "Finance Analyst covering Treasury and Billing at JOTELULU Madrid. Cash management and billing analysis.", "url": "https://to.indeed.com/aamhv9w2qz6r", "source": "Indeed"},
        {"title": "Financial Reporting Analyst", "company": "BNP Paribas", "location": "Madrid", "description": "Financial Reporting Analyst permanent role at BNP Paribas Madrid. IFRS, regulatory reporting and financial statements.", "url": "https://to.indeed.com/aa9jsj6t6sy6", "source": "Indeed"},
        {"title": "Finance Project Manager Analyst", "company": "BNP Paribas", "location": "Madrid", "description": "Finance Project Manager and Analyst at BNP Paribas Madrid. Financial analysis and project delivery.", "url": "https://to.indeed.com/aazxykjx9rmg", "source": "Indeed"},
        {"title": "Business Data Analyst and Project Manager", "company": "BNP Paribas", "location": "Madrid", "description": "Business Data Analyst and Project Manager at BNP Paribas Madrid. Data analysis and financial project management.", "url": "https://to.indeed.com/aazs7pppmjfj", "source": "Indeed"},
        {"title": "Finance Data Quality Analyst", "company": "BNP Paribas", "location": "Madrid", "description": "Finance Data Quality Analyst at BNP Paribas Madrid. Ensuring data quality in financial systems.", "url": "https://to.indeed.com/aazydp8lkzhq", "source": "Indeed"},
        {"title": "Operational Support Analyst Financial Markets", "company": "Grupo Digital", "location": "Madrid", "description": "Operational Support Analyst for Financial Markets at Grupo Digital Madrid. Hybrid working.", "url": "https://to.indeed.com/aamkd9kdb6sb", "source": "Indeed"},
    ],
    "credit analyst_Barcelona_10": [
        {"title": "Strategic Finance Analyst Retail", "company": "SeQura", "location": "Barcelona", "description": "Strategic Finance Analyst with retail focus at SeQura Barcelona. Financial modelling and strategic analysis.", "url": "https://to.indeed.com/aampm9cyd9zh", "source": "Indeed"},
        {"title": "Fraud Strategy and Operations Analyst", "company": "Delivery Hero", "location": "Barcelona", "description": "Fraud Strategy and Operations Analyst at Delivery Hero Barcelona. Credit risk, fraud detection and financial analysis.", "url": "https://to.indeed.com/aasqfqmgqf6f", "source": "Indeed"},
        {"title": "Tax Compliance Junior Analyst", "company": "Delivery Hero", "location": "Barcelona", "description": "Tax Compliance Junior Analyst at Delivery Hero Barcelona. Supporting tax compliance, financial reporting and regulatory obligations.", "url": "https://to.indeed.com/aa7v4b8lbprb", "source": "Indeed"},
        {"title": "Invoice to Cash Process Analyst", "company": "Air Products", "location": "Barcelona", "description": "Invoice to Cash Process Analyst full-time at Air Products Barcelona. Managing accounts receivable and cash collection processes.", "url": "https://to.indeed.com/aa8zk8jfzzjh", "source": "Indeed"},
        {"title": "Fraud Data Analyst", "company": "Satispay", "location": "Barcelona", "description": "Fraud Data Analyst full-time role at Satispay Barcelona. Analysing financial transaction data to detect fraud patterns.", "url": "https://to.indeed.com/aal2v9mstgtf", "source": "Indeed"},
        {"title": "Senior Analyst Growth", "company": "Delivery Hero", "location": "Barcelona", "description": "Senior Analyst Growth role at Delivery Hero Barcelona. Financial analysis supporting business growth and strategy.", "url": "https://to.indeed.com/aaclk9fjzm88", "source": "Indeed"},
        {"title": "Senior Regional Operations Analyst", "company": "Delivery Hero", "location": "Barcelona", "description": "Senior Regional Operations Analyst at Delivery Hero Barcelona. Regional financial analysis and operational reporting.", "url": "https://to.indeed.com/aaldqqr8rhpy", "source": "Indeed"},
        {"title": "Graduate Business Analyst Early Careers", "company": "Delivery Hero", "location": "Barcelona", "description": "Graduate Business Analyst Early Careers programme at Delivery Hero Barcelona. Entry-level financial and business analysis.", "url": "https://to.indeed.com/aarchpm4gxdg", "source": "Indeed"},
    ],
}

cache_file = "job_cache.json"
cache = {}
if os.path.exists(cache_file):
    with open(cache_file) as f:
        cache = json.load(f)

cache.update(indeed_jobs)

with open(cache_file, "w") as f:
    json.dump(cache, f, indent=2)

print(f"Cache updated with {sum(len(v) for v in indeed_jobs.values())} Indeed Spain jobs")
print(f"Cache keys added: {list(indeed_jobs.keys())}")
