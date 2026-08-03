def reverse_number(num):
    """
    This function takes an integer number as input and returns its reverse.
    
    Parameters:
    num (int): The number to be reversed.
    
    Returns:
    int: The reversed number.
    """
    # Convert the number to string, reverse it, and convert back to integer
    reversed_num = int(str(num)[::-1])
    return reversed_num