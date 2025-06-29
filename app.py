from flask import Flask, jsonify, request
from flask_cors import CORS
from sec_api import FormAdvApi
import json
import pandas as pd

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend connection

# Initialize SEC API
formAdvApi = FormAdvApi("a9b681b529945c800d40eb81d3064fd7f0e3ef698c72fc30c0b010a1605d8ffb")

def get_filings(query):
    from_param = 0
    size_param = 20
    all_filings = []

    for i in range(20):
        query['from'] = from_param
        query['size'] = size_param
        
        response = formAdvApi.get_firms(query)
        filings = response['filings']

        if len(filings) == 0:
            break

        all_filings.extend(filings)
        from_param += size_param

    return pd.json_normalize(all_filings)

def format_item_5e(filings):
    filtered_columns = filings.filter(like='FormInfo.Part1A.Item5E')
    additional_columns = filings[['Info.BusNm', 'Info.FirmCrdNb', 'FormInfo.Part1A.Item5F.Q5F2C']]
    additional_columns = additional_columns.rename(columns={'Info.BusNm': 'Adviser', 'Info.FirmCrdNb': 'CRD', 'FormInfo.Part1A.Item5F.Q5F2C': "AUM ($)"})
    selected_columns = pd.concat([additional_columns, filtered_columns], axis=1)
    selected_columns.columns = selected_columns.columns.str.replace(r'^FormInfo\.Part1A\.Item5E\.', '', regex=True)
    
    selected_columns = selected_columns.rename(columns={'Q5E1': 'Percent of Assets', 'Q5E2': 'Hourly Fees', 'Q5E3': 'Subscription Fees', 'Q5E4': 'Fixed Fees', 'Q5E5': 'Commissions', 'Q5E6': 'Performance', 'Q5E7': 'Other Compensation Arrangements'})
    selected_columns.insert(0, 'Index', range(1, len(selected_columns) + 1))
    selected_columns["AUM ($)"] = selected_columns["AUM ($)"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else x)

    return selected_columns

@app.route('/api/query', methods=['POST'])
def execute_query():
    try:
        data = request.json
        query_type = data.get('queryType', 'compensation')
        
        if query_type == 'compensation':
            compensation_query = {
                "query": "FormInfo.Part1A.Item5E.Q5E1:Y AND Info.FirmCrdNb:[1 TO 152000]",
                "sort": [{ "Filing.Dt": { "order": "desc" }}]
            }
            
            filings = get_filings(compensation_query)
            formatted_data = format_item_5e(filings)
            
            # Convert to list of dictionaries for JSON response
            result = formatted_data.to_dict('records')
            
            return jsonify({
                'success': True,
                'data': result,
                'total': len(result)
            })
            
        elif query_type == 'aum':
            aum_min = data.get('aumMin', 1)
            aum_max = data.get('aumMax', 780000000)
            emp_min = data.get('employeeMin', 1)
            emp_max = data.get('employeeMax', 50)
            
            aum_query = {
                "query": f"FormInfo.Part1A.Item5F.Q5F2C:[{aum_min} TO {aum_max}] AND FormInfo.Part1A.Item5A.TtlEmp:[{emp_min} TO {emp_max}]",
                "sort": [{ "Info.FirmCrdNb": { "order": "desc" }}]
            }
            
            filings = get_filings(aum_query)
            
            # Process AUM data
            sort_column = 'FormInfo.Part1A.Item5F.Q5F2C'
            sorted_by_aum = filings.sort_values(sort_column, ascending=False)
            
            selected_columns = sorted_by_aum[[
                sort_column,
                'Info.BusNm', 
                'Info.FirmCrdNb', 
                'FormInfo.Part1A.Item5F.Q5F2F',
                'FormInfo.Part1A.Item5A.TtlEmp'
            ]].rename(columns={
                'FormInfo.Part1A.Item5F.Q5F2C': 'AUM ($)', 
                'Info.FirmCrdNb': 'CRD',
                'Info.BusNm': 'Name',
                'FormInfo.Part1A.Item5F.Q5F2F': 'Accounts',
                'FormInfo.Part1A.Item5A.TtlEmp': 'Employees' 
            })
            
            selected_columns['AUM per Account'] = selected_columns['AUM ($)'].astype(int) / selected_columns['Accounts'].astype(int)
            selected_columns.insert(0, 'Index', range(1, len(selected_columns) + 1))
            
            # Format numbers
            for col in ['AUM per Account', 'AUM ($)', 'Accounts', 'Employees']:
                selected_columns[col] = selected_columns[col].apply(lambda x: f"{int(x):,}")
            
            result = selected_columns.to_dict('records')
            
            return jsonify({
                'success': True,
                'data': result,
                'total': len(result)
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=3000)