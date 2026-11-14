"""Load the three data.gov.my files and merge them into one state-year dataset."""
import pandas as pd

YEARS = list(range(2019, 2024))          # 2019 - 2023
INCOME_YEARS = [2019, 2020, 2022]        # years that exist in hh_income_state.csv


def _add_year(df):
    df = df.copy()
    df["year"] = pd.to_datetime(df["date"]).dt.year
    return df


def load_raw(folder="."):
    schools = _add_year(pd.read_csv(f"{folder}/schools_district.csv"))
    income = _add_year(pd.read_csv(f"{folder}/hh_income_state.csv"))
    marriages = _add_year(pd.read_csv(f"{folder}/marriages_state.csv"))
    schools = schools[schools["year"].isin(YEARS)]
    income = income[income["year"].isin(YEARS)]
    marriages = marriages[marriages["year"].isin(YEARS)]
    return schools, income, marriages


def build_merged(schools, income, marriages):
    """Merge the three datasets on state + year (16 states x 5 years)."""
    # Schools: use the 'All Districts' rows as state totals (avoids double counting)
    st = schools[(schools["district"] == "All Districts") & (schools["state"] != "Malaysia")]
    sp = (st.pivot_table(index=["state", "year"], columns="stage", values="schools", aggfunc="sum")
            .add_prefix("schools_").reset_index())
    sp["schools_total"] = sp[["schools_primary", "schools_secondary", "schools_tertiary"]].sum(axis=1)

    # Marriages: male and female side by side
    mp = marriages.pivot_table(index=["state", "year"], columns="sex", values=["abs", "rate"]).reset_index()
    mp.columns = ["state", "year"] + [f"marriage_{a}_{b}" for a, b in mp.columns[2:]]
    mp["marriage_abs_avg"] = (mp["marriage_abs_female"] + mp["marriage_abs_male"]) / 2

    # Income: only 2019, 2020, 2022 exist (left join keeps other years empty)
    hi = income[["state", "year", "income_mean", "income_median"]]

    merged = sp.merge(mp, on=["state", "year"], how="outer").merge(hi, on=["state", "year"], how="left")
    merged["income_gap"] = merged["income_mean"] - merged["income_median"]
    return merged.sort_values(["state", "year"]).reset_index(drop=True)


def school_districts(schools):
    """District-level rows only (no 'All Districts' totals, no national row)."""
    d = schools[(schools["district"] != "All Districts") & (schools["state"] != "Malaysia")]
    return d.copy()


def school_state_type(schools):
    """State totals by school type (from the 'All Districts' rows)."""
    return schools[(schools["district"] == "All Districts") & (schools["state"] != "Malaysia")].copy()


def canon(name):
    """Normalise a state name so data and GeoJSON names can be matched."""
    n = str(name).lower().strip()
    for junk in ["w.p. ", "wilayah persekutuan ", "federal territory of "]:
        n = n.replace(junk, "")
    aliases = {"penang": "pulau pinang", "malacca": "melaka", "trengganu": "terengganu",
               "negri sembilan": "negeri sembilan"}
    return aliases.get(n, n)
