from pynput.keyboard import Key, Controller
import time


# 将 num 转为整数
num = int(input("输入本群人数，只能是正整数："))

# 初始化键盘控制器
keyboard = Controller()

# 等待2秒，方便切换到目标输入框
print(f"Starting in 2 seconds... Will run {num} iterations.")
time.sleep(2)

# 循环 num 次
for i in range(1, num + 1):
    print(f"Executing iteration {i}...")

    # 第一部分：按下 Shift + 2
    with keyboard.pressed(Key.shift):
        keyboard.press('2')
        keyboard.release('2')

    time.sleep(0.1)

    # 第二部分：按下 ↓ (下方向键) (i-1) 次（第一次不按）
    for _ in range(i - 1):
        keyboard.press(Key.down)
        keyboard.release(Key.down)
        time.sleep(0.05)  # 小延迟，确保输入被识别

    # 按下 Enter
    keyboard.press(Key.enter)
    keyboard.release(Key.enter)

    # 每次循环之间稍作停顿，避免过快
    time.sleep(0.5)

print("Done!")