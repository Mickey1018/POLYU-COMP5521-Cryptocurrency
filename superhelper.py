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
        print(f'gcd = {x}\n')
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
        return f'No solution: {e} and {n} are not relatively prime\n'

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
    print(f'counter = {counter}, inverse = {int(inverse)}\n')
    return int(inverse)


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
            print(f'{n} = {prime}*{int(num)}')
            return int(prime), int(num)
        else:
            continue


def euler_totient_function(n):
    number = 0
    for i in range(1,n):
        if gcd(i,n) == 1:
            number += 1
    return number


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


def group_generator_with_mod_operation(p, divisor):
    generator = set()
    group_set = set(i for i in range(1, p))  # for 0 <= i <= p-1
    for g in group_set:
        subset = set()
        for i in range(1, p):
            subset.add(g**i % divisor)
        print(f'group element: {g}')
        print(f'subset: {subset}')
        print(f'order of subset is {len(subset)}\n')
        if not group_set.symmetric_difference(subset):
            generator.add(g)
    print(f'generators: {generator}')
    return generator


def test_generator(prime, g):
    group_set = set(i for i in range(1, prime))
    if prime not in generate_prime(1,500):
        return f'{prime} is not a prime'
    if g not in group_set:
        return 'g is not in the group'
    if abs(g) == 1 or abs(g) == prime-1:
        return 'g cannot be 1 or p-1'
    for p1 in generate_prime(1, 500):
        if prime-1 == 2*p1:
            print(f'p1 is {p1}')
            if g**p1 % prime != 1:
                print(f'{g} is a generator')
                break
            else:
                print(f'{g} is not a generator')
                print(f'{-g} or {prime-g} is a generator')
                break


def rsa(message, public_key, n):

    phi_n = euler_totient_function(n)

    if gcd(public_key, phi_n) != 1:
        return 'e and phi_n are not relatively prime, cannot do RSA!'

    ciphertext = message**public_key % n
    private_key = modular_inverse(e=public_key, n=phi_n)

    print(f'\nphi_n is {phi_n}')
    print(f'ciphertext is {ciphertext}')
    print(f'private key is {private_key}')

    m = ciphertext**private_key % n
    if m == message:
        print('match!')
        return True
    else:
        print('not match!')
        return False


def diffie_hellman(prime, generator, private_key_a, private_key_b):
    x = generator**private_key_a % prime
    y = generator**private_key_b % prime
    print(f'X = g^a mod(p) = {x}')
    print(f'Y = g^b mod(p) = {y}')

    share_key_x = y**private_key_a % prime
    share_key_y = x**private_key_b % prime
    if share_key_x == share_key_y:
        print(f'share key is {share_key_x}\n')
        return share_key_x


def rsa_signature(message, public_key, n):

    phi_n = euler_totient_function(n)

    if gcd(public_key, phi_n) != 1:
        return 'e and phi_n are not relatively prime, cannot do RSA!'

    signing_key = modular_inverse(e=public_key, n=phi_n)
    signature = message ** signing_key % n

    print(f'\nphi_n is {phi_n}')
    print(f'signature is {signature}')
    print(f'signing key is {signing_key}')

    m = signature**public_key % n
    if m == message:
        print('match!')
        return True
    else:
        print('not match!')
        return False


def elgamal_digital_signature(message, prime, generator, secret_x, one_time_k):
    if prime not in generate_prime(1, 500):
        return f'{prime} is not a prime!'

    if generator not in group_generator_with_mod_operation(p=prime, divisor=prime):
        return f'not a generator'

    y = generator**secret_x % prime

    if one_time_k <= 0 or one_time_k > prime-1:
        return 'one time key out of range'

    if gcd(one_time_k, prime) != 1:
        return f'one time key and prime are not relatively prime'

    r = generator**one_time_k % prime

    k_inverse = modular_inverse(one_time_k, prime-1)

    s = k_inverse*(message - secret_x*r) % (prime-1)

    a = generator**message % prime
    b = y**r * r**s % prime

    print(f'\ny = g^x mod(p) = {y}')
    print(f'r = g^k mod (p) = {r}')
    print(f'k^-1 = {k_inverse}')
    print(f's = k^-1 * (X - x*r) mod(p-1) = {s}')
    print(f'g^x mod(p) = {a}')
    print(f'y^r * r^s mod(p) = {b}')

    if a == b:
        print('match!')
        return True
    else:
        print('not match!')
        return False


def chum_blind_signature(message, blinding_factor, n, public_key):

    if gcd(blinding_factor, n) != 1:
        return 'blinding factor and n are not relatively prime'
    blinding_factor_inverse = modular_inverse(blinding_factor, n)

    blinded_message = message*blinding_factor**public_key % n

    phi_n = euler_totient_function(n)

    if gcd(phi_n, public_key) != 1:
        return 'e and n are not relatively prime'

    private_key = modular_inverse(public_key, phi_n)
    blinded_signature = blinded_message**private_key % n
    signature_1 = blinded_signature*blinding_factor_inverse % n
    signature_2 = message**private_key % n

    print(f'private key = {private_key}')
    print('\nBlinding phase:')
    print(f'Blind message = {blinded_message}')
    print('\nSigning phase:')
    print(f'Signature to Blind message = {blinded_signature}')
    print('\nUnblinding phase:')
    print(f'signature generated from inverse of blinding factor = {signature_1}')
    print(f'signature to message with private key = {signature_2}')

    if signature_1 == signature_2:
        print('signature match!')
    else:
        print('signature do not match...')


if __name__ == "__main__":

    # 參考以下例子

    # find gcd
    gcd(999, 911)

    # find modular inverse
    modular_inverse(e=48, n=391)

    # decompose prime
    decompose_prime(391)

    # euler's totient function
    print(euler_totient_function(31))

    # millar rabin algorithm
    miller_rabin(9233)

    # crt
    crt(n=20**37, divisor=77)

    # generator
    group_generator_with_mod_operation(p=11, divisor=11)

    # test generator
    test_generator(prime=11, g=3)

    # diffie hellman
    diffie_hellman(prime=23, generator=9, private_key_a=4, private_key_b=3)

    # RSA
    rsa(message=6, public_key=7, n=55)

    # RSA signature scheme
    rsa_signature(message=688, public_key=1019, n=3337)

    # elgamal digital signature scheme
    elgamal_digital_signature(message=9, prime=11, generator=2, secret_x=3, one_time_k=7)

    # Chum's Blind Signature
    chum_blind_signature(message=37, blinding_factor=29, n=119, public_key=5)


