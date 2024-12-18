import random


def get_random_captcha(num):
    code_list = []
    # 每一位验证码都有三种可能（大写字母，小写字母，数字）
    for i in range(num):
        statu = random.randint(1, 3)
        if statu == 1:
            a = random.randint(65, 90)
            random_uppercase = chr(a)
            code_list.append(random_uppercase)

        elif statu == 2:
            b = random.randint(97, 122)
            random_lowercase = chr(b)
            code_list.append(random_lowercase)

        elif statu == 3:
            random_num = random.randint(0, 9)
            code_list.append(str(random_num))

    verification_code = "".join(code_list)  # 生成随机验证码
    return verification_code
