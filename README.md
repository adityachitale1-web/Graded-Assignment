# UrbanMart Sales Dashboard (Synthetic Data)

This project generates a synthetic UrbanMart transactional dataset and provides:
- A console analysis script (`urbanmart_analysis.py`) for basic checks
- A Streamlit dashboard (`app.py`) answering:
  1) best performing product categories
  2) sales variation across stores/days
  3) most valuable customers

## Run locally
```bash
pip install -r requirements.txt
python urbanmart_analysis.py
streamlit run app.py
