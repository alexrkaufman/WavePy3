import numpy as np
from numpy.random import default_rng
from .utils import ft2, ift2
from . import psd
from . import phase_screen

rng = default_rng()

pi = np.pi

screen_method_dict = {
    'ft_sh': phase_screen.ft_sh_phase_screen,
    'ft': phase_screen.ft_phase_screen,
    'vacuum': phase_screen.vacuum
}

psd_dict = {
    'kolmogorov': psd.kolmogorov,
    'vonKarman': psd.vonkarman,
    'modified_vonKarman': psd.modified_vonkarman,
    'wavepy_og': psd.wavepy_og
}


# TODO: Implement a better algorithm for self.r0s

class Atmos:
    """Object representing Atmosphere

    TODO improve documentation
    """

    def __init__(self, n_gridpts, z, dx_0, dx_n, **settings):
        '''
        initialization

        n_gridpts - the number of grid points along one side length
        z - an array of phase screen locations
        dx_0 - the grid spacing in the image plane
        dx_n - the grid spacing in the pupil plane

        Phase Screen Numbering Scheme

        0     1     2    ...    n
        |     |     |           |
        |     |     |           |
        |     |     |           |
        |     |     |           |
        '''

        # there should be a check on atmos params based on psd and
        # screen_method to make sure the user has defined all the
        # appropriate values

        prop_frac = z / z[-1]

        self.n_gridpts = n_gridpts
        self.screen_locations = z
        self.dx_sampling = (dx_n - dx_0) * prop_frac + dx_0

        self.n_scr = len(z)
        self.screen_method_name = settings['screen_method_name']
        self.screen_method = screen_method_dict[self.screen_method_name]
        self.settings = {
            k: settings[k]
            for k in
                settings.keys() - {'screen_method_name', 'psd_name'}}

        try:
            self.psd_name = settings['psd_name']
            self.psd = self.__psd_setup()
        except KeyError:
            self.psd = None

        if self.screen_method_name == 'vacuum':
            self.settings['r0'] = float('inf')

        self.r0s = [self.settings['r0'] / self.n_scr**(-3 / 5)] * self.n_scr

        self.screen = [self.screen_method(*inputs)
                       for inputs in self.__screen_method_input()]

    def __screen_method_input(self):

        phase_screen_input_dict = {
            'vacuum': ['N'],
            'ft': ['N', 'dx', 'r0', 'psd'],
            'ft_sh': ['N', 'dx', 'n_subharm', 'r0', 'psd']
            }

        keys = phase_screen_input_dict[self.screen_method_name]
        a = {'N': self.n_gridpts, 'psd': self.psd, **self.settings}

        for (dx, r0) in zip(self.dx_sampling, self.r0s):
            a = {'dx': dx, 'r0': r0, **a}
            yield [a[key] for key in keys]

    def __psd_setup(self):
        ''' psd function

        The psd function is meant to alias whichever psd someone wants to use.
        The idea is that this can be swapped out at will and we wont have to
        change other code.
        '''

        psd_input_dict = {
            'kolmogorov': [],
            'vonKarman': ['L0'],
            'modified_vonKarman': ['L0', 'l0']
        }

        psd_raw = psd_dict[self.psd_name]

        setting_names = psd_input_dict[self.psd_name]

        psdfn = psd_raw(*[self.settings[setting_name]
                          for setting_name in setting_names])

        return psdfn

    def __get_derived_parms(self, z, wvl, Cn2):

        k = 2 * pi / wvl

        # This is the plane wave r0
        r0_pw = (0.423 * k**2 * Cn2 * z) ** (-3.0 / 5.0)
        print(r0_pw)

        return {
            'r0': r0_pw
            # 'theta0': theta0,
            # 'rytov_sq': rytov_sq
        }

    def __wavepy_og(self):
        # TODO make this do what wavepy did originally
        # it may require updating the ft_phase_screen and _ft_sh methods
        # and its possible that this approach has all the same params and
        # then some so we could just set some of the parameters for the
        # von karman psd

        # extract params from info

        # create phase screens
        pass

    def vacuum(self, *args):
        return np.ones([self.n_gridpts, self.n_gridpts])

    @staticmethod
    def __vonKarman_psd(r0, f, fm, f0):
        ''' vonKarman_psd

        This is the modified von Karman PSD function.
        The von Karman PSD is equivalent to fm = 'inf'.
        The Kolmogorov PSD is equivalent to fm = 'inf' and f0 = 0.
        '''

        if fm == float('inf'):
            f_ratio = 0
        else:
            f_ratio = f / fm

        psd_phi = (0.023 * r0**(-5/3) * np.exp(-(f_ratio)**2)
                   / (f**2 + f0**2)**(11/6))

        return psd_phi

    def __getitem__(self, key):
        return self.screen[key]

    def __len__(self):
        return len(self.screen)
