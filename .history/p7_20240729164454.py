class Solution:
	def partition(self, arr, low, high):
		pivot = arr[high]
		i=low-1
		for j in range(low,high):
			if arr[j] < pivot:
				i+=1
				arr[j], arr[i] = arr[i], arr[j]
		
		arr[i+1], arr[high] = arr[high], arr[i+1]
		
		return i+1
			
			
	def quickSort(self, arr,low,high):
		if low < high:
			p = self.partition(arr, low, high)
			self.quickSort(arr, low, p-1)
			self.quickSort(arr,p+1,high)
		return
	
    
    def findUnion(self, arr1, arr2):
		i,j=0,0
		unionset = []
		
		while i<len(arr1) and j<len(arr2):
			if arr1[i] <= arr2[j]:
				if len(unionset) == 0 or unionset[-1] != arr1[i]:
					unionset.append(arr1[i])
				i+=1
			else:
				if len(unionset) == 0 or unionset[-1] != arr2[j]:
					unionset.append(arr2[j])
				j+=1
				
		while i < len(arr1):
			unionset.append(arr1[i])
			i+=1
		
		while j < len(arr2):
			unionset.append(arr[j])
			j+=1
		
		return arr