/*window.tests = [
    {
        "cases": [
            "transport"
        ],
        "name": "01_square_regular_grid"
    },
    {
        "cases": [
            "flow_fv_sorption",
//            "flow_LMH_dg_heat",
//            "flow_LMH_richards",
            "flow_dg_sorption",
//            "flow_unsteady_dg",
            "flow_fv",
            "flow_bddc",
            "flow_bddc_fieldformula"
        ],
        "name": "02_cube_123d"
    },
    {
        "cases": [
            "mesh_read"
        ],
        "name": "03_mesh_read"
    },
//    {
//        "cases": [
//            "flow"
//        ],
//        "name": "04_kravi_hora"
//    },
    {
        "cases": [
            "transport"
        ],
        "name": "05_dfn_2d"
    }
];
/*window.tests = [
    {
        "cases": [
            "04_source_LMH",
            "06_unsteady_MH_exact",
            "02_unsteady",
            "03_unsteady_LMH",
            "01_source",
            "08_gravity",
            "07_unsteady_init_piezo",
            "05_unsteady_LMH_exact"
        ],
        "name": "10_darcy"
    },
    {
        "cases": [
            "03_robin",
            "04_total_flux",
            "02_neumann",
            "05_seepage",
            "10_dirichlet_LMH",
            "06_river_square",
            "07_river_slope",
            "09_seepage_stagnation",
            "01_dirichlet"
        ],
        "name": "11_darcy_bc"
    },
    {
        "cases": [
            "11_exact_2d_nc_p0",
            "30_surf_cube_cc",
            "31_surf_cube_23d_p0",
            "02_vtk",
            "03_piezo",
            "05_square",
            "04_bddc",
            "01_gmsh",
            "10_exact_2d_cc",
            "06_cube"
        ],
        "name": "12_darcy_frac"
    },
    {
        "cases": [
            "01_square",
            "02_unsteady_MH_time_dep"
        ],
        "name": "13_darcy_time"
    },
    {
        "cases": [
            "04_2d_horizontal",
            "02_1d_dirichlet",
            "01_1d",
            "03_1d_horizontal"
        ],
        "name": "14_darcy_richards"
    },
    {
        "cases": [
            "02_sources",
            "03_bc",
            "01_sources_small"
        ],
        "name": "20_solute_fv"
    },
    {
        "cases": [
            "01_fv_dp_sorp_gmsh",
            "04_y_branch",
            "03_fv_dp_sorp_small",
            "02_fv_dp_sorp_vtk"
        ],
        "name": "21_solute_fv_frac"
    },
    {
        "cases": [
            "01_fv_dp_sorp_small",
            "03_bc_short_pulse",
            "02_bc",
            "04_unsteady_flow"
        ],
        "name": "22_solute_fv_time"
    },
    {
        "cases": [
            "02_aniso_diff",
            "01_sources"
        ],
        "name": "24_solute_dg"
    },
    {
        "cases": [
            "03_total_flux",
            "04_diff_flux",
            "01_inflow",
            "02_dirichlet"
        ],
        "name": "25_solute_dg_bc"
    },
    {
        "cases": [
            "01_vtk",
            "05_diffusion_fracture",
            "04_y_branch",
            "03_dg_dp_sorp_small",
            "02_dg_dp"
        ],
        "name": "26_solute_dg_frac"
    },
    {
        "cases": [
            "01_frac_gmsh",
            "04_bc_short_pulse",
            "03_bc",
            "02_dg_dp_sorp_small",
            "05_unsteady_flow",
            "06_sources"
        ],
        "name": "27_solute_dg_time"
    },
    {
        "cases": [
            "02_source",
            "04_langmuir",
            "10_linear_dg",
            "06_linear",
            "07_langmuir_var",
            "09_linear_var",
            "05_freundlich",
            "03_flow_trans_sorp",
            "01_simple",
            "08_freundlich_var"
        ],
        "name": "30_sorption"
    },
    {
        "cases": [
            "03_reaction",
            "02_time",
            "06_cfl",
            "05_sorp_reaction",
            "04_sorp",
            "01"
        ],
        "name": "31_dual_por"
    },
    {
        "cases": [
            "02_3el_cfl",
            "01_3el",
            "04_3el_chain",
            "03_3el_molar_mass"
        ],
        "name": "32_decay"
    },
    {
        "cases": [
            "02_3el_6subst",
            "03_3el_cfl",
            "01_3el_long"
        ],
        "name": "33_reaction"
    },
    {
        "cases": [
            "02_fast_frac_flow_slow_diff",
            "01_frac"
        ],
        "name": "34_sorption_dg"
    },
    {
        "cases": [
            "03_dif_por",
            "04_dif_por_2d",
            "02_flow_transport_heat",
            "01_flow_heat"
        ],
        "name": "40_heat"
    },
    {
        "cases": [
            "01_cmd_line"
        ],
        "name": "flow123d"
    }
];*/ 


interface Test {
    cases: string[],
    name: string;
}


interface Window {
  tests: Test[];
}

window.tests = [
  {
      "cases": [
          "cache"
      ],
      "name": "memory"
  }
];