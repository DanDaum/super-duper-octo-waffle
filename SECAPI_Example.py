
from sec_api import FormAdvApi
import json
import pandas as pd



formAdvApi = FormAdvApi("a9b681b529945c800d40eb81d3064fd7f0e3ef698c72fc30c0b010a1605d8ffb")

search_query_firms = {
    "query": "Info.FirmCrdNb:361",
    "from": "0",
    "size": "10"
}

search_query_individuals = {
    "query": "Info.indvlPK:7696734",
    "from": "0",
    "size": "50"
}
aum_query = {
  "query": "FormInfo.Part1A.Item5F.Q5F2C:[1 TO 780000000] AND FormInfo.Part1A.Item5A.TtlEmp:[1 TO 50]",
  "sort": [{ "Info.FirmCrdNb": { "order": "desc" }}]
}



firm_advisers_query = {
    "query": "Info.FirmCrdNb:151980",
    "from": "0",
    "size": "1",
    "sort": [{"Info.FirmCrdNb": {"order": "desc"}}],
}


#response_firms_1 = formAdvApi.get_firms(firm_advisers_query)
#print('Total matches found:', response_firms_1['total']['value'])
#print('Filing')
#print('------')
#print(json.dumps(response_firms_1['filings'], indent=2))


#response_brochures   = formAdvApi.get_brochures(151980)
#print(json.dumps(response_brochures, indent=2))


def get_filings(query):
  from_param = 0
  size_param = 20
  all_filings = []

  for i in range(20):  # Limit to 1000 iterations to prevent infinite loop
    query['from'] = from_param
    query['size'] = size_param
    
    response = formAdvApi.get_firms(query)
    filings = response['filings']

    if len(filings) == 0:
      break

    all_filings.extend(filings)

    from_param += size_param
    
    print("got a filing")
    
    json.dumps(response['filings'], indent=2)
  return pd.json_normalize(all_filings)

#aum_filings = get_filings(aum_query)
#print('Advisers with $1bn+ AUM:', len(aum_filings))
#print(aum_filings.iloc[:, :3])


compensation_query = {
    "query": "FormInfo.Part1A.Item5E.Q5E1:Y AND Info.FirmCrdNb:[1 TO 152000]",
    "sort": [{ "Filing.Dt": { "order": "desc" }}]
}



def format_item_5e(filings):
  filtered_columns = filings.filter(like='FormInfo.Part1A.Item5E')
  additional_columns = filings[['Info.BusNm', 'Info.FirmCrdNb', 'FormInfo.Part1A.Item5F.Q5F2C']]
  additional_columns = additional_columns.rename(columns={'Info.BusNm': 'Adviser', 'Info.FirmCrdNb': 'CRD', 'FormInfo.Part1A.Item5F.Q5F2C': "AUM ($)"})
  selected_columns = pd.concat([additional_columns, filtered_columns], axis=1)
  selected_columns.columns = selected_columns.columns.str.replace(r'^FormInfo\.Part1A\.Item5E\.', '', regex=True)
  
  #Update Titles in columns 
  selected_columns = selected_columns.rename(columns={'Q5E1': 'Percent of Assets', 'Q5E2': 'Hourly Fees', 'Q5E2': 'Hourly Fees', 'Q5E3': 'Subscription Fees', 'Q5E4': 'Fixed Fees', 'Q5E5': 'Commissions', 'Q5E6': 'Performance', 'Q5E7': 'Other Compensation Arrangements'})


  #Add Index column
  selected_columns.insert(0, 'Index', range(1, len(selected_columns) + 1))
  
  
  #Format AUM Column
  selected_columns["AUM ($)"] = selected_columns["AUM ($)"].apply(lambda x: f"{int(x):,}" if pd.notna(x) else x)

  return selected_columns



form_advs_filtered_by_compensation = get_filings(compensation_query)
print('Form ADVs filtered by compensation arrangements')
print('-----------------------------------------------')
print('Number of Form ADVs found:', len(form_advs_filtered_by_compensation))
print(format_item_5e(form_advs_filtered_by_compensation).to_string(index=False))



"""


# Sort by AUM
sort_column = 'FormInfo.Part1A.Item5F.Q5F2C'
sorted_by_aum = aum_filings.sort_values(sort_column, ascending=False)

# Select and rename
sorted_by_aum = sorted_by_aum[[
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

# Compute AUM per account
sorted_by_aum['AUM per Account'] = sorted_by_aum['AUM ($)'].astype(int) / sorted_by_aum['Accounts'].astype(int)

# Format numbers
columns_to_convert = ['AUM per Account', 'AUM ($)', 'Accounts', 'Employees']
for col in columns_to_convert:
    sorted_by_aum[col] = sorted_by_aum[col].apply(lambda x: f"{int(x):,}")

# Drop first row (bad AUM)
#sorted_by_aum = sorted_by_aum.drop(sorted_by_aum.index[0]).reset_index(drop=True)

# Get top 3
top_20 = sorted_by_aum.head(20)

# Output
print('Queried Firms')
print('---------------------------')
print(top_20)

"""



