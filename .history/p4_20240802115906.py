class Solution:
    '''
    Design an algorithm to encode a list of strings to a single string. The encoded string is then decoded back to the original list of strings.

    Please implement encode and decode
    '''

    def encode(self, strs) -> str:
        res = ""
        for s in strs:
            res += str(len(s)) + "#" + s
        return res

    def decode(self, s: str):
        res = []
        i = 0
        
        while i < len(s):
            j = i
            while s[j] != '#':
                j += 1
            length = int(s[i:j])
            i = j + 1
            j = i + length
            res.append(s[i:j])
            i = j
            
        return res
    
# s = Solution()
# result = s.encode(["neet","code","love","you"]) # "x"
# print(result)
# result = s.decode(result) # ["neet","code","love","you"]
# print(result)



def plusOne(digits):
    output = "".join([str(i) for i in digits])
    output = str(int(output) + 1)
    return [int(i) for i in output]
