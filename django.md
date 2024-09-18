Ravi Kant Gautam 

class Publisher(models.Model):
    name = models.CharField(max_length=100)


class Book(models.Model):
    name = models.CharField(max_length=300)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    rating = models.FloatField()
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)


1. # Max price across all books

    Books.objects.aggregate(max(‘price’)).price


2. # The top 5 publishers, in order by number of books.
    Publisher.objects.annotate(number_of_books=Count(‘books’).order(‘-number_of_books’)[:5]




Q  = or and group

# find out the average rating of books written by each publisher
    Publisher.objects.filter(Q(rating__gt=2)|~Q(rating__lt=3)))



def do_twice(func, arg, kwargs):
	Def wrap():
		func(arg,kwarg)
		func(arg,kwarg)

	Return wrap

@do_twice
def greet(name):
	print(name)


Def func_series():
	For i in range(1,5):
		Yield i

next(func_series())




Given the head of a singly linked list, reverse the list, and return the reversed list.

Example 1:
Input: head = [1,2,3,4,5]
Output: [5,4,3,2,1]

Example 2:
Input: head = [1,2]
Output: [2,1]


class Node: 
  
    # Constructor to initialize the node object 
    def __init__(self, data): 
        self.data = data 
        self.next = None
  
  
class LinkedList: 
  
    # Function to initialize head 
    def __init__(self): 
        self.head = None
   
    # Function to insert a new node at the beginning 
    def push(self, new_data): 
        new_node = Node(new_data) 
        new_node.next = self.head 
        self.head = new_node 
 
   # Function to reverse the linked list 
    def reverse(self): 	
	    While self.head:
		    Self.head.head =self.head
		    Self.head.data = data
            Self.head = None



Student :





StudentCourse 




Select * from StudentCourse as sc left join Student as s on sc.roll_no = s.roll_no;
