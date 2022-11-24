import json
from scipy import optimize
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from yakopcic_functions import *

model = json.load(open('../../../fitted/fitting_pulses/old_device/regress_negative_xp_alphap-adjusted_ap_an'))


def one_step_yakopcic(voltage, x, readV, **params):
    x = x + dxdt(voltage, x, model['Ap'], model['An'], model['Vp'], model['Vn'], model['xp'],
                 model['xn'], model['alphap'], model['alphan'], 1) * model['dt']
    if x < 0:
        x = 0
    if x > 1:
        x = 1

    i = current(readV, x,
                params['gmax_p'], params['bmax_p'], params['gmax_n'], params['bmax_n'],
                params['gmin_p'], params['bmin_p'], params['gmin_n'], params['bmin_n'])
    r = readV / i

    return x, r


def iterate_yakopcic(resetV, setV, iterations=10, plot_output=False, print_output=False):
    print_cond = lambda *a, **k: None
    if print_output:
        print_cond = print

    x0 = 0.6251069761800688
    readV = -0.1

    # random.seed(0)

    x_p = x_n = x0
    R_p = []
    R_n = []
    X_p = [x_p]
    X_n = [x_n]

    for j in tqdm(range(iterations)):
        x_p, r_p = one_step_yakopcic(setV, x_p, readV, **model)
        R_p.append(r_p)
    print_cond('\nStart value:', R_p[0], 'End value:', R_p[-1])
    # calculate average percent change in resistances (https://sciencing.com/calculate-mean-change-5953798.html)
    set_efficacy = np.abs(np.mean(np.diff(R_p) / np.abs(R_p[:-1])) * 100)
    print_cond('Average resistance change with SET pulses:', set_efficacy, '%')

    for j in tqdm(range(iterations)):
        x_n, r_n = one_step_yakopcic(resetV, x_n, readV, **model)
        R_n.append(r_n)
    print_cond('\nStart value:', R_n[0], 'End value:', R_n[-1])
    reset_efficacy = np.abs(np.mean(np.diff(R_n) / np.abs(R_n[:-1])) * 100)
    print_cond('Average resistance change with RESET pulses:', reset_efficacy, '%')

    if set_efficacy > reset_efficacy:
        reset_vs_set_efficacy_percent = np.abs(((set_efficacy - reset_efficacy) / reset_efficacy) * 100)
        print_cond('SET pulses are more effective than RESET pulses by', reset_vs_set_efficacy_percent, '%')
    else:
        set_vs_reset_efficacy_percent = np.abs(((reset_efficacy - set_efficacy) / set_efficacy) * 100)
        print_cond('RESET pulses are more effective than SET pulses by', set_vs_reset_efficacy_percent, '%')

    if plot_output:
        fig, ax = plt.subplots()
        ax.plot(R_p, label='SET')
        ax.plot(R_n, label='RESET')
        ax.legend()
        fig.suptitle(f'SET {setV} V, RESET {resetV} V')
        fig.show()

    if set_efficacy > reset_efficacy:
        k = np.abs(set_efficacy / reset_efficacy)
        Preset = 1
        Pset = 1 / k
    else:
        k = np.abs(reset_efficacy / set_efficacy)
        Pset = 1
        Preset = 1 / k

    print_cond('k:', k)
    print_cond('Vreset', resetV, '| Vset', setV)
    print_cond('Preset:', Preset, '| Pset:', Pset)

    return k, setV, resetV, Pset, Preset


def residuals_voltages(x):
    resetV = x[0]
    setV = x[1]

    k, _, _, _, _ = iterate_yakopcic(resetV, setV)

    return k


# -- target probabilities at 1 and find voltages that give that outcome
find_voltages = optimize.least_squares(residuals_voltages, [-0.2, 3.86621037038006], bounds=([-10, 0], [0, 10]),
                                       method='dogbox', verbose=1)
print('VOLTAGES GIVEN TARGET PROBABILITIES AT 1')
iterate_yakopcic(find_voltages.x[0], find_voltages.x[1], plot_output=True, print_output=True)

# -- calculate probabilities given voltages
print('PROBABILITIES GIVEN VOLTAGES')
iterate_yakopcic(-2, 3.86621037038006, plot_output=True, print_output=True)