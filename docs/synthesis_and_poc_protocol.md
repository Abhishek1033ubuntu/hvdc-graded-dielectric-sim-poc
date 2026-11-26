# Stage 1 & Stage 3 Technical Specification (To Be Developed / Not Yet POC'd)

**Primary Author:** Abhishek Singh (ORCID: https://orcid.org/0009-0004-6913-096X)  
**Co-Author / AI Research Collaborator:** Google Gemini  
**Status:** To Be Developed / Not Yet POC'd  

## 1. Monomer Repeat Unit & Electronic Trap Energetics (Stage 1)
- **Repeat Unit:** `[-C6F6O2 - ArF - Imide(6FDA-TFMB) - Si(CH3)2O - Si(CF3CH2CH2)(CH3)O - ArF-]_n`
- **Bandgap (E_g):** 7.45 eV (matrix) / ~6.0 eV (11B15N filler)
- **Deep Electron Trap Depth (E_te):** 1.95 eV below conduction band minimum (`N_te` graded from `2.8e23 m^-3` at `r_o` to `5.4e23 m^-3` at `r_i`)
- **Deep Hole Trap Depth (E_th):** 1.80 eV above valence band maximum (`N_th` graded from `1.9e23 m^-3` at `r_o` to `3.66e23 m^-3` at `r_i`)
- **Mean Inter-Trap Spacing:** 1.31 nm (suppresses trap-to-trap tunneling percolation)

## 2. Field-Guided Synthesis & Extrusion Protocol (Stage 3 - To Be Developed)
1. **Isotopic 11B15N Functionalization:** Exfoliate >99% isotopically pure 11B15N in anhydrous NMP and graft edges with 3-(triethoxysilyl)propyl-perfluorooctanamide.
2. **Telechelic Oligomer Synthesis:** Polycondense 6FDA, TFMB, and trifluoropropyl-methyl oligosiloxane, chemically imidize to remove H2O, and end-cap with 4-(trifluorovinyloxy)benzoyl chloride.
3. **Co-Extrusion & Radial Dielectrophoretic Poling:** Co-extrude at 130 C; hold at 145 C pre-gelation under a 45 kV radial DC field and 40 kHz ultrasonic standing wave to establish the 1.93x radial polar-group concentration gradient and align 11B15N basal planes radially.
4. **Thermal [2+2] Cyclodimerization Lock-In:** Cure at 195 C for 45 min under pressurized nitrogen while keeping the DC poling field active, locking the radial activation energy gradient permanently with zero volatile byproducts.
