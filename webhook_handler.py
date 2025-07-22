import json
import pandas as pd
from datetime import datetime
import requests
import os

class MakeWebhookHandler:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or os.getenv('MAKE_WEBHOOK_URL')
        
    def process_bank_data(self, payload):
        """Process incoming bank data from Make.com"""
        try:
            # Extract data from payload
            data = {
                'date': payload.get('date', datetime.now().isoformat()),
                'revenue': payload.get('revenue', 0),
                'costs': payload.get('costs', 0),
                'transactions': payload.get('transactions', [])
            }
            
            # Calculate metrics
            data['profit'] = data['revenue'] - data['costs']
            data['margin'] = (data['profit'] / data['revenue'] * 100) if data['revenue'] > 0 else 0
            
            return data
            
        except Exception as e:
            print(f"Error processing bank data: {e}")
            return None
    
    def update_excel_file(self, data, year, month):
        """Update Excel file with new data"""
        filename = f"Resultado Financeiro - {year}.xlsx"
        
        try:
            # Read existing Excel or create new
            try:
                df = pd.read_excel(filename, sheet_name='Resultado')
            except:
                # Create new structure if file doesn't exist
                df = pd.DataFrame(columns=['Unnamed: 0'] + [m for m in ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']])
                df['Unnamed: 0'] = ['FATURAMENTO', 'CUSTOS VARIÁVEIS', 'LUCRO']
            
            # Map month number to column name
            month_map = {1: 'JAN', 2: 'FEV', 3: 'MAR', 4: 'ABR', 5: 'MAI', 6: 'JUN',
                        7: 'JUL', 8: 'AGO', 9: 'SET', 10: 'OUT', 11: 'NOV', 12: 'DEZ'}
            
            month_col = month_map.get(month)
            
            if month_col:
                # Update values
                df.loc[df['Unnamed: 0'] == 'FATURAMENTO', month_col] = data['revenue']
                df.loc[df['Unnamed: 0'] == 'CUSTOS VARIÁVEIS', month_col] = data['costs']
                df.loc[df['Unnamed: 0'] == 'LUCRO', month_col] = data['profit']
                
                # Save updated Excel
                with pd.ExcelWriter(filename, mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name='Resultado', index=False)
                
                return True
                
        except Exception as e:
            print(f"Error updating Excel: {e}")
            return False
    
    def send_to_make(self, data):
        """Send processed data back to Make.com"""
        if not self.webhook_url:
            print("No webhook URL configured")
            return False
            
        try:
            response = requests.post(
                self.webhook_url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending to Make.com: {e}")
            return False
    
    def create_make_template(self):
        """Create Make.com scenario template"""
        template = {
            "name": "Marine Seguros Financial Sync",
            "description": "Automated financial data synchronization",
            "modules": [
                {
                    "type": "webhook",
                    "name": "Receive Bank Data",
                    "config": {
                        "method": "POST",
                        "headers": ["Content-Type: application/json"]
                    }
                },
                {
                    "type": "plaid",
                    "name": "Get Bank Transactions",
                    "config": {
                        "account": "{{webhook.account_id}}",
                        "start_date": "{{webhook.start_date}}",
                        "end_date": "{{webhook.end_date}}"
                    }
                },
                {
                    "type": "transformer",
                    "name": "Process Transactions",
                    "config": {
                        "revenue": "{{sum(plaid.transactions[category='income'].amount)}}",
                        "costs": "{{sum(plaid.transactions[category='expense'].amount)}}"
                    }
                },
                {
                    "type": "http",
                    "name": "Send to Marine App",
                    "config": {
                        "url": "{{app_webhook_url}}",
                        "method": "POST",
                        "body": {
                            "year": "{{formatDate(now, 'YYYY')}}",
                            "month": "{{formatDate(now, 'M')}}",
                            "revenue": "{{transformer.revenue}}",
                            "costs": "{{transformer.costs}}",
                            "transactions": "{{plaid.transactions}}"
                        }
                    }
                }
            ],
            "schedule": {
                "type": "daily",
                "time": "09:00"
            }
        }
        
        return json.dumps(template, indent=2)