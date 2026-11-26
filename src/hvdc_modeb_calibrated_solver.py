import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import solve_banded

# Calibrated 1D Cylindrical Electro-Thermal & Bipolar Charge Solver
# Status: Simulated POC; Mode B Material To Be Developed / Not Yet POC'd
# Author: Abhishek Singh | ORCID: 0009-0004-6913-096X | Co-Author: Google Gemini

e_charge = 1.602176634e-19
k_B_eV = 8.617333262e-5
eps_0 = 8.854187817e-12

r_i = 0.025
r_o = 0.052
V_dc = 525.0e3
W_c = 120.0
T_o = 318.15
Nr = 160
r = np.linspace(r_i, r_o, Nr)
dr = r[1] - r[0]


def solve_cylindrical_poisson(r_grid, rho, eps_r, V_inner, V_outer=0.0):
    N = len(r_grid)
    dr_loc = r_grid[1] - r_grid[0]
    eps = eps_0 * eps_r
    ab = np.zeros((3, N))
    rhs = np.zeros(N)
    ab[1, 0] = 1.0
    rhs[0] = V_inner
    ab[1, -1] = 1.0
    rhs[-1] = V_outer
    r_mid_plus = 0.5 * (r_grid[1:-1] + r_grid[2:])
    r_mid_minus = 0.5 * (r_grid[1:-1] + r_grid[:-2])
    c_plus = r_mid_plus / (r_grid[1:-1] * dr_loc**2)
    c_minus = r_mid_minus / (r_grid[1:-1] * dr_loc**2)
    ab[0, 2:] = c_plus
    ab[1, 1:-1] = -(c_plus + c_minus)
    ab[2, :-2] = c_minus
    rhs[1:-1] = -rho[1:-1] / eps
    V = solve_banded((1, 1), ab, rhs)
    E = -np.gradient(V, dr_loc)
    return V, E


