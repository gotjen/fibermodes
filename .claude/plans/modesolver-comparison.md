# Mode solver comparison: fibermodes (Python) and nlight-fiber-model (MATLAB)

Recorded 2026-10-02. This is a reference for future plans. It changes no code.

- Python: this repo (`fibermodes`, originally by C. Brunet).
- MATLAB: `~/PurpleDocs/WORK/archive/nLight/nlight-fiber-model`. Its solver is
  `svmodes.m` by Thomas Murphy (UMD), driven by `FIBER.m` and `FIBERMODE.m`.

The findings come from a read of the code. No code was run. File and line
references to this repo are for branch `refactor/modernization`.

## 1. The two methods

Both methods solve the same eigenproblem. Find `β = k0·neff` and a field `φ` that
satisfy the wave equation and decay outside the fiber:

    ∇t²φ + k0²·n²(x,y)·φ = β²·φ

They differ in how they make the problem finite.

### `svmodes`: a large linear eigenproblem

1. It puts `φ` on a grid of `nx × ny` points.
2. It replaces `∇t²` with a five-point difference formula.
3. The equation becomes `A·v = β²·v`. `A` is sparse, with one row per grid point.
4. `eigs` factors `(A − σI)` once, with `σ = (2π·nguess/λ)²`. It returns the
   `nmodes` eigenvalues nearest to `σ` (`svmodes.m:163-171`, tolerance 1e-8).

The eigenvalue is `β²`. The eigenvector is the field at each grid point. All
requested modes come from one solve.

### `fibermodes`: a small nonlinear eigenproblem

1. The fiber is circular, so the angle dependence is `exp(iνφ)`. `ν` is an input.
2. In a layer with constant index, the radial solution is exact: Bessel `J` and `Y`
   where `neff < n`, and `I` and `K` where `neff > n`.
3. The only unknowns are some amplitudes for each layer.
4. Field continuity at each interface gives a small system `M(neff)·c = 0`.
5. A solution exists only where `det M(neff) = 0`: the characteristic equation.
6. `brentq` finds one root of that scalar function. One root is one mode.

`neff` is inside the Bessel arguments, so the problem is nonlinear in `neff`. It
needs a root search, not a matrix eigensolver.

Solver classes:

- `fiber/solver/ssif.py`: two layers. Closed-form characteristic equations. The
  bracket comes from the cutoffs of the mode and of the next mode. `_findBetween`
  bisects until a sign change, then calls `brentq`.
- `fiber/solver/mlsif.py`: any number of layers. It carries `(Ez, Hz, Ephi, Hphi)`
  outward layer by layer (`StepIndex.EH_fields`, 4×4 solve in `vConstants`) and
  evaluates a 2×2 determinant at the last interface (`_heceq`). `_findFirstRoot`
  steps down from the `neff` of the previous mode with `delta = 1e-6`.
- `fiber/solver/tlsif.py`: analytic cutoff equations for three layers.
  `ssif.Cutoff` uses Bessel zeros.
- `fiber/fiber.py`: `beta` derivatives by five-point finite difference in omega
  give `ng`, `D`, `S`.

### Summary table

| Topic | `svmodes` (eigs) | `fibermodes` (root search) |
|---|---|---|
| Problem type | Large, linear | Small, nonlinear in `neff` |
| Basis | Grid points; local, approximate | Bessel functions; global, exact |
| Dimension | 2D Cartesian grid | 1D radial, analytic azimuthal order |
| Problem size | `nx·ny` unknowns | A 4×4 solve for each layer |
| Error source | Grid spacing, staircase at the core edge, finite window | Root tolerance only |
| Geometry | Any `n(x,y)` | Circular, piecewise-constant layers |
| Where to look | `nguess` shift | Bracket from cutoffs or the previous mode |
| Modes per solve | Many | One |
| Mode label | Unknown; inferred from the field | Known; `(family, ν, m)` is the input |
| `neff` | Complex; imaginary part gives loss | Real, between `n_clad` and `n_max` |
| Outer boundary | Zero field plus complex coordinate stretch | Exact `K` decay in an infinite last layer |
| Vector physics | Semivectorial, one polarization (`'ex'`) | Full vector (HE, EH, TE, TM) and scalar LP |
| Cutoff | Not available directly | Separate analytic equation |

### Failure modes

- `eigs` does not miss a mode near the shift if `nmodes` is sufficient. It also
  returns modes of the computation window, which are not fiber modes.
  `FIBERMODE.filtermodebyconfinement` removes them after the solve.
- The root search returns no false modes if the bracket is correct. It can miss a
  root, or stop on a pole. `solver.py` tests for poles ("Skip discontinuities").
  Two roots closer than the `mlsif` step (`1e-6`) can be missed.

### Why a bend needs the grid method

A bend adds the term `n·(1 + y/R)`. The index then depends on angle, so the
`exp(iνφ)` separation is not valid. No Bessel solution exists for each layer. The
grid method only gets a different `eps` matrix.

## 2. Capability comparison

| Capability | Python | MATLAB |
|---|---|---|
| Step-index accuracy | Exact to root tolerance | Limited by the 0.5 um grid |
| Measured or graded profile | No (step layers only, in practice) | Yes |
| Bend loss, leakage loss | No | Yes |
| Thermal load | No | Yes |
| Core ellipticity | No | Yes |
| True vector modes, HE/EH split | Yes | No |
| Cutoff wavelengths | Yes, direct | No, only by scan |
| Dispersion (`ng`, `D`, `S`), material dispersion | Yes (Sellmeier materials) | No (fixed `nsilica = 1.45645`) |
| Mode labels | Yes | No |
| Parameter sweeps | `Simulator` / `PSimulator` | `MandrelSeries` with `arrayfun` |

