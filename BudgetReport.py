import re
import json
import gspread
import pandas as pd
from plotly.offline import download_plotlyjs,init_notebook_mode,plot,iplot
import cufflinks as cf
from oauth2client.service_account import ServiceAccountCredentials

init_notebook_mode(connected=True)
cf.go_offline()

class Budget(object):
    budget_items = {}
        
    #empty vars
    categories = None
    Total = None
    
    def __init__(self, csvfile, gsheet, format=True):
        self.csvfile = csvfile
        self.gsheet = gsheet
        # Load columns 0,2,3 and assign headers
        self.df = pd.read_csv(self.csvfile,usecols=[0,2,3], names=['date', 'amount', 'vendor'])
        # Convert to datetime objects
        self.df['date'] = pd.to_datetime(self.df['date'])
        
        with open("budgetitems.json", "r") as b_items:
            Budget.budget_items = json.load(b_items)
        
        if format:
            self.format()
            
    def format(self):
       
        self.df.fillna(value='Missing',inplace=True)
        self.df=self.df[self.df['amount'] < 0]
        self.df['amount'] = self.df['amount'].apply(lambda x: x * -1)
        self.df['vendor'] = self.df['vendor'].apply(self._format_vendor)
        self.df['category'] = self.df['vendor'].apply(self._classify_vendor).astype('category')
        # If gas category is > $50, recategorize as tobacco
        self.df['category'] = self.df.apply(lambda x: 'tobacco' if x.category == 'gas' and  x.amount > 50 else x.category, 1)
        
        self.df.set_index(['category','date'],inplace=True)
        self.df.sort_index(inplace=True)
        
        # Hold data
        budgetvals = {}
        totals = {}
        
        # Google sheets
        scope = ['https://spreadsheets.google.com/feeds']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        client = gspread.authorize(creds)
        # Read 'Budget' sheet from Google sheets, read first worksheet
        sheet = client.open(self.gsheet).sheet1
        
        # Zip from 2x2 diff columns from Sheets
        budget = zip(sheet.col_values(1),sheet.col_values(3))
        budget1 = zip(sheet.col_values(9),sheet.col_values(11))
        
        # Iterate imported budget columns
        for b in budget, budget1:
            for cat,amount in b:
                # Skip if category is empty
                if not cat:
                    next
                else:
                    # Assign lowered budget categories from google with parsed $ amount
                    # Removes $ and ,
                    budgetvals[cat.lower()] = float(amount[1:-3].replace(',',''))
              
        # Convert category index to set
        for val in set(self.df.index.get_level_values('category')):
            # Assign tuple of category sum, budget amount, and diff (category - budget)
            totals[val] = (self.df.loc[val].sum().amount, budgetvals.get(val,0), self.df.loc[val].sum().amount - budgetvals.get(val,0))

        # Add total values as column
        Budget.Total = pd.DataFrame.from_dict(totals, orient='index')
        Budget.Total.sort_index(inplace=True)
        Budget.Total.columns = [ 'Expense','Budget','Diff' ]
        
    def _format_vendor(self, vendor):
        
        pattern = re.compile(r'\b[a-z]+\b',re.I)
        
        # Manual Corrections
        for key in Budget.budget_items['corrections'].keys():
            if key in vendor:
                vendor = Budget.budget_items['corrections'][key]
            
        words = re.findall(pattern,vendor)
        
        for idx,val in enumerate(words):
            if val.upper() in Budget.budget_items['ignored']:
                words.pop(idx)
            elif len(words[-1]) <= 2:
                words.pop(-1)
        if len(words) > 0:
            return ' '.join(words)
        return vendor
        
    def vendors(self):
        return self.df['vendor'].unique()
                
    def _classify_vendor(self, vendor):        
        Budget.categories = [x for x in Budget.budget_items['categories'].keys()]
        for k,v in Budget.budget_items['categories'].items():
            for val in v:
                if val in vendor.upper():
                    return k
        return "misc"

    def graph(self):
        self.Total.iplot(kind="bar")
        

