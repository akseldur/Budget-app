from app.budget.forecast import forecast


def test_gronn_under_80_prosent_av_prognose():
    # 15 dager inne i en 30-dagers måned, brukt 300 av 1000 -> prognose 600 (60 %)
    result = forecast(spent_so_far=300, planned_amount=1000, days_elapsed=15, days_in_month=30)
    assert result.projected == 600
    assert result.status == "green"


def test_gul_mellom_80_og_100_prosent():
    # Prognose 900 av 1000 = 90 %
    result = forecast(spent_so_far=450, planned_amount=1000, days_elapsed=15, days_in_month=30)
    assert result.projected == 900
    assert result.status == "yellow"


def test_rod_over_budsjett():
    # Prognose 1200 av 1000 = 120 %
    result = forecast(spent_so_far=600, planned_amount=1000, days_elapsed=15, days_in_month=30)
    assert result.projected == 1200
    assert result.status == "red"


def test_grensetilfelle_nokkaktig_80_prosent_er_gul():
    result = forecast(spent_so_far=800, planned_amount=1000, days_elapsed=30, days_in_month=30)
    assert result.projected == 800
    assert result.status == "yellow"


def test_start_av_maneden_ingen_dager_gatt_ennaa():
    # Dag 0: ingen prognosegrunnlag, skal ikke variere med planned_amount
    result = forecast(spent_so_far=0, planned_amount=1000, days_elapsed=0, days_in_month=30)
    assert result.status == "green"


def test_kategori_uten_budsjett_men_med_forbruk_er_rod():
    result = forecast(spent_so_far=50, planned_amount=0, days_elapsed=10, days_in_month=30)
    assert result.status == "red"


def test_kategori_uten_budsjett_og_uten_forbruk_er_gronn():
    result = forecast(spent_so_far=0, planned_amount=0, days_elapsed=10, days_in_month=30)
    assert result.status == "green"
