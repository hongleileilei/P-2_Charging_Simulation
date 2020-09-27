# My Code Design

## Design
In this project, we want to utilize given NYC yellow taxi data to simulate the smart grid charging algoirthm

## Updates
09/20: I have done calculating the max value of pickup and dropoff count in a minute-based conditions. In current situation, we only need to manipulate day 1 and in self-test, day 1 data only exists in the first 1M data. So currently We only read first 1M data from the csv.

09/21: Remove commentified codes, add additional classes for electricity data and top level class 

09/26: Using third party library deals with taxi allocation problem. 

09/26: We removed data that contains region with index -1, which means is not inside the 38 blocks we define


## Notice
09/20: Pay attention if we want to import all csv files, which have about 194M rows. Be aware of the memory usage.

09/26: In using the library, we met the problem that there are some taxi that either its pickup region or dropoff region or both of them are outside of the given 38 region polygons and we annotate these regions as -1. In addition, there are also some region can be fit in more than one region and for that kind of situation, we consider the very first region that matches the point as its region.

09/26: Appendix: How find this special cases:

	   pseudo-code 1:
	   Node exists
	   for region in regions:
	       if Node.within(region):
	           pickup_region.append(region_index)
	       else:
	           continue


	   pseudo-code 2:
	   Node exists
	   find_region = False
	   for region in regions:
	       if Node.within(region):
	           pickup_region.append(region_index)
	           find_region = True
	       else:
	           continue
	   if find_region is False:
	       pickup_region.append(-1)

	   pseudo-code 3:
	   Node exists
	   find_region = False
	   for region in regions:
	       if Node.within(region):
	           pickup_region.append(region_index)
	           find_region = True
	           break
	       else:
	           continue
	   if find_region is False:
	       pickup_region.append(-1)

For code1, we have length:

initial data: 349351 rows

pickup_region: 305638 rows

For code2, we have length:

initial data: 349351 rows

pickup_region: 350908 rows

For code3, we have length:

initial data: 349351 rows

pickup_region: 349351 rows


