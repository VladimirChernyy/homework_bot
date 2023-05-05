def longestCommonPrefix(self, strs: List[str]) -> str:
    st = ''
    for s in strs:
        for y in range(len(s)):
            if s[y] in (strs[0] and strs[1] and strs[2]):
                if s[y] not in st:
                    st += s[y]
    return st

print(longestCommonPrefix())