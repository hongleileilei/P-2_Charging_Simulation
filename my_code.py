import pandas as pd
import matplotlib.pyplot as plt
import math
from shapely.geometry import Point, Polygon

class power_process():
	def __init__(self, path):
		self.file = open(path, 'r')
		self.lines = self.file.readlines()


	def power_preprocess(self):
		temp_memory = {}
		for i in range(len(self.lines)):
			self.lines[i] = self.lines[i].replace('POLYGON((','')
			self.lines[i] = self.lines[i].replace('))','')
			region_name = i+1
			coordinates = self.lines[i].split(',')
			for coordinate in coordinates:
				coordinate = coordinate.split()
				coordinate[0] = 0 - float(coordinate[0][1:])
				coordinate[1] = float(coordinate[1])
			temp_memory[region_name] = coordinates
			#print(line)
		return temp_memory

class taxi_process():
	def __init__(self, path):
		self.df = pd.read_csv(path,nrows=10000000)

	def taxi_preprocess(self):
		del self.df['VendorID']
		del self.df['passenger_count']
		del self.df['payment_type']
		del self.df['store_and_fwd_flag']
		del self.df['extra']
		del self.df['mta_tax']
		del self.df['tip_amount']
		del self.df['tolls_amount']
		del self.df['total_amount']
		# We only concerned about taxi within the region on NYC
		self.df = self.df[self.df.RateCodeID == 1]
		del self.df['RateCodeID']
		print("\nWe only consider data from date 2015-01-05")
		self.df = self.df[self.df.tpep_pickup_datetime.str.contains('2015-01-05')]
		self.df = self.df[self.df.tpep_dropoff_datetime.str.contains('2015-01-05')]
		print(self.df.head(10))
		print("\nWe now move unwanted date info, only leaves time")
		self.df['tpep_pickup_datetime'] = self.df['tpep_pickup_datetime'].map(lambda x: x.lstrip('2015-01-05').strip())
		self.df['tpep_dropoff_datetime'] = self.df['tpep_dropoff_datetime'].map(lambda x: x.lstrip('2015-01-05').strip())
		self.df = self.df.sort_values(by=['tpep_pickup_datetime'])
		#print(self.df.head(10),'\n')
		self.df['pickup_hour'] = self.df['tpep_pickup_datetime'].apply(lambda s: int(s.split(':')[0]))
		self.df['pickup_min'] = self.df['tpep_pickup_datetime'].apply(lambda s: int(s.split(':')[1]))
		self.df['pickup_sec'] = self.df['tpep_pickup_datetime'].apply(lambda s: int(s.split(':')[2]))
		self.df['dropoff_hour'] = self.df['tpep_dropoff_datetime'].apply(lambda s: int(s.split(':')[0]))
		self.df['dropoff_min'] = self.df['tpep_dropoff_datetime'].apply(lambda s: int(s.split(':')[1]))
		self.df['dropoff_sec'] = self.df['tpep_dropoff_datetime'].apply(lambda s: int(s.split(':')[2]))
		del self.df['tpep_pickup_datetime']
		del self.df['tpep_dropoff_datetime']
		print(self.df.tail(10),'\n')
		return self.df

	def taxi_df_info(self):
		print(self.df.info())
		return None


	def taxi_counting(self):
		self.df['pickup_time'] = self.df.apply(lambda x: x.pickup_hour * 60 + x.pickup_min, axis=1)
		self.df['dropoff_time'] = self.df.apply(lambda x: x.dropoff_hour * 60 + x.dropoff_min, axis = 1)

		df_pickup_based = self.df.sort_values(by=['pickup_time'])
		df_dropoff_based = self.df.sort_values(by=['dropoff_time'])

		counts = []
		time = []
		count = 0
		for minute in range(0, 24*60):
			count += len(df_pickup_based[df_pickup_based['pickup_time'] == minute])
			count -= len(df_dropoff_based[df_dropoff_based['dropoff_time'] == minute])
			counts.append(count)
			time.append(minute)
		#plt.figure()
		#plt.plot(time,counts,color='red')
		#plt.show()
		print('Taxi number = Taxi number(prev) + num_pickup - num_dropoff')
		taxi_count = max(counts)
		print('Taxi number: ',taxi_count)
		del self.df['pickup_time']
		del self.df['dropoff_time']
		return taxi_count


	def taxi_region(self, regions):
		pickup_region = []
		dropoff_region = []
		polygons = {}

		for region_idx in regions:
			vertices = []
			for coors in regions[region_idx]:
				coor_str = coors.split()
				temp = (float(coor_str[0]), float(coor_str[1]))
				vertices.append(temp)
			polygons[region_idx] = Polygon(vertices)


		########################################
		# Tester
		########################################
		plt.figure()
		for poly in polygons:
			x,y = polygons[poly].exterior.xy
			plt.plot(x,y)
		plt.show()

		########################################
		# Tester End
		########################################

		for index, row in self.df.iterrows():
			coor = []
			find_region = False
			coor.append(row['pickup_longitude'])
			coor.append(row['pickup_latitude'])
			point = Point(coor[0],coor[1])

			for polygon_idx in polygons:
				if point.within(polygons[polygon_idx]) == True:
					pickup_region.append(polygon_idx)
					find_region = True
					break
				else:
					continue
			if find_region == False:
				pickup_region.append(-1)

			find_region = False
			coor = []
			coor.append(row['dropoff_longitude'])
			coor.append(row['dropoff_latitude'])
			point = Point(coor[0],coor[1])

			for polygon_idx in polygons:
				if point.within(polygons[polygon_idx]) == True:
					dropoff_region.append(polygon_idx)
					find_region = True
					break
				else:
					continue
			if find_region == False:
				dropoff_region.append(-1)
		#print(len(dropoff_region))
		#print(len(pickup_region))
		#print(self.df.count())			
		self.df["pickup_region"] = pickup_region
		self.df["dropoff_region"] = dropoff_region

		self.df = self.df[self.df.pickup_region != -1]
		self.df = self.df[self.df.dropoff_region != -1]
		print(self.df.head(10))
		print(self.df.tail(10))
		return None

class Process(power_process, taxi_process):
	def __init__(self, power_path, taxi_path):
		self.power = power_process(power_path)
		self.taxi = taxi_process(taxi_path)
		self.taxi_count = 0
		self.regions = {}

	def preprocess(self):
		#self.power.power_preprocess()
		self.taxi.taxi_preprocess()

		## After preprocessing the data, we calculate the taxi count first
		self.regions = self.power.power_preprocess()
		self.taxi_count = self.taxi.taxi_counting()
		#print(self.regions)
		## add pickup and dropoff regions respectively to the df
		self.taxi.taxi_region(self.regions)





def main():
	taxi_path = 'taxi_data.csv'
	power_path = 'e_bound'

	process = Process(power_path,taxi_path)
	process.preprocess()



if __name__ == "__main__":
	main()