print("Hi! This is a simple calculator program.")
print("Enter two numbers and an operator to perform a calculation.")
print("Operators: +, -, *, /, %, **")

op = input("Enter the operator: ");
try:
    num1 = float(input("Enter the first number: "));
    num2 = float(input("Enter the second number: "));
    if op == '+':
        print("Result: ", num1 + num2)
    elif op == '-':
        print("Result: ", num1 - num2)
    elif op == '*':
        print("Result: ", num1 * num2)
    elif op == '/':
        print("Result: ", num1 / num2)
    elif op == '%':
        print("Result: ", num1 % num2)
    elif op == '**':
        print("Result: ", num1 ** num2)
    else:
        print("Invalid operator. Please enter a valid operator.")
        exit()
except ValueError:
    print("Invalid input. Please enter a number.")
    exit()