def run_calibrated_hvdc(material="XLPE"):
    if material == "XLPE":
        eps_r, kappa = 2.30, 0.28
        T = T_o + (W_c / (2.0 * np.pi * kappa)) * np.log(r_o / r)
        Ea = np.full_like(r, 0.90)
        mu0 = 1.2e-4
        Et_e, Et_h = 0.72, 0.70
        Nt_e = np.full_like(r, 8.0e19)
        Nt_h = np.full_like(r, 8.0e19)
        phi_inj = 1.30
        Cn, Cp = 3.5e-18, 3.5e-18
        beta_pf = np.sqrt(e_charge / (np.pi * eps_0 * eps_r))
    else:
        eps_r, kappa = 2.65, 1.15
        T = T_o + (W_c / (2.0 * np.pi * kappa)) * np.log(r_o / r)
        Ea_o = 1.150
        Ea = Ea_o * (T / T_o)
        mu0 = 4.2e-5
        Et_e, Et_h = 1.95, 1.80
        Nt_e = 2.8e23 * (Ea / Ea_o)**16.0
        Nt_h = 1.9e23 * (Ea / Ea_o)**16.0
        phi_inj = 1.65
        Cn, Cp = 1.8e-16, 1.8e-16
        beta_pf = 0.25 * np.sqrt(e_charge / (np.pi * eps_0 * eps_r))

    nu0 = 6.0e12
    detrap_e = nu0 * np.exp(-Et_e / (k_B_eV * T))
    detrap_h = nu0 * np.exp(-Et_h / (k_B_eV * T))
    n_free = np.full_like(r, 5.0e12)
    p_free = np.full_like(r, 5.0e12)
    n_trap = np.zeros_like(r)
    p_trap = np.zeros_like(r)
    A_rich = 1.2017e6
    beta_sch = np.sqrt(e_charge**3 / (4.0 * np.pi * eps_0 * eps_r))
    R_rec = 2.5e-18
    dt_macro, t_steady, t_vpr = 2.0, 18000.0, 120.0
    steps_steady, steps_vpr = int(t_steady / dt_macro), int(t_vpr / dt_macro)
    E_pre_vpr = rho_pre_vpr = None
    E_post_envelope = np.zeros_like(r)
    r_faces = np.concatenate(([r_i], 0.5 * (r[:-1] + r[1:]), [r_o]))

    for step in range(steps_steady + steps_vpr):
        V_app = V_dc if step < steps_steady else V_dc * (1.0 - 2.0 * ((step - steps_steady + 1) / steps_vpr))
        rho = e_charge * (p_free + p_trap - n_free - n_trap)
        _, E = solve_cylindrical_poisson(r, rho, eps_r, V_app, 0.0)
        pf_arg = np.clip(beta_pf * np.sqrt(np.abs(E)) / (k_B_eV * T), 0.0, 12.0)
        mu_e = mu0 * np.exp(-Ea / (k_B_eV * T) + pf_arg)
        mu_h = 0.65 * mu_e
        n_sub = int(np.clip(np.ceil(dt_macro / (0.4 * dr / max(np.max(mu_e * np.abs(E)), 1e-12))), 1, 50))
        dt = dt_macro / n_sub
        for _ in range(n_sub):
            rho = e_charge * (p_free + p_trap - n_free - n_trap)
            _, E = solve_cylindrical_poisson(r, rho, eps_r, V_app, 0.0)
            if step >= steps_steady:
                E_post_envelope = np.maximum(E_post_envelope, np.abs(E))
            pf_arg = np.clip(beta_pf * np.sqrt(np.abs(E)) / (k_B_eV * T), 0.0, 12.0)
            mu_e = mu0 * np.exp(-Ea / (k_B_eV * T) + pf_arg)
            mu_h = 0.65 * mu_e
            E_in, E_out = E[0], E[-1]
            barr_in = max(0.55, phi_inj - beta_sch * np.sqrt(abs(E_in)) / e_charge)
            barr_out = max(0.55, phi_inj - beta_sch * np.sqrt(abs(E_out)) / e_charge)
            J_p_in = (A_rich * T[0]**2 / e_charge) * np.exp(-barr_in / (k_B_eV * T[0])) if E_in >= 0 else 0.0
            J_n_in = (A_rich * T[0]**2 / e_charge) * np.exp(-barr_in / (k_B_eV * T[0])) if E_in < 0 else 0.0
            J_n_out = (A_rich * T[-1]**2 / e_charge) * np.exp(-barr_out / (k_B_eV * T[-1])) if E_out >= 0 else 0.0
            J_p_out = (A_rich * T[-1]**2 / e_charge) * np.exp(-barr_out / (k_B_eV * T[-1])) if E_out < 0 else 0.0
            F_p = np.zeros(Nr + 1)
            F_n = np.zeros(Nr + 1)
            F_p[0], F_p[-1] = J_p_in, -J_p_out
            F_n[0], F_n[-1] = -J_n_in, J_n_out
            E_face = 0.5 * (E[:-1] + E[1:])
            mu_p_face = 0.5 * (mu_h[:-1] + mu_h[1:])
            mu_n_face = 0.5 * (mu_e[:-1] + mu_e[1:])
            p_up = np.where(E_face >= 0, p_free[:-1], p_free[1:])
            n_up = np.where(E_face >= 0, n_free[1:], n_free[:-1])
            F_p[1:-1] = mu_p_face * E_face * p_up
            F_n[1:-1] = -mu_n_face * E_face * n_up
            div_Fp = (r_faces[1:] * F_p[1:] - r_faces[:-1] * F_p[:-1]) / (r * dr)
            div_Fn = (r_faces[1:] * F_n[1:] - r_faces[:-1] * F_n[:-1]) / (r * dr)
            trap_rate_e = Cn * n_free * np.maximum(0.0, 1.0 - n_trap / Nt_e) - detrap_e * n_trap
            trap_rate_h = Cp * p_free * np.maximum(0.0, 1.0 - p_trap / Nt_h) - detrap_h * p_trap
            recomb = R_rec * (n_free * p_free + n_free * p_trap + p_free * n_trap)
            n_free = np.clip(n_free + dt * (-div_Fn - trap_rate_e - recomb), 1.0e6, 1.0e21)
            p_free = np.clip(p_free + dt * (-div_Fp - trap_rate_h - recomb), 1.0e6, 1.0e21)
            n_trap = np.clip(n_trap + dt * (trap_rate_e - R_rec * p_free * n_trap), 0.0, Nt_e)
            p_trap = np.clip(p_trap + dt * (trap_rate_h - R_rec * n_free * p_trap), 0.0, Nt_h)
        if step == steps_steady - 1:
            E_pre_vpr, rho_pre_vpr = E.copy(), rho.copy()
    rho_post_vpr = e_charge * (p_free + p_trap - n_free - n_trap)
    return {
        "r_mm": r * 1e3, "T_C": T - 273.15, "dT": T[0] - T[-1],
        "rho_pre": rho_pre_vpr, "E_pre_kvmm": E_pre_vpr / 1e6,
        "E_post_env_kvmm": E_post_envelope / 1e6,
        "E_pre_i": E_pre_vpr[0] / 1e6, "E_pre_o": E_pre_vpr[-1] / 1e6,
        "E_post_max": np.max(E_post_envelope) / 1e6,
        "rho_max": np.max(np.abs(rho_post_vpr)),
    }


