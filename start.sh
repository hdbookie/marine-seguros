#!/bin/bash
export PYTHONPATH=/app:$PYTHONPATH
streamlit run app_refactored.py --server.port=$PORT --server.address=0.0.0.0