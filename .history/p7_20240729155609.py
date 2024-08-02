class Solution:
	def partition(self, arr, low, high):
		pivot = arr[high]
		i=0
		for j in range(low,high):
			if arr[j] < pivot:
				i+=1
			arr[j], arr[i] = arr[i], arr[j]
		
		arr[i+1], arr[high] = arr[i+1], arr[high]
		
		return i+1
			
			
	def quickSort(self, arr,low,high):
		if low < high:
			p = self.partition(arr, low, high)
			self.quickSort(arr, low, p-1)
			self.quickSort(arr,p+1,high)