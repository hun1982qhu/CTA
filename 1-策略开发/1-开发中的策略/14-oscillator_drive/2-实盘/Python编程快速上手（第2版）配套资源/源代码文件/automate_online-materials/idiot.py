import pyinputplus as pyip

while True:
    prompt = 'Want to know how to keep an idiot busy for hours?\n'
    response = pyip.inputYesNo(prompt)
    if response == 'no':
        break
print('Thank you. Have a nice day.')
