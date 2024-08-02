class Solution:
	def merge(arr, low, mid, high):
		left = low
		right = mid + 1
		temp = []
		while (left <= mid and low < = mid)
			if (arr[low] <= arr[mid]:
				temp.append(arr[left])
				left += 1
			else:
				temp.append(arr[right])
				right +=1
		
		while left <= mid:
			temp.append(arr[left])
			left +=1
		
		while right <= high:
			temp.append(arr[right])
			right +=1
			
		for i in range(low, high):
			arr[low - i] = temp[i]

		


	def mergeSort(arr, low, high):
        if left <= high:
            mid = (low+high)//2
            mergeSort(arr, low, mid)
            mergeSort(arr,mid+1,high)
            merge(arr,low,mid,high)
		
		