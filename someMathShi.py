from functools import lru_cache

@lru_cache
def fibo(n: int) -> int:
    if n <= 1:
        return n
    else:
        return fibo(n - 1) + fibo(n - 2)
    
for i in range(0, 100):
    print(f"{i}: {fibo(i)}")