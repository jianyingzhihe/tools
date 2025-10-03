input=r"D:\code\rogback\qwen\src\reasons.jsonl"
with open(input ,"r") as f:
    cnt=0
    for line in f:
        cnt+=1
print(cnt)