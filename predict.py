import re
import pickle
import numpy as np
from catboost import CatBoostRegressor

# вычисление расстояния между указанными символами
def get_dist(lower, upper, dist_1, dist_2):
    result = {}

    for i in range(dist_2):
        for j in range(dist_1):
            if i*dist_1+j <= len(lower)-1:
                result[lower[i*dist_1+j]] = j
                result[upper[i*dist_1+j]] = j
    return result

# среднее расстояние ввода
def calc_dist(a):
    summ = 0    
    for i in range(len(a)-1):
        if (a[i] not in hor) or (a[i+1] not in hor):
            continue
        summ += abs((hor[a[i]] - hor[a[i+1]]) + (vert[a[i]] - vert[a[i+1]]))
    return summ/len(a)

# среднее квадратичное расстояние ввода
def calc_dist_square(a):
    summ = 0    
    for i in range(len(a)-1):
        if (a[i] not in hor) or (a[i+1] not in hor):
            continue
        summ += ((hor[a[i]] - hor[a[i+1]])**2 + (vert[a[i]] - vert[a[i+1]])**2)**0.5
    return summ/len(a)

# посимвольное расстояние ввода
def calc_dist_i(a,i):
    if len(a) > i:
        if (a[i] not in hor) or (a[i-1] not in hor):
            return 0
        return abs((hor[a[i]] - hor[a[i-1]]) + (vert[a[i]] - vert[a[i-1]]))
    return -1

def palindrom(word):
    if len(word) == 1 or len(word) == 0:
        return 1
    if word[0] == word[-1]:
        return palindrom(word[1:-1])
    else:
        return 0
    
def count_symb(a, symb):
    return sum([1 if symb.intersection(i) else 0 for i in a])

def vowel(a, vow):
    if vow:
        return sum([1 if (i in 'aeiouy') & i.isalpha() else 0 for i in a])
    else:
        return sum([1 if (i not in 'aeiouy') & i.isalpha() else 0 for i in a])


low1 = "1234567890-=qwertyuiop[]asdfghjkl;'\\zxcvbnm,./"
upp1 = '!@#$%^&*()_+QWERTYUIOP{}ASDFGHJKL:"|ZXCVBNM<>?'
low2 = "1qaz2wsx3edc4rfv5tgb6yhn7ujm8ik,9ol.0p;/"
upp2 = '!QAZ@WSX#EDC$RFV%TGB^YHN&UJM*IK<(OL>)P:?'
dictionary = low1+upp1
dist_1 = 12
dist_2 = 4

                
hor = get_dist(low1, upp1, dist_1, dist_2)
vert = get_dist(low2, upp2, dist_2, dist_1)
new_h = {'±':0, '§':0,'~':0,'`':0, '\x03':11, '\x0f':11,'\x07':11,'\x02':11}
new_v = {'-':0,'[':1,"'":2,'=':0,']':1, '\\':2, '_':0, '\x03':2,'\x0f':2,'\x07':2,'\x02':2,\
         '{':1,'"':2,'+':0,'}':1,'|':2, '±':0, '§':0,'~':3,'`':3}
vert.update(new_v)
hor.update(new_h)



def transform(passw):
    symb = set('[~!@#$%^&*()_+{}":;\']+$')
    features = np.zeros(63)
    
    # длина пароля
    features[0] = len(passw)
    
    # количество нижних, верхних, цифр, спецсимволов, бинарный число ли
    features[1] = sum(map(str.isupper, passw))
    features[2] = sum(map(str.islower, passw))
    features[3] = sum(map(str.isdigit, passw))
    features[4] = 1 if passw.isdigit() else 0 
    features[5] = 1 if symb.intersection(passw) else 0
    features[6] = count_symb(passw,symb)

    # палиндром
    features[7] = 1 if palindrom(passw) else 0
    
    # признаки по расстоянию клавиш
    for i in range(10):
        features[i+8] = -1
    for i in range(1,11):
        features[i+8] = calc_dist_i(passw,i)
    features[19] = calc_dist(passw)
    features[20] = calc_dist_square(passw)

    # очистка от символов и цифр
    reg = re.compile('[^a-zA-Z ]')
    clean_passw = passw.replace('\d+', '')
    clean_passw = reg.sub('', clean_passw).lower()

    # бинарные признаки по длине
    features[21] = features[0] < 5
    features[22] = features[0] < 10
    features[23] = features[0] < 15
    features[24] = features[0] >= 15
    
    # относительная частота симоволов
    features[25] = features[2]/features[0]
    features[26] = features[1]/features[0]
    features[27] = features[3]/features[0]
    features[28] = features[6]/features[0]
    features[29] = (features[1] + features[2])/features[0]

    # совместное появление типов символов
    features[30] = (features[2] > 0) & (features[3] > 0) \
           & (features[1] == 0) & (features[6] == 0)
    features[31] = (features[2] == 0) & (features[3] == 0) \
           & (features[1] > 0) & (features[6] == 0)
    features[32] = (features[2] > 0) & (features[3] == 0) \
           & (features[1] == 0) & (features[6] == 0)
    features[33] = (features[2] > 0) & (features[3] == 0) \
           & (features[1] == 1) & (features[6] == 0)
    features[34] = (features[2] > 0) & (features[1] > 0)

    # количество уникальных символов
    features[35] = len(set(passw))
    
    # частые фразы
    features[36] = 'pass' in passw
    features[37] = 'qwerty' in passw
    features[38] = 'qwe' in passw
    features[39] = 'qaz' in passw
    features[40] = '123' in passw
    features[41] = '12345' in passw
    features[42] = '321' in passw
    features[43] = 'fuck' in passw
    features[44] = 'abc' in passw
    features[45] = '000' in passw
    features[46] = '111' in passw
    features[47] = '666' in passw
    features[48] = '777' in passw
    features[49] = 'love' in passw

    # гласные согласные
    features[50] = vowel(passw.lower(), True)
    features[51] = vowel(passw.lower(), False)
    features[52] = features[50]/features[0]
    features[53] = features[51]/features[0]
    if (features[1] + features[2]) == 0:
        features[54] = 0
        features[55] = 0
    else:
        features[54] = features[50]/(features[1] + features[2])
        features[55] = features[51]/(features[1] + features[2])
    
    
    # количество уникальных букв, цифр, спецсимволов
    spec_symb = '!@#$%^&*()_+-=}{:;"><,./?|\~`'
    features[56] = sum([1 if j.isdigit() else 0 for j in set(passw)])
    features[57] = sum([1 if j.isalpha() else 0 for j in set(passw)])
    features[58] = sum([1 if j in spec_symb else 0 for j in set(passw)])
    
    # количество букв, относительная частота, первая буква
    features[59] = features[1] + features[2]
    features[60] = features[59]/features[0]
    features[61] = passw[0].isalpha()
    
    # текст и после него цифры
    regex = re.compile('^[a-zA-Z]+[\d]{1,4}$')
    features[62]= 1 if regex.match(passw) else 0

    where_are_NaNs = np.isnan(features)
    features[where_are_NaNs] = 0
    
    return features

def predict(password, model):
    y = transform(password)
    pred = int(np.expm1(model.predict(y)))
    return 5 if pred < 0 else pred