res_xlpe = run_calibrated_hvdc("XLPE")
res_modeb = run_calibrated_hvdc("MODE_B")
E_lap_kvmm = (V_dc / (r * np.log(r_o / r_i))) / 1e6
print(f"XLPE   | dT={res_xlpe['dT']:.2f} K | Pre={res_xlpe['E_pre_i']:.2f}/{res_xlpe['E_pre_o']:.2f} kV/mm | PostMax={res_xlpe['E_post_max']:.2f} kV/mm | rho_max={res_xlpe['rho_max']:.2e}")
print(f"Mode B | dT={res_modeb['dT']:.2f} K | Pre={res_modeb['E_pre_i']:.2f}/{res_modeb['E_pre_o']:.2f} kV/mm | PostMax={res_modeb['E_post_max']:.2f} kV/mm | rho_max={res_modeb['rho_max']:.2e}")

fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.5), dpi=300)
axes[0, 0].plot(res_xlpe["r_mm"], res_xlpe["T_C"], color="#d95f02", lw=2.2, label="XLPE")
axes[0, 0].plot(res_modeb["r_mm"], res_modeb["T_C"], color="#1b9e77", lw=2.2, label="Mode B")
axes[0, 0].set_title("Radial Temperature Profile")
axes[0, 0].legend()
axes[0, 1].plot(res_xlpe["r_mm"], res_xlpe["rho_pre"], color="#d95f02", lw=2.2)
axes[0, 1].set_title("Pre-VPR Net Space Charge")
axes[1, 0].plot(res_xlpe["r_mm"], E_lap_kvmm, color="#2b5c8f", ls="-.", label="Laplacian")
axes[1, 0].plot(res_xlpe["r_mm"], res_xlpe["E_pre_kvmm"], color="#d95f02", lw=2.2, label="XLPE")
axes[1, 0].plot(res_modeb["r_mm"], res_modeb["E_pre_kvmm"], color="#1b9e77", lw=2.2, label="Mode B")
axes[1, 0].set_title("Pre-VPR Electric Field")
axes[1, 0].legend()
axes[1, 1].plot(res_xlpe["r_mm"], E_lap_kvmm, color="#2b5c8f", ls="-.", label="Laplacian")
axes[1, 1].plot(res_xlpe["r_mm"], res_xlpe["E_post_env_kvmm"], color="#d95f02", lw=2.2, label="XLPE Peak")
axes[1, 1].plot(res_modeb["r_mm"], res_modeb["E_post_env_kvmm"], color="#1b9e77", lw=2.2, label="Mode B Peak")
axes[1, 1].set_title("Post-VPR Peak Electric Field")
axes[1, 1].legend()
plt.tight_layout()
plt.savefig("hvdc_modeb_radial_profiles.png", dpi=300)
plt.show()
