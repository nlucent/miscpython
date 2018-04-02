import numpy as np
import pandas as pd
import matplotlib as plt
from plotly.offline import download_plotlyjs,init_notebook_mode,plot,iplot
import cufflinks as cf
import re

%matplotlib inline
init_notebook_mode(connected=True)
cf.go_offline()

class Amex(object):
    ignored = ["AK","AL","AR","AZ","CA","CO","CT","DC","DE","FL","GA","GU","HI","IA",
                  "ID", "IL","IN","KS","KY","LA","MA","MD","ME","MH","MI","MN","MO","MS",
                  "MT","NC","ND","NE","NH","NJ","NM","NV","NY", "OH","OK","OR","PA","PR",
                  "PW","RI","SC","SD","TN","TX","UT","VA","VI","VT","WA","WI","WV","WY",
                  "SPGS", "SPRI", "APP", "BILL","COM", "WWW","STORE","SPRINGS","COLORADO"]
    categories = None
    Total = None
    
    def __init__(self, csvfile="Amex March.csv",format=True):
        self.csvfile = csvfile
        self.df = pd.read_csv(self.csvfile,usecols=[0,2,3], names=['date', 'amount', 'vendor'])
        self.df['date'] = pd.to_datetime(self.df['date'])
        if format:
            self.format()
            
    def format(self):
        self.df.fillna(value='Missing',inplace=True)
        self.df=self.df[self.df['amount'] < 0]
        self.df['amount'] = self.df['amount'].apply(lambda x: x * -1)
        self.df['vendor'] = self.df['vendor'].apply(self._format_vendor)
        self.df['category'] = self.df['vendor'].apply(self._classify_vendor).astype('category')
         
        self.df.set_index(['category','date'],inplace=True)
        self.df.sort_index(inplace=True)
        
        totals = {}
        
        for val in set(self.df.index.get_level_values('category')):
            totals[val] = self.df.loc[val].sum().amount
            
        Amex.Total = pd.DataFrame.from_dict(totals, orient='index')
        Amex.Total.sort_index(inplace=True)
        Amex.Total.columns = [ Amex.Total.sum()[0] ]
        
    def _format_vendor(self, vendor):
        
        pattern = re.compile(r'\b[a-z]+\b',re.I)
        
        # Manual Corrections
        if '5GUYS' in vendor:
            vendor = 'FIVE GUYS'
        elif 'AT&T' in vendor:
            vendor = 'ATT MOBILE'
            
        words = re.findall(pattern,vendor)
        
        for idx,val in enumerate(words):
            if val.upper() in Amex.ignored:
                words.pop(idx)
            elif len(words[-1]) <= 2:
                words.pop(-1)
        if len(words) > 0:
            return ' '.join(words)
        return vendor
    
    def vendors(self):
        return self.df['vendor'].unique()
    
    def _classify_vendor(self, vendor):
        categories = { 'groceries': ['HANNAFORD', 'SHAW', 'SAFEWAY', 'WHOLEFDS', 'MARKET BASKET', 'KING SOOPER'],
                      'gas': ['KUM GO', 'BP','SHELL', 'CONOCO', 'SONOCO', 'CIRCLE K'],
                      'restaurants': ['SUBWAY','HARDEE'],
                      'amazon': ['AMAZON'],
                      'house': ['ACEHARD','HOME DEPOT', 'LOWE'],
                      'phone': ['ATT', 'VONAGE'],
                      'dog': ['VET', 'PETSMART', 'PETCO'],
                      'health': ['HOSPITAL','MEDICINE','CVS', 'WALGREEN'],
                      'entertainment': ['TICKETMASTER','SIRIUS', 'NETFLIX'],
                      'apple': ['IPHONE', 'ITUNES'],
                      'trash': ['BESTWAY'],
                      'paypal': ['PAYPAL'],
                      'shopping': ['MACY','MARSHALL', 'T J MAX', 'TARGET'],
                      'travel': ['TRAVEL', 'HORSTAX','TOLL', 'UNITED', 'SOUTHWEST', 'AIR CANADA'],
                      'subscriptions': ['TRANSUNION', 'MEMBERSHIP','MAKE MAG','ROADRUNNER'],
                      'education': ['UNIV', 'COLLEGE', 'UNDRGR', 'U BOULD','GREAT COURSES','GREATCOURSES','UDEMY'],
                      'motorcycle': ['BMW', 'TWISTED THROTTLE','REVZILLA','CYCLE GEAR'],
                      'cable': ['COMCAST'],
                      'uhaul': ['UHAUL', 'U HAUL'],
                      'it': ['AUTODESK','RACKSPACE'],
                      'vehicle': ['MOTOR VEHICLE', 'PEPBOY', 'TIRE WAREHOUSE','AUTOZONE','ADVANCE AUTO'],
                      'shipping':['USPS', 'THE UPS ','FEDEX'],
                      'outdoor': ['REI','YETI'],
                      'charity': ['WPY','AUTISM'],
                      'utilities': ['COS UTILITIES']
                     }
        
        
        Amex.categories = [x for x in categories.keys()]
        for k,v in categories.items():
            for val in v:
                if val in vendor.upper():
                    return k
        return "misc"
            
        
amex = Amex(format=True) 
