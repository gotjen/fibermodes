# This file is part of FiberModes.
#
# FiberModes is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FiberModes is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with FiberModes.  If not, see <http://www.gnu.org/licenses/>.


"""Test suite for fiber.fiber module"""

import unittest
import os.path

from fibermodes import Mode, FiberFactory
from fibermodes.fiber.material.material import OutOfRangeWarning
from math import isinf, isnan
import warnings

_HERE, _ = os.path.split(__file__)


class TestFiber(unittest.TestCase):

    """Test suite for Fiber class"""

    def testFiberProperties(self):
        f = FiberFactory(os.path.join(_HERE, 'rcf.fiber'))
        fiber = f[0]
        self.assertEqual(len(fiber), 3)
        self.assertEqual(fiber.name(0), "center")
        self.assertEqual(fiber.name(1), "ring")
        self.assertEqual(fiber.name(2), "cladding")
        self.assertEqual(fiber.innerRadius(1), 4e-6)
        self.assertEqual(fiber.outerRadius(1), 8e-6)
        self.assertEqual(fiber.thickness(1), 4e-6)
        self.assertEqual(fiber.index(6e-6, 1550e-9), 1.454)
        self.assertEqual(fiber.minIndex(1, 1550e-9), 1.454)
        self.assertEqual(fiber.maxIndex(1, 1550e-9), 1.454)

    def testFiberWithMaterials(self):
        f = FiberFactory(os.path.join(_HERE, 'smf28.fiber'))
        f.layers[0].material = "SiO2GeO2"
        f.layers[0].mparams = [0.05]
        f.layers[1].material = "Silica"
        fiber = f[0]

        self.assertAlmostEqual(fiber.index(2e-6, 1550e-9),
                               1.451526777142772)
        self.assertAlmostEqual(fiber.index(8e-6, 1550e-9),
                               1.444023621703261)

    def testToWl(self):
        f = FiberFactory(os.path.join(_HERE, 'smf28.fiber'))
        fiber = f[0]
        self.assertAlmostEqual(fiber.toWl(fiber.V0(1600e-9)), 1600e-9)

        f.layers[0].material = "Silica"
        f.layers[1].material = "Air"
        fiber = f[0]
        self.assertAlmostEqual(fiber.toWl(fiber.V0(1600e-9)), 1600e-9)

        self.assertEqual(fiber.toWl(float("inf")), 0)
        self.assertTrue(isinf(fiber.toWl(0)))

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=OutOfRangeWarning)
            f = FiberFactory()
            f.addLayer(radius=10e-6, material="SiO2GeO2", x=0.25)
            f.addLayer(material="Silica")
            fiber = f[0]
            wl = fiber.toWl(2.4)
            self.assertGreater(wl, 10e-6)

    def testToWlNearResonanceClaussiusMossotti(self):
        """The fixed point iteration can try a wavelength near the 8.96 um
        resonance of silica, where the Claussius-Mossotti index (SiO2F) is
        not defined. This is not a convergence, but it must not raise."""
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=OutOfRangeWarning)
            f = FiberFactory()
            f.addLayer(radius=4e-6, material="SiO2GeO2", x=0.05)
            f.addLayer(radius=10e-6, material="SiO2F", x=0.05)
            f.addLayer(material="Silica")
            fiber = f[0]
            # No wavelength of the material models gives V0 = 1: NaN.
            self.assertTrue(isnan(fiber.toWl(1.0)))
            for v0 in (2.4, 5.0):
                wl = fiber.toWl(v0)
                self.assertAlmostEqual(fiber.V0(wl), v0, places=9)
            for mode in (Mode("TE", 0, 1), Mode("TM", 0, 1),
                         Mode("HE", 2, 1), Mode("LP", 1, 1)):
                co = fiber.cutoff(mode)
                self.assertTrue(0 < co < float("inf"), msg=str(mode))

    def testToWlSolvesV0(self):
        """toWl returns the wavelength where V0 equals the given V, for a
        fiber with dispersive (SiO2F, Claussius-Mossotti) layers. (Below
        V0 = 2.27, the wavelength would be above 8 um, beyond the
        material models.)"""
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=OutOfRangeWarning)
            fiber = _wfiber()
            for v0 in (3.0, 4.0, 8.3, 11.5):
                wl = fiber.toWl(v0)
                self.assertAlmostEqual(fiber.V0(wl), v0, places=9,
                                       msg=str(v0))

    def testCutoffsWFiber(self):
        """Cutoffs of a W fiber (SiO2GeO2 core, SiO2F trench). With a
        non-converged toWl, the scan found false roots for HE(2,1) and
        HE(3,1). Each cutoff must be a sign change of its equation."""
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=OutOfRangeWarning)
            fiber = _wfiber()
            expected = {
                Mode("TE", 0, 1): 8.269621,
                Mode("HE", 2, 1): 8.298005,
                Mode("TM", 0, 1): 8.310835,
                Mode("EH", 1, 1): 11.557234,
                Mode("HE", 3, 1): 11.568822,
            }
            fct = {"TE": fiber._cutoff._tecoeq, "TM": fiber._cutoff._tmcoeq,
                   "HE": fiber._cutoff._hecoeq, "EH": fiber._cutoff._ehcoeq}
            for mode, co in expected.items():
                v = fiber.cutoff(mode)
                self.assertAlmostEqual(v, co, places=5, msg=str(mode))
                f = fct[mode.family.name]
                before = f(v - 1e-4, mode.nu)
                after = f(v + 1e-4, mode.nu)
                self.assertLess(before * after, 0, msg=str(mode))
            self.assertLess(fiber.cutoff(Mode("EH", 1, 1)),
                            fiber.cutoff(Mode("HE", 3, 1)))


def _wfiber():
    f = FiberFactory()
    f.addLayer(radius=4e-6, material="SiO2GeO2", x=0.05)
    f.addLayer(radius=10e-6, material="SiO2F", x=0.05)
    f.addLayer(material="Silica")
    return f[0]


if __name__ == "__main__":
    unittest.main()
