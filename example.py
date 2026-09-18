from typing import List

class Solution:
    def vowelStrings(self, word: str, queries: List[List[int]]) -> List[int]:
        # Your code goes here
        vowel_set = {'a', 'e', 'i', 'o','u'}
        output = []
        for i in queries:
            char_set = {i for i in word[i[0]:i[1]+1]}
            output.append(len(vowel_set.intersection(char_set)))
        return output

if __name__ == "__main__":
    solution = Solution()
    word = "prefixsum"
    queries = [[0, 2], [1, 4], [3, 5]]
    print(solution.vowelStrings(word, queries))