import random
answer = random.randint(1,100)
print("我想了一个 1 - 100 的数字,你有 7 次的机会。")
for i in range(7):
    guess = int(input(f"第 {i + 1} 次猜测:"))
    if guess > answer:
        print("大了")
    elif guess < answer:
        print("小了")
    else:
        print(f"恭喜！答案就是 {answer},你用了 {i + 1}次。")
        break
else:
    print(f"7 次都没猜对，答案就是 {answer}。")