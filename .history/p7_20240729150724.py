class Solution:
	def merge(self, arr, low, mid, high):
		left = low
		right = mid + 1
		temp = []
		while (left <= mid and right <= high):
			if (arr[low] <= arr[right]):
				temp.append(arr[left])
				left += 1
			else:
				temp.append(arr[right])
				right += 1

		while left <= mid:
			temp.append(arr[left])
			left += 1

		while right <= high:
			temp.append(arr[right])
			right += 1

		for i in range(low, high+1):
			arr[i] = temp[i-low]

	def mergeSort(self, arr, low, high):
		if low <= high:
			mid = (low+high)//2
			self.mergeSort(arr, low, mid)
            self.mergeSort(arr,mid+1,high)
            self.merge(arr,low,mid,high)
		
		