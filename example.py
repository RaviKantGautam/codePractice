from typing import List

class Solution:
    def vowelStrings(self, word: str, queries: List[List[int]]) -> List[int]:
        # Your code goes here
        vowel_set = set('aeiou')
        output = []
        for i in queries:
            char_set = set(word[i[0]:i[1]+1])
            output.append(len(vowel_set.intersection(char_set)))
        return output

if __name__ == "__main__":
    solution = Solution()
    word = "prefixsum"
    queries = [[0, 2], [1, 4], [3, 5]]
    print(solution.vowelStrings(word, queries))