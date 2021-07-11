import pyautogui, time
print('5 second til it starts')
pyautogui.LOG_SCREENSHOTS = True
pyautogui.LOG_SCREENSHOTS_LIMIT = 100
time.sleep(5)
pyautogui.click()    # click to put drawing program in focus
distance = 300
shrink = 20
while distance > 0:
    pyautogui.dragRel(distance, 0, duration=0.1)   # move right
    distance = distance - shrink
    pyautogui.dragRel(0, distance, duration=0.1)   # move down
    pyautogui.dragRel(-distance, 0, duration=0.1)  # move left
    distance = distance - shrink
    pyautogui.dragRel(0, -distance, duration=0.1)  # move up
