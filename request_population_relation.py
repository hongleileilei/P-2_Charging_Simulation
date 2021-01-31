import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import json
import os
from datetime import datetime, timedelta


from shapely.geometry import Point, Polygon


class relation():
    def __init__(self):
        # population and request are region-based
        self.population = {}
        self.boundaries = {}
        self.requests = {}
        self.income = {}

    def import_census(self, census_path: str, geo_path: str):

        census = pd.read_excel(census_path)
        geo = pd.read_json(geo_path)
        # Iterate rows to store population information
        for index, row in census.iterrows():
            if index == 0:
                continue
            self.population[row['GEO.id2']] = row['Population']
        
        for index, row in geo.iterrows():
            boundary = row['features']['geometry']['coordinates'][0][0].copy()
            self.boundaries[int(row['features']['properties']['GEOID'])] = boundary
        
        return

    def export_census(self, geo_path: str):
        with open(geo_path) as f:
            data = json.load(f)
        data_feats = data["features"]
        for feat in data_feats:
            feat["properties"]["census"] = self.population[int(feat["properties"]["GEOID"])]
        new_data = data.copy()
        new_data["features"] = data_feats
        with open("census_geo_map.json","w") as json_file:
            json.dump(new_data,json_file)
        return

    def import_requests(self, data_paths: str):
        request_location = []
        for files in os.listdir(data_paths):
            f = open(data_paths+'/'+files,"r")
            new_req = []
            for line in f:
                if line[1:4] == "lat":
                    new_req.append(float(line[6:-1]))
                if line[1:4] == "lng":
                    new_req.insert(0,float(line[6:-1]))
            request_location.append(new_req)
        for each_req in request_location:
            point = Point(each_req[0],each_req[1])
            for geoid in self.boundaries:
                region = Polygon(self.boundaries[geoid])
                if point.within(region):
                    if geoid not in self.requests:
                        self.requests[geoid] = 1
                    else:
                        self.requests[geoid] += 1
                else:
                    continue
        
        # Unspecified data
        for bnd_geoid in self.boundaries:
            if bnd_geoid not in self.requests:
                self.requests[bnd_geoid] = 0
        
    
    def export_requests(self, geo_path: str):
        with open(geo_path) as f:
            data = json.load(f)
        data_feats = data["features"]
        for feat in data_feats:
            feat["properties"]["req_num"] = self.requests[int(feat["properties"]["GEOID"])]
        new_data = data.copy()
        new_data["features"] = data_feats
        with open("req_geo_map.json","w") as json_file:
            json.dump(new_data,json_file)
        return
    
    def export_req_div_cen(self, geo_path: str):
        with open(geo_path) as f:
            data = json.load(f)
        data_feats = data["features"]
        for feat in data_feats:
            feat["properties"]["req_div_cecn"] = self.requests[int(feat["properties"]["GEOID"])] / self.population[int(feat["properties"]["GEOID"])]
        new_data = data.copy()
        new_data["features"] = data_feats
        with open("req_div_cen.json","w") as json_file:
            json.dump(new_data,json_file)
        return
    
    def import_income(self, income_path: str):
        income = pd.read_csv(income_path)
        headers = income.iloc[0]
        income = pd.DataFrame(income.values[1:], columns=headers)
        last_row_idx = len(income)
        income = income.drop([last_row_idx-1,last_row_idx-2])
        income = income.rename(columns={"Estimate!!Median household income in the past 12 months (in 2018 inflation-adjusted dollars)":"Median",
                                        "Margin of Error!!Median household income in the past 12 months (in 2018 inflation-adjusted dollars)":"Margin"})
        
        income = income.replace("250,000+",250000)
        income["Median"] = income["Median"].astype('int64')
        income["id"] = income["id"].str.replace("1400000US",'')
        income["id"] = income["id"].astype('int64')

        for index, row in income.iterrows():
            self.income[row["id"]] = row["Median"]

        return


    def req_div_spec(self, census_path: str, data_paths: str):
        #print("implemented")
        spec = pd.read_excel(census_path)
        header = spec.iloc[0]
        spec = pd.DataFrame(spec.values[1:],columns = header)


        spec = spec.drop(['Id', 'Geography'], axis = 1)
        spec = spec.loc[:,~spec.columns.duplicated()]
        exist = []
        for index, row in spec.iterrows():  
            if row['Id2'] not in self.requests:
                exist.append(False)
            else:  
                exist.append(True)
        
        deleted = []
        for idx in range(len(exist) - 1, -1, -1):
            if exist[idx] == False:
                deleted.append(idx)
            else:
                continue
        
        spec = spec.drop(spec.index[i] for i in deleted)
        spec = spec.reset_index(drop=True)
        req = []
        for index, row in spec.iterrows():
            req.append(self.requests[row['Id2']])
        columns = list(spec.columns)[1:]
        x_val = []
        for i in range(len(req)):
            x_val.append(i)

        hispanic_rate = []
        non_his_rate = []
        male_rate = []
        female_rate = []
        areas = []
        density = []
        req_append = []
        no_income_idx = []
        for index, row in spec.iterrows():
            if row['Id2'] not in self.income:
                no_income_idx.append(index)
        spec = spec.drop(spec.index[i] for i in no_income_idx)

        incomes = []
        for index, row in spec.iterrows():
            hispanic_rate.append(float(row['Not Hispanic or Latino:']) / float(row['Population']))
            non_his_rate.append(1 - float(row['Not Hispanic or Latino:']) / float(row['Population']))
            male_rate.append(float(row['Male:'] / float(row['Population'])))
            female_rate.append(float(row['Female:'] / float(row['Population'])))
            areas.append(Polygon(self.boundaries[row['Id2']]).area)
            density.append(self.population[row['Id2']] / Polygon(self.boundaries[row['Id2']]).area)
            req_append.append(self.requests[row['Id2']])
            incomes.append(self.income[row['Id2']])
        spec['hispanic rate'] = hispanic_rate
        spec['non hispanic rate'] = non_his_rate
        spec['area'] = areas
        spec['density'] = density
        spec['male rate'] = male_rate
        spec['female rate'] = female_rate
        spec['income median'] = incomes
        spec['request'] = req_append

        # for column in spec.columns[1:-1]:
        #     plt.title('specs of '+column+' vs request numbers')
        #     plt.scatter(spec[column],spec['request'])
        #     plt.xlabel(column)
        #     plt.ylabel('request')
        #     plt.show(block=False)
        #     plt.pause(2)
        #     plt.close()
        plt.title('income median vs request count')
        plt.scatter(spec['income median'], spec['request'])
        plt.xlabel('income')
        plt.ylabel('request')
        plt.show(block=False)
        plt.pause(5)
        plt.close()

        # for column in spec.columns[1:-2]:
        #     plt.title('specs of '+column+' vs income median')
        #     plt.scatter(spec[column],spec['income median'])
        #     plt.xlabel(column)
        #     plt.ylabel('income median')
        #     plt.show(block=False)
        #     plt.pause(2)
        #     plt.close()            

        correlation_kendall = {}
        correlation_pearson = {}
        correlation_spearman = {}
        for column in spec.columns[1:-1]:
            spec[column] = spec[column].astype('float64')
            correlation_kendall[column] = spec[column].corr(spec['request'], method = 'kendall')
            correlation_pearson[column] = spec[column].corr(spec['request'], method = 'pearson')
            correlation_spearman[column] = spec[column].corr(spec['request'], method = 'spearman')
        correlation_kendall = dict(sorted(correlation_kendall.items(),key = lambda x: x[1], reverse = True))
        correlation_pearson = dict(sorted(correlation_pearson.items(),key = lambda x: x[1], reverse = True))
        correlation_spearman = dict(sorted(correlation_spearman.items(),key = lambda x: x[1], reverse = True))
        # Kendall 
        x = []
        y = []
        for attri in correlation_kendall:
            x.append(attri)
            y.append(correlation_kendall[attri])
        plt.title("Correlation between request and attributes (Kendall)")
        plt.bar(x,y)
        plt.ylabel('correlation coefficient')
        plt.xlabel('correlation factors')
        plt.xticks(rotation=90)
        plt.show()
        # Pearson
        x = []
        y = []
        for attri in correlation_pearson:
            x.append(attri)
            y.append(correlation_pearson[attri])
        plt.title("Correlation between request and attributes (Pearson)")
        plt.bar(x,y)
        plt.ylabel('correlation coefficient')
        plt.xlabel('correlation factors')
        plt.xticks(rotation=90)
        plt.show()
        # Spearman
        x = []
        y = []
        for attri in correlation_spearman:
            x.append(attri)
            y.append(correlation_spearman[attri])
        plt.title("Correlation between request and attributes (Spearman)")
        plt.bar(x,y)
        plt.ylabel('correlation coefficient')
        plt.xlabel('correlation factors')
        plt.xticks(rotation=90)
        plt.show()




        req_time = {}

        for files in os.listdir(data_paths):
            f = open(data_paths+'/'+files,"r")
            found_create = False
            found_close = False
            new_req = []
            start_time = None
            end_time = None
            time_lapsed = float('-INF')
            for line in f:
                if line[1:7] == "status":
                    #print(line,'     ',line[10:16])
                    if line[10:16] != "Closed" and line[10:18] != "Archived":
                        break
                if line[1:4] == "lat":
                    new_req.append(float(line[6:-1]))
                if line[1:4] == "lng":
                    new_req.insert(0,float(line[6:-1]))
                if line[1:11] == 'created_at' and found_create is False:
                    if line[13:17] == 'null' or len(line) < 17:
                        break
                    else:
                        found_create=True
                    #print(line)
                        start_time = datetime.strptime(line[16:-8],'%y-%m-%dT%H:%M:%S')
                if line[1:10] == 'closed_at' and found_close is False:
                    if line[12:16] == 'null' or len(line) < 16:
                        break
                    else:
                        found_close = True
                    #print(line)
                        end_time = datetime.strptime(line[15:-8],'%y-%m-%dT%H:%M:%S')
                        if end_time is None or start_time is None:
                            break
                        else:
                            time_lapsed = end_time - start_time
                    #print(start_time,'\n',end_time,'\n',time_lapsed)
                    #print()
                if time_lapsed != float('-INF'):          
                    point = Point(new_req[0],new_req[1])
                    for geoid in self.boundaries:
                        region = Polygon(self.boundaries[geoid])
                        if point.within(region):
                            if geoid not in  req_time:
                                req_time[geoid] = []
                                req_time[geoid].append(time_lapsed)
                            else:
                                req_time[geoid].append(time_lapsed)
                        else:
                            continue
        for geoid in req_time:
            count = len(req_time[geoid])
            sumtime = sum(req_time[geoid], timedelta())
            avgtime = sumtime / count
            avgtime = pd.Timedelta(avgtime)
            avgtime = avgtime.delta / (1000000000 *60 *60 *24)
            req_time[geoid] = avgtime

        for geoid in self.boundaries:
            if geoid not in req_time:
                req_time[geoid] = np.nan

        spec = spec.drop(['request'], axis = 1)
        req_time_append = []
        for index, row in spec.iterrows():
            req_time_append.append(req_time[row['Id2']])
        spec['req time'] = req_time_append

        plt.title('income median vs request finish time')
        plt.scatter(spec['income median'], spec['req time'])
        plt.xlabel('income')
        plt.ylabel('request finishing time')
        plt.show(block=False)
        plt.pause(5)
        plt.close()

        for column in spec.columns[1:-1]:
            plt.title('specs of '+column+' vs request solving time')
            plt.scatter(spec[column],spec['req time'])
            plt.xlabel(column)
            plt.ylabel('request solving time')
            plt.show(block=False)
            plt.pause(2)
            plt.close()

        for column in spec.columns[1:-1]:
            spec[column] = spec[column].astype('float64')
            correlation_kendall[column] = spec[column].corr(spec['req time'], method = 'kendall')
            correlation_pearson[column] = spec[column].corr(spec['req time'], method = 'pearson')
            correlation_spearman[column] = spec[column].corr(spec['req time'], method = 'spearman')
        correlation_kendall = dict(sorted(correlation_kendall.items(),key = lambda x: x[1], reverse = True))
        correlation_pearson = dict(sorted(correlation_pearson.items(),key = lambda x: x[1], reverse = True))
        correlation_spearman = dict(sorted(correlation_spearman.items(),key = lambda x: x[1], reverse = True))
        # Kendall 
        x = []
        y = []
        for attri in correlation_kendall:
            x.append(attri)
            y.append(correlation_kendall[attri])
        plt.title("Correlation between request time and attributes (Kendall)")
        plt.bar(x,y)
        plt.ylabel('correlation coefficient')
        plt.xlabel('correlation factors')
        plt.xticks(rotation=90)
        plt.show()
        # Pearson
        x = []
        y = []
        for attri in correlation_pearson:
            x.append(attri)
            y.append(correlation_pearson[attri])
        plt.title("Correlation between request time and attributes (Pearson)")
        plt.bar(x,y)
        plt.ylabel('correlation coefficient')
        plt.xlabel('correlation factors')
        plt.xticks(rotation=90)
        plt.show()
        # Spearman
        x = []
        y = []
        for attri in correlation_spearman:
            x.append(attri)
            y.append(correlation_spearman[attri])
        plt.title("Correlation between request time and attributes (Spearman)")
        plt.bar(x,y)
        plt.ylabel('correlation coefficient')
        plt.xlabel('correlation factors')
        plt.xticks(rotation=90)
        plt.show()


        return        