Gaps in the Python code:

- `mlsif._tefield` is `pass`.
- `mlsif._tmfield` returns names that are not defined.
- `SuperGaussian.EH_fields` does not set the derivative start values when
  `ri != 0`. Graded-index support is not complete.

## 3. MATLAB solver path

- `FIBER.meshrip`: uniform grid, `meshdx = 0.5` um, window `rmult = 6` core radii,
  clad stretch `cladfactor = 2`. The index of a cell is the mean of four vertex
  values. Option `ellip` scales the y axis.
- `FIBER.bendrip`: conformal tilt `n·(1 + y/R)`, `stressfactor = 1.0`.
- `FIBER.heatrip`: radial temperature profile (`betaT.m`) times dn/dT.
- `FIBER.svmodes` (static wrapper, line 1364): default shift is
  `nsilica + max(dn)`. It passes `eps = INDbq.^2`, the stretched `dx` and `dy`,
  boundary `'0000'`, and field `'ex'`.
- `FIBER.modesolrelative`: for a bend series, each straight-fiber `neff` is the
  shift, with 5 modes requested. This replaces a 600-mode solve.
- `FIBERMODE`: power normalization, confinement filter (power inside 2 core radii
  above 0.1), 1/e² widths, far field by `fft2`, loss in dB/m from `imag(neff)`.
- `wgmodes.m` (full vector) is in the repo but nothing calls it.

### Dispatch at `FIBER.m:1380`

The unqualified call `svmodes(...)` inside the static method `FIBER.svmodes` goes
to the path function `util/Anisotropic dielectric waveguide modesolver/svmodes.m`.
A static method needs the class prefix or a `FIBER` object in the argument list.
Line 1380 has neither, so MATLAB uses the path function. If a `FIBER` object is
added to that argument list, the call recurses.

## 4. MATLAB code review

No MATLAB rule file exists in `~/.claude/rules/`. The review used
`common/coding-style.md` and accepted MATLAB practice.

Marks: **M** = lines read in the main session. **S** = subagent report only.

Verdict: the default path (Liekki fiber, `'constant'` mesh, straight `modesol`) is
coherent. Several branches around it are broken or dead. There are no tests.
`FIBER.m` has 1484 lines and mixes database import, meshing, solver drivers, RP
Fiber Power, export, and plots. `FIBERMODE.m` is cohesive.

Defects that change results or break a path:

- `FIBER.m:402` (M): `length(mode.nmode)` is always 1. The retry and the
  "Failed to find HOM" warning never run. The comparison also looks inverted.
- `FIBER.m:434-435` (M): `modesolrelative` drops the heat load. A chained call does
  not fix it alone, because `heatrip` and `bendrip` each reset `INDbq`.
- `FIBER.m:294` (M): dn/dT is `12e-7`. `betaT.m` documents `12e-6`.
- `FIBER.m:203-238` (M): `'schedule'` and `'adaptive'` meshes are one-sided.
  `'schedule'` scales by `rcore` twice.
- `FIBER.m:1216-1224` (S): `set.conf` sets `stale = true`, then overwrites it.
- `FIBER.m:1450,1463` (S): `setupStepindexFiber` calls `fib.getmesh`, which does
  not exist. This is the entry point for a step-index benchmark.
- `FIBER.m:1423` (S): the profile radius is normalized by core diameter, but
  `meshrip` rescales by radius.
- `FIBERMODE.m:339-340` (M): far-field draw reads `far.thx` and `far.thy`, which
  are never created.
- `util/modeshape.m:44,48,56-61` (M): fallbacks assign an intensity to a position,
  and report the full window as the width without a warning.
- `FIBERMODE.m:182,220,249,265,320` (M): `mustBeMember(x, ['real','imag',...])`
  joins the words into one char vector. It validates characters, not words.

Other findings (S unless marked):

- Errors swallowed at `FIBER.m:100-105, 505-509, 656-658, 1211-1214`.
- `eval` and `assignin` in `util/ini2struct.m`; `assignin` at `FIBER.m:360, 1361`.
- Static `FIBER.svmodes` has the same name as the path function (M).
- `xlsread` and `xlswrite` are deprecated. `RP.m` and `FiberDirectoryMap.ini` have
  hardcoded paths.
- `util/mesh2dRIP.m` is dead and uses undeclared options (M).
- `scripts/Fib_2_10_compare.m` uses an old API.

Facts that affect trust in the MATLAB numbers:

- The west side has no absorbing layer: stretch layers are `[10 10 20 0]` (M).
- The core edge is not on a grid node. Four-vertex averaging smears a step (M).
- Ellipticity changes the index, but not `RADc`, which the confinement mask uses (M).
- The confinement filter has no test that `neff` exceeds the cladding index.
  Window modes can pass (S, inferred).
- The sort criterion depends on the loss of the first mode from `eigs` (M).
- MFD is the 1/e² full width of a 1D slice through the peak. It is not
  Petermann II or 4-sigma. Compare like for like with `Field.Aeff` (M).
- The loss formula `4π/λ · Im(neff) · 10/ln(10)` is correct (M).

## 5. Relevance to future plans

- For a step-index fiber, `fibermodes` LP `neff` is a reference for the `svmodes`
  `'scalar'` field option. The difference shows the grid error.
- The grid method covers what `fibermodes` cannot do: measured profiles, bends,
  heat, and loss.
- Possible work, none started:
  1. A step-index benchmark between the two tools. It needs MATLAB and a repair of
     `setupStepindexFiber`.
  2. Repair of the MATLAB defects in section 4.
  3. A finite-difference solver in Python beside the analytic solvers.
