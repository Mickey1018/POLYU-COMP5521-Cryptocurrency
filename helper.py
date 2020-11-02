import random
import math


def generate_prime(start, end):
    primes = []
    for i in range(start, end + 1):
        for j in range(2, i):
            if i % j == 0:
                break
            else:
                primes.append(i)
    return primes


def gcd(x, y):
    """
    assume always x > y
    :param x:
    :param y:
    :return: gcd value
    """
    if x < y:
        z = x
        x = y
        y = z
    if y == 0:
        print(f'gcd = {x}')
        return x
    else:
        print(f'{x} = {(x - x % y) / y}*{y} + {x % y}')
        return gcd(y, x % y)


def modular_inverse(e, n):
    """
    Given that gcd(e, n) = 1, i.e. e,n are relatively prime
    :param e:
    :param n:
    :return: modular inverse of e such that e^-1 * e = 1 mod(n)
    """
    if gcd(e, n) != 1:
        return f'No solution: {e} and {n} are not relatively prime'

    inverse = None
    counter = 1
    answer = None
    while not answer:
        inverse = (n*counter + 1)/e
        if inverse % 1 == 0:
            answer = inverse
        else:
            counter += 1
            answer = None
    return f'counter = {counter}, inverse = {inverse}'


def miller_rabin(n):

    if n % 2 == 0 and n != 2:
        return 'Even number is not a prime'

    def decomposition(prime):
        prime -= 1
        for odd in range(1,math.floor(prime/2) + 1,2):
            for power in range(1,math.floor(math.log(prime)/math.log(2))):
                if prime == 2**power * odd:
                    return odd,power

    print(f"Number to be test: {n}")
    print("loading...")
    q = decomposition(n)[0]
    k = decomposition(n)[1]
    a = random.randint(1,n-1)
    print(f"{n-1} can be decomposed to 2^{k}*{q}")
    print(f"the selected random integer is {a}")

    for j in range(0,k):
        remainder = a ** ((2**j) * q) % n
        print(f"remainder is {remainder}")
        if remainder == 1 or remainder == n-1:
            print("inconclusive: possibly a prime")
        else:
            print("composite: not a prime")
    return True


def decompose_prime(n):

    primes = generate_prime(3, 500)

    for prime in primes:
        num = n/prime
        if num in primes:
            print(f'{n} = {prime}*{num}')
            return int(prime), int(num)
        else:
            continue


def crt(n, divisor):
    divisor1, divisor2 = decompose_prime(divisor)
    if gcd(divisor1, divisor2) != 1:
        return 'divisors are not co-prime!'
    remainder1 = n % divisor1
    remainder2 = n % divisor2
    print(f'step 1: {n} mod{divisor1} = {remainder1}')
    print(f'        {n} mod{divisor2} = {remainder2}')
    print(f'step 2: x = {remainder1} mod{divisor1}')
    print(f'step 3: x = {remainder2} mod{divisor2}')
    print(f'step 4: x = {divisor1}t + {remainder1} = {remainder2} mod{divisor2}')
    print(f'step 5: {divisor1}t = {remainder2-remainder1} mod{divisor2}')
    counter = None
    remainder = None
    for y in range(50):
        if (divisor2*y + remainder2 - remainder1)/divisor1 % 1 == 0:
            counter = y
            remainder = (divisor2*y + remainder2 - remainder1)/divisor1
            print(f'step 6: counter = {counter}, t = {int(remainder)} mod{divisor2}')
            print(f'step 7: t = {divisor2}s + {int(remainder)}')
            break
    print('sub (7) into (4)')
    print(f'step 8: x = {divisor1}({divisor2}s + {int(remainder)}) + {remainder1}')
    print(f'        x = {divisor1*divisor2}s + {remainder1+divisor2*counter+remainder2-remainder1}')
    print(f'        x = {remainder1+divisor2*counter+remainder2-remainder1} when s = 0, and x < {n}')
    return True


if __name__ == "__main__":

    # find gcd
    print(gcd(999, 911))

    # find modular inverse
    print(modular_inverse(e=48, n=99))

    # decompose prime
    print(decompose_prime(391))

    # millar rabin algorithm
    print(miller_rabin(9233))

    # crt
    print(crt(n=20**37, divisor=77))